import os
import gc
import time
import json
import hashlib
import re
from datetime import datetime
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

if not os.environ.get("GOOGLE_API_KEY"): 
    os.environ["GOOGLE_API_KEY"] = "AIzaSyABvDYLDLd880La-U1phLJ20JpyjIuz0vQ"

MODEL_NAME = "gemini-embedding-001"
PERSIST_DIR = "tamarin_vectordb"
COLLECTION_NAME = "tamarin_manual"
LOG_FILE = "ingestion_log.json"
MAX_SECTION_SIZE = 1000  # Reduced for better granularity
CHUNK_OVERLAP = 150  # Overlap between chunks for context

def extract_sections_from_markdown(md_path):
    """
    Extract sections from markdown file based on headers.
    Handles complex header formats including bold markdown within headers.
    Returns a list of section dictionaries with full path, content, level, and line numbers.
    """
    print(f"📖 Opening Markdown file: {md_path}")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    sections = []
    stack = [{"name": "Document Root", "level": 0}]
    current_content = []
    current_start_line = 1
    
    # Regex pattern to match headers: # through #### with optional bold markers
    # Matches: # Title, ## Title, ### **Title**, #### Title, etc.
    header_pattern = re.compile(r'^(#{1,4})\s+\*\*?(.+?)\*\*?\s*$|^(#{1,4})\s+(.+?)\s*$')
    
    for line_num, line in enumerate(lines, start=1):
        # Check if line is a header
        match = header_pattern.match(line.rstrip())
        
        if match:
            # Extract level and title
            if match.group(1):  # Format with bold
                hashes = match.group(1)
                title = match.group(2).strip()
            else:  # Format without bold
                hashes = match.group(3)
                title = match.group(4).strip()
            
            level = len(hashes)
            
            # Skip empty titles
            if not title:
                current_content.append(line)
                continue
            
            # Save previous section if it has content
            if current_content:
                content_text = ''.join(current_content).strip()
                if content_text:
                    section_path = ' > '.join([s['name'] for s in stack[1:]])  # Skip root
                    if not section_path:
                        section_path = stack[-1]['name']
                    sections.append({
                        "path": section_path,
                        "title": stack[-1]['name'],
                        "content": content_text,
                        "level": stack[-1]['level'],
                        "start_line": current_start_line,
                        "end_line": line_num - 1
                    })
            
            # Update stack based on level
            while len(stack) > 1 and stack[-1]['level'] >= level:
                stack.pop()
            
            # Push new section to stack
            stack.append({"name": title, "level": level})
            
            # Reset content collection for new section
            current_content = []
            current_start_line = line_num + 1
        else:
            # Not a header - add line to current content
            current_content.append(line)
    
    # Add the last section if it has content
    if current_content:
        content_text = ''.join(current_content).strip()
        if content_text:
            section_path = ' > '.join([s['name'] for s in stack[1:]])
            if not section_path:
                section_path = stack[-1]['name']
            sections.append({
                "path": section_path,
                "title": stack[-1]['name'],
                "content": content_text,
                "level": stack[-1]['level'],
                "start_line": current_start_line,
                "end_line": len(lines)
            })
    
    print(f"📑 Found {len(sections)} sections with content")
    
    # Show statistics
    total_chars = sum(len(sec['content']) for sec in sections)
    avg_size = total_chars // len(sections) if sections else 0
    print(f"📊 Total characters: {total_chars:,}, Average section size: {avg_size:,} chars")
    
    # Show sample sections
    for i, sec in enumerate(sections[:5]):
        print(f"   Section {i+1}: '{sec['path']}'")
        print(f"      Lines {sec['start_line']}-{sec['end_line']}, {len(sec['content'])} chars, Level {sec['level']}")
    if len(sections) > 5:
        print(f"   ... and {len(sections) - 5} more sections")
    
    return sections

def split_large_section(section, max_size=MAX_SECTION_SIZE):
    """
    Split a section if it's too large, using text splitter.
    Returns a list of subsections with better chunking.
    """
    content = section["content"]
    
    # Skip empty content
    if not content or not content.strip():
        return []
    
    if len(content) <= max_size:
        return [section]
    
    print(f"   ✂️  Splitting large section '{section['title']}' ({len(content)} chars)")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_size,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
    )
    
    chunks = text_splitter.split_text(content)
    subsections = []
    
    for i, chunk in enumerate(chunks):
        # Skip empty chunks
        if not chunk or not chunk.strip():
            continue
            
        subsection = section.copy()
        subsection["content"] = chunk.strip()
        subsection["chunk_index"] = i
        subsection["total_chunks"] = len(chunks)
        subsection["chunk_id"] = f"{section['title']}_chunk_{i}"
        subsections.append(subsection)
    
    print(f"      Created {len(subsections)} chunks")
    return subsections

