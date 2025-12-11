from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from typing import Optional, List, Dict, Any
import os

# Embedding model — same as you used
EMBED_MODEL = "gemini-embedding-001"
PERSIST_DIR = "tamarin_vectordb"
COLLECTION_NAME = "tamarin_manual"


def load_vector_store() -> Chroma:
    """Load the vector store with embeddings."""
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings
    )
    return vectorstore

def query_vectordb(
    query: str,
    k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """
    Query the vector DB for the top-k most similar chunks to `query`.
    Optionally filter by metadata.
    """
    vectorstore = load_vector_store()
    docs = vectorstore.similarity_search(query, k=k, filter=filter_dict)
    return docs

def print_results(docs: List[Document], show_full_content: bool = True):
    """Pretty print search results."""
    if not docs:
        print("   ❌ No results found!")
        return
    
    print(f"   Found {len(docs)} results:\n")
    for i, doc in enumerate(docs, 1):
        print(f"   {'='*70}")
        print(f"   Result #{i}")
        print(f"   {'='*70}")
        print(f"   📍 Section: {doc.metadata.get('section_title', 'Unknown')}")
        print(f"   📂 Path: {doc.metadata.get('section_path', 'Unknown')}")
        print(f"   📄 Lines: {doc.metadata.get('start_line', '?')}-{doc.metadata.get('end_line', '?')}")
        print(f"   📏 Length: {doc.metadata.get('char_count', 0)} chars")
        
        if 'chunk_index' in doc.metadata:
            print(f"   📦 Chunk: {doc.metadata['chunk_index'] + 1}/{doc.metadata['total_chunks']}")
        
        print(f"\n   📝 Content Preview:")
        content = doc.page_content
        if show_full_content:
            print(f"   {content}")
        else:
            # Show first 300 characters
            preview = content[:300] + "..." if len(content) > 300 else content
            print(f"   {preview}")
        print()

def inspect_database():
    """Show database statistics."""
    print("\n" + "="*70)
    print("🔍 DATABASE INSPECTION")
    print("="*70)
    
    vectorstore = load_vector_store()
    data = vectorstore.get()
    
    total_docs = len(data.get("documents", []))
    print(f"\n📊 Total documents: {total_docs}")
    
    if total_docs > 0:
        # Analyze metadata
        metadatas = data.get("metadatas", [])
        
        # Count unique sections
        sections = set()
        chunked_docs = 0
        levels = {}
        
        for meta in metadatas:
            if meta:
                sections.add(meta.get('section_title', 'Unknown'))
                if 'chunk_index' in meta:
                    chunked_docs += 1
                level = meta.get('section_level', 0)
                levels[level] = levels.get(level, 0) + 1
        
        print(f"📚 Unique sections: {len(sections)}")
        print(f"📦 Chunked documents: {chunked_docs}")
        print(f"📊 Documents by level:")
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} docs")
        
        # Show sample sections
        print(f"\n📋 Sample sections:")
        sample_sections = list(sections)[:10]
        for sec in sample_sections:
            print(f"   - {sec}")
        if len(sections) > 10:
            print(f"   ... and {len(sections) - 10} more")

if __name__ == "__main__":
    # First, inspect the database
    inspect_database()
    
    # Test queries
    test_queries = [
        ("How to install Tamarin on Windows?", 5),
        ("What are rules in Tamarin?", 5),
        ("Explain lemmas and properties", 5),
        ("How to model protocols?", 5),
        ("What is the Dolev-Yao adversary model?", 5),
    ]
    
    print("\n" + "="*70)
    print("🔍 TESTING QUERIES")
    print("="*70)
    
    for query, k in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: '{query}' (top {k} results)")
        print(f"{'='*70}\n")
        
        docs = query_vectordb(query, k=k)
        print_results(docs, show_full_content=True)
    
    # Interactive mode
    print("\n" + "="*70)
    print("💬 INTERACTIVE MODE")
    print("="*70)
    print("Enter your questions (or 'quit' to exit):\n")
    
    while True:
        try:
            query = input("❓ Your question: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            docs = query_vectordb(query, k=3)
            print_results(docs, show_full_content=True)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
