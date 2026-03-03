"""
PDF to Markdown Converter using PyMuPDF (fitz)
Converts PDF documents to Markdown format with proper formatting preservation.
Uses PyMuPDF4LLM for optimal conversion quality (2025 best practices).
"""

import fitz  # PyMuPDF
import os
import sys
from pathlib import Path


def convert_pdf_to_markdown_basic(pdf_path: str, output_path: str = None) -> str:
    """
    Convert PDF to Markdown using basic PyMuPDF text extraction.
    
    Args:
        pdf_path: Path to the input PDF file
        output_path: Path to save the output Markdown file (optional)
    
    Returns:
        Markdown formatted string
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        markdown_content = []
        
        print(f"Converting {pdf_path} to Markdown...")
        print(f"Total pages: {len(doc)}")
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Add page separator
            markdown_content.append(f"\n---\n**Page {page_num + 1}**\n---\n\n")
            
            # Extract text blocks with formatting information
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block["type"] == 0:  # Text block
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            text = span["text"]
                            font_size = span["size"]
                            font_flags = span["flags"]
                            
                            # Apply formatting based on font properties
                            # Bold text (flag 16)
                            if font_flags & 16:
                                text = f"**{text}**"
                            # Italic text (flag 2)
                            if font_flags & 2:
                                text = f"*{text}*"
                            
                            # Heading detection based on font size
                            if font_size > 16:
                                text = f"# {text}"
                            elif font_size > 14:
                                text = f"## {text}"
                            elif font_size > 12:
                                text = f"### {text}"
                            
                            line_text += text
                        
                        if line_text.strip():
                            markdown_content.append(line_text + "\n")
                    
                    markdown_content.append("\n")
        
        doc.close()
        
        # Join all content
        final_markdown = "".join(markdown_content)
        
        # Save to file if output path is provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_markdown)
            print(f"Markdown saved to: {output_path}")
        
        return final_markdown
    
    except Exception as e:
        print(f"Error converting PDF to Markdown: {e}")
        return None


def convert_pdf_to_markdown_pymupdf4llm(pdf_path: str, output_path: str = None) -> str:
    """
    Convert PDF to Markdown using PyMuPDF4LLM (recommended for 2025).
    This method provides better structure preservation and formatting.
    
    Args:
        pdf_path: Path to the input PDF file
        output_path: Path to save the output Markdown file (optional)
    
    Returns:
        Markdown formatted string
    """
    try:
        import pymupdf4llm
        
        print(f"Converting {pdf_path} to Markdown using PyMuPDF4LLM...")
        
        # Convert PDF to Markdown
        markdown_content = pymupdf4llm.to_markdown(pdf_path)
        
        # Save to file if output path is provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Markdown saved to: {output_path}")
        
        return markdown_content
    
    except ImportError:
        print("PyMuPDF4LLM not installed. Install it with: pip install pymupdf4llm")
        print("Falling back to basic conversion method...")
        return convert_pdf_to_markdown_basic(pdf_path, output_path)
    
    except Exception as e:
        print(f"Error converting PDF to Markdown: {e}")
        return None


def main():
    """Main function to handle command-line execution."""
    # Default paths
    base_dir = Path(__file__).parent
    pdf_path = base_dir / "Matter-1.4-Core-Specification-1.pdf"
    output_path = base_dir / "core_spec1.md"
    
    # Check if PDF exists
    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        print("Please provide the correct path to tamarin-manual.pdf")
        sys.exit(1)
    
    print("=" * 60)
    print("PDF to Markdown Converter")
    print("=" * 60)
    print(f"Input PDF: {pdf_path}")
    print(f"Output MD: {output_path}")
    print("=" * 60)
    print()
    
    # Try PyMuPDF4LLM first (best quality), then fallback to basic
    result = convert_pdf_to_markdown_pymupdf4llm(str(pdf_path), str(output_path))
    
    if result:
        print()
        print("=" * 60)
        print("Conversion completed successfully!")
        print(f"Output saved to: {output_path}")
        print(f"File size: {len(result)} characters")
        print("=" * 60)
    else:
        print("Conversion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