def create_section_id(section):
    """
    Create a unique ID for a section based on its full path and position.
    """
    id_string = f"{section['path']}_{section['start_line']}"
    if 'chunk_index' in section:
        id_string += f"_chunk{section['chunk_index']}"
    return hashlib.md5(id_string.encode()).hexdigest()

def load_ingestion_log(log_file=LOG_FILE):
    """
    Load the ingestion log to track which sections have been processed.
    """
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "processed_sections": [],
        "last_updated": None,
        "total_documents": 0
    }

def save_ingestion_log(log_data, log_file=LOG_FILE):
    """
    Save the ingestion log.
    """
    log_data["last_updated"] = datetime.now().isoformat()
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def create_documents_from_sections(sections, md_path):
    """
    Create LangChain documents from sections with improved metadata.
    """
    print(f"📝 Creating documents from {len(sections)} sections...")
    
    documents = []
    processed_sections = []
    
    for section in sections:
        # Split large sections if necessary
        subsections = split_large_section(section)
        
        for subsec in subsections:
            # Skip if content is empty after stripping
            if not subsec["content"] or not subsec["content"].strip():
                print(f"   ⚠️  Skipping empty section: '{subsec['path']}'")
                continue
                
            section_id = create_section_id(subsec)
            
            # Create comprehensive metadata
            metadata = {
                "source": os.path.basename(md_path),
                "section_path": subsec["path"],
                "section_title": subsec["title"],
                "section_level": subsec["level"],
                "start_line": subsec["start_line"],
                "end_line": subsec["end_line"],
                "section_id": section_id,
                "char_count": len(subsec["content"]),
                # Add searchable keywords from section title
                "keywords": subsec["title"].lower()
            }
            
            if 'chunk_index' in subsec:
                metadata["chunk_index"] = subsec["chunk_index"]
                metadata["total_chunks"] = subsec["total_chunks"]
                metadata["chunk_id"] = subsec.get("chunk_id", f"chunk_{subsec['chunk_index']}")
            
            # Prepend section context to content for better retrieval
            enhanced_content = f"Section: {subsec['title']}\n\n{subsec['content']}"
            
            # Create document
            doc = Document(
                page_content=enhanced_content,
                metadata=metadata
            )
            documents.append(doc)
            
            # Track processed section for log
            processed_sections.append({
                "section_id": section_id,
                "path": subsec["path"],
                "title": subsec["title"],
                "start_line": subsec["start_line"],
                "end_line": subsec["end_line"],
                "char_count": len(subsec["content"]),
                "is_chunked": 'chunk_index' in subsec
            })
    
    print(f"✅ Created {len(documents)} document chunks from sections")
    
    # Show size distribution
    sizes = [len(doc.page_content) for doc in documents]
    if sizes:
        avg_size = sum(sizes) // len(sizes)
        min_size = min(sizes)
        max_size = max(sizes)
        print(f"📊 Document sizes - Min: {min_size}, Max: {max_size}, Avg: {avg_size}")
    
    return documents, processed_sections

def load_existing_vectorstore(persist_directory=PERSIST_DIR, collection_name=COLLECTION_NAME, embedding=None):
    """
    If a persisted Chroma store exists, load it and return (vectorstore, existing_count).
    Otherwise return (None, 0).
    """
    try:
        vs = Chroma(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_function=embedding
        )
        data = vs.get()
        existing = len(data.get("documents", []))
        print(f"⚙️  Loaded existing vectorstore: {existing} documents already stored")
        return vs, existing
    except Exception as e:
        print("⚠️  Could not load existing vectorstore (will create new):", e)
        return None, 0

def filter_new_documents(documents, log_data):
    """
    Filter out documents that have already been processed based on section_id.
    """
    processed_ids = set([s["section_id"] for s in log_data.get("processed_sections", [])])
    new_docs = []
    skipped = 0
    
    for doc in documents:
        section_id = doc.metadata.get("section_id")
        if section_id not in processed_ids:
            new_docs.append(doc)
        else:
            skipped += 1
    
    if skipped > 0:
        print(f"📋 Skipping {skipped} already processed sections")
    
    return new_docs

