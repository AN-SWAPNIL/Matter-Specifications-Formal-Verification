import nest_asyncio
nest_asyncio.apply()

from llama_parse import LlamaParse
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

# Define page ranges for 1175-page doc
chunks = [
    ("500-715", "full_chunk1"),
    # ("250-499", "chunk2"),
    # ("500-749", "chunk3"),
    # ("750-1174", "chunk4"),
    # ("1000-1174", "chunk5"),
]

for page_range, chunk_name in chunks:
    print(f"\n{'='*60}")
    print(f"Processing {chunk_name}: Pages {page_range}")
    print(f"{'='*60}")
    
    parser = LlamaParse(
        api_key=os.getenv('LLAMA_CLOUD_API_KEY'),
        result_type="markdown",
        
        # CORRECT: Use valid parse_mode values
        parse_mode="parse_page_with_agent",  # ✅ For diagrams & images
        
        verbose=True,
        num_workers=4,
        language="en",
        target_pages=page_range,
        page_separator="\n\n---PAGE_BREAK---\n\n",
        invalidate_cache=True,
    )
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting {chunk_name}...")
        print(f"Mode: parse_page_with_agent (extracts images & diagrams)")
        
        documents = parser.load_data("../files/Matter-1.4-Application-Cluster-Specification.pdf")
        
        if len(documents) == 0:
            print(f"⚠ Warning: {chunk_name} returned 0 documents!")
            continue
        
        output_file = f"matter_spec_{chunk_name}.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Matter Specification - {chunk_name.upper()}\n")
            f.write(f"## Pages {page_range}\n\n")
            
            for doc in documents:
                f.write(doc.text)
                f.write("\n\n")
        
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        
        # Check for images/diagrams in output
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            images = content.count("![")
            diagrams = content.count("```mermaid")
        
        print(f"✓ {chunk_name} complete: {file_size:.2f} MB")
        print(f"  ├─ Images found: {images}")
        print(f"  └─ Diagrams (Mermaid): {diagrams}")
        
    except Exception as e:
        print(f"✗ Error on {chunk_name}: {str(e)}")
        continue

print("\n" + "="*60)
print("✓ All chunks processed!")
print("="*60)
print("\nMerge all files with:")
print("Get-Content matter_spec_*.md | Set-Content matter_spec_complete.md")
