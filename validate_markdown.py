"""
Quick validation script to test markdown parsing without ingestion
"""
import re
from collections import Counter

def validate_markdown_structure(md_path="tamarin-manual.md"):
    """Validate markdown structure and show statistics."""
    
    print("="*70)
    print("MARKDOWN STRUCTURE VALIDATION")
    print("="*70)
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n📄 File: {md_path}")
    print(f"📊 Total lines: {len(lines):,}")
    
    # Header pattern matching the ingestion script
    header_pattern = re.compile(r'^(#{1,4})\s+\*\*?(.+?)\*\*?\s*$|^(#{1,4})\s+(.+?)\s*$')
    
    headers = []
    level_counts = Counter()
    
    for line_num, line in enumerate(lines, start=1):
        match = header_pattern.match(line.rstrip())
        if match:
            if match.group(1):  # Format with bold
                hashes = match.group(1)
                title = match.group(2).strip()
            else:  # Format without bold
                hashes = match.group(3)
                title = match.group(4).strip()
            
            level = len(hashes)
            if title:  # Only count non-empty titles
                headers.append({
                    'line': line_num,
                    'level': level,
                    'title': title,
                    'raw': line.strip()
                })
                level_counts[level] += 1
    
    print(f"\n📋 Headers found: {len(headers)}")
    print(f"\n📊 Headers by level:")
    for level in sorted(level_counts.keys()):
        print(f"   Level {level} ({'#' * level}): {level_counts[level]} headers")
    
    print(f"\n📝 Sample headers (first 20):")
    for i, header in enumerate(headers, 1):
        indent = "  " * (header['level'] - 1)
        print(f"   {i}. {indent}[Line {header['line']}] {header['title']}")
    
    
    # Analyze content between headers
    print(f"\n📏 Content analysis:")
    content_sizes = []
    
    for i in range(len(headers)):
        start_line = headers[i]['line']
        end_line = headers[i+1]['line'] - 1 if i+1 < len(headers) else len(lines)
        
        # Calculate content size
        content = ''.join(lines[start_line:end_line]).strip()
        if content:
            content_sizes.append(len(content))
    
    if content_sizes:
        print(f"   Total sections with content: {len(content_sizes)}")
        print(f"   Smallest section: {min(content_sizes)} chars")
        print(f"   Largest section: {max(content_sizes):,} chars")
        print(f"   Average section: {sum(content_sizes)//len(content_sizes):,} chars")
        print(f"   Median section: {sorted(content_sizes)[len(content_sizes)//2]:,} chars")
        
        # Count sections that would need chunking
        chunk_size = 1000
        large_sections = sum(1 for size in content_sizes if size > chunk_size)
        print(f"\n   Sections > {chunk_size} chars: {large_sections} ({large_sections*100//len(content_sizes)}%)")
        
        # Estimate total chunks
        total_chunks = sum((size // chunk_size) + 1 if size > chunk_size else 1 
                          for size in content_sizes)
        print(f"   Estimated total chunks: {total_chunks}")
    
    # Show sections that will be chunked
    print(f"\n📦 Large sections that will be chunked (>1000 chars):")
    large_count = 0
    for i in range(min(len(headers), len(content_sizes))):
        if content_sizes[i] > 1000:
            large_count += 1
            if large_count <= 10:
                chunks_needed = (content_sizes[i] // 1000) + 1
                print(f"   {large_count}. '{headers[i]['title']}' - {content_sizes[i]:,} chars → {chunks_needed} chunks")
    
    if large_count > 10:
        print(f"   ... and {large_count - 10} more large sections")
    
    print("\n" + "="*70)
    print("✅ Validation complete!")
    print("="*70)

if __name__ == "__main__":
    validate_markdown_structure()