def store_in_vectordb(
    documents,
    processed_section_data,
    db_path=PERSIST_DIR,
    collection_name=COLLECTION_NAME,
    batch_size=3,
    delay_seconds=5,
    embedding_model=MODEL_NAME
):
    """
    Store documents in vector database with progress tracking.
    """
    print(f"\n💾 Storing/updating vector DB at: {db_path}")
    embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
    
    # Load ingestion log
    log_data = load_ingestion_log()
    
    # Filter out already processed documents
    to_add = filter_new_documents(documents, log_data)
    
    if not to_add:
        print("✅ All sections already embedded — nothing to add.")
        return True
    
    print(f"📥 {len(to_add)} new documents to embed and add...")
    
    # Load or create vectorstore
    vectorstore, existing_count = load_existing_vectorstore(
        persist_directory=db_path,
        collection_name=collection_name,
        embedding=embeddings
    )
    
    # Create a mapping of document to section data for tracking
    doc_to_section = {}
    for doc, sec_data in zip(documents, processed_section_data):
        doc_to_section[doc.metadata["section_id"]] = sec_data
    
    if vectorstore is None:
        # First time - create new vectorstore
        vectorstore = Chroma.from_documents(
            documents=to_add,
            embedding=embeddings,
            persist_directory=db_path,
            collection_name=collection_name
        )
        
        # Update log with detailed section info
        added_sections = [doc_to_section[doc.metadata["section_id"]] for doc in to_add]
        log_data["processed_sections"].extend(added_sections)
        log_data["total_documents"] = len(to_add)
        save_ingestion_log(log_data)
        
        print("✅ Initial ingestion done")
        return True
    else:
        # Add in batches
        total = len(to_add)
        successfully_added = []
        
        for i in range(0, total, batch_size):
            batch = to_add[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            print(f"   📦 Batch {batch_num}/{total_batches} ({len(batch)} docs)...", end=" ")
            
            try:
                vectorstore.add_documents(batch)
                gc.collect()
                
                # Track successfully added sections with full details
                for doc in batch:
                    section_id = doc.metadata.get("section_id")
                    if section_id and section_id in doc_to_section:
                        successfully_added.append(doc_to_section[section_id])
                
                print("✅ batch added")
                
                # Update log after each successful batch
                log_data["processed_sections"].extend(successfully_added)
                log_data["total_documents"] = existing_count + len(log_data["processed_sections"])
                save_ingestion_log(log_data)
                successfully_added = []  # Reset for next batch
                
            except Exception as e:
                print(f"❌ Error adding batch: {e}")
                # Save progress so far
                if successfully_added:
                    log_data["processed_sections"].extend(successfully_added)
                    log_data["total_documents"] = existing_count + len(log_data["processed_sections"])
                    save_ingestion_log(log_data)
                return False
            
            if batch_num < total_batches:
                print(f"      ⏱️ Waiting {delay_seconds}s before next batch...")
                time.sleep(delay_seconds)
        
        print("✅ All new sections added")
        return True

def ingest_markdown_to_vectordb(
    md_path,
    db_path=PERSIST_DIR,
    max_section_size=MAX_SECTION_SIZE,
    batch_size=5,
    delay_seconds=3
):
    """
    Main function to ingest markdown file into vector database.
    Improved with better error handling and progress tracking.
    """
    print("\n" + "="*60)
    print("🚀 Markdown → Vector Database Ingestion")
    print("="*60)
    
    if not os.path.exists(md_path):
        print(f"❌ Error: Markdown file not found at {md_path}")
        return False
    
    # Show file info
    file_size = os.path.getsize(md_path) / 1024 / 1024  # MB
    print(f"📄 File: {os.path.basename(md_path)} ({file_size:.2f} MB)")
    
    # Extract sections from markdown
    sections = extract_sections_from_markdown(md_path)
    
    if not sections:
        print("❌ No sections found in markdown file!")
        return False
    
    # Create documents from sections
    documents, processed_section_data = create_documents_from_sections(sections, md_path)
    
    if not documents:
        print("❌ No documents created from sections!")
        return False
    
    # Store in vector database
    return store_in_vectordb(
        documents,
        processed_section_data,
        db_path=db_path,
        collection_name=COLLECTION_NAME,
        batch_size=batch_size,
        delay_seconds=delay_seconds,
        embedding_model=MODEL_NAME
    )

if __name__ == "__main__":
    md_path = "tamarin-manual.md"
    
    print("\n🔧 Configuration:")
    print(f"   Max section size: {MAX_SECTION_SIZE} chars")
    print(f"   Chunk overlap: {CHUNK_OVERLAP} chars")
    print(f"   Embedding model: {MODEL_NAME}")
    print(f"   Vector DB: {PERSIST_DIR}")
    
    success = ingest_markdown_to_vectordb(
        md_path=md_path,
        max_section_size=MAX_SECTION_SIZE,
        batch_size=5,
        delay_seconds=3
    )
    
    if success:
        print("\n✅ Ingestion completed successfully!")
        log_data = load_ingestion_log()
        print(f"📊 Total sections processed: {len(log_data['processed_sections'])}")
        print(f"📊 Total documents in DB: {log_data['total_documents']}")
        
        # Show some sample sections from log
        if log_data['processed_sections']:
            print("\n📋 Sample processed sections:")
            for sec in log_data['processed_sections'][:10]:
                chunk_info = ""
                if sec.get('is_chunked'):
                    chunk_info = " [CHUNKED]"
                print(f"   - {sec['title']}{chunk_info}")
                print(f"     Path: {sec['path']}")
                print(f"     Lines: {sec['start_line']}-{sec['end_line']}, {sec['char_count']} chars")
    else:
        print("\n❌ Ingestion failed. Check the errors above.")
