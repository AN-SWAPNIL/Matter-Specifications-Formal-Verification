# PDF to Markdown Converter

This tool converts PDF documents to Markdown format using PyMuPDF (fitz) with 2025 best practices.

## Features

- **Dual Conversion Methods**:
  - **PyMuPDF4LLM** (Recommended): State-of-the-art conversion with excellent structure preservation
  - **Basic PyMuPDF**: Fallback method with manual formatting detection
- Preserves document structure (headings, bold, italic)
- Handles multi-page documents
- Automatic page numbering and separation
- UTF-8 encoding support

## Installation

Make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install PyMuPDF pymupdf4llm
```

## Usage

### Command Line

Simply run the script to convert `tamarin-manual.pdf` to Markdown:

```bash
python pdf_to_markdown_converter.py
```

This will:
1. Look for `tamarin-manual.pdf` in the parent directory
2. Convert it to Markdown format
3. Save the output as `tamarin-manual.md`

### As a Python Module

```python
from pdf_to_markdown_converter import convert_pdf_to_markdown_pymupdf4llm

# Convert PDF to Markdown
markdown_text = convert_pdf_to_markdown_pymupdf4llm(
    "path/to/your.pdf",
    "path/to/output.md"
)

# Or use basic method
from pdf_to_markdown_converter import convert_pdf_to_markdown_basic

markdown_text = convert_pdf_to_markdown_basic(
    "path/to/your.pdf",
    "path/to/output.md"
)
```

## Methods Comparison

### PyMuPDF4LLM (Recommended)
- Best for: Technical documents, academic papers, manuals
- Pros: Superior structure preservation, table detection, better formatting
- Cons: Requires additional package

### Basic PyMuPDF
- Best for: Simple text documents
- Pros: No extra dependencies, faster processing
- Cons: Less sophisticated formatting detection

## Output Format

The converter creates a Markdown file with:
- Page separators for multi-page documents
- Proper heading hierarchy (H1, H2, H3)
- Bold and italic text preservation
- Clean, readable formatting

## Example Output Structure

```markdown
---
**Page 1**
---

# Main Title

## Section Heading

Regular text with **bold** and *italic* formatting.

---
**Page 2**
---

### Subsection

More content...
```

## Troubleshooting

### PyMuPDF4LLM not found
If you see an import error, install the package:
```bash
pip install pymupdf4llm
```

### PDF not found
Make sure `tamarin-manual.pdf` is in the `FSM_Generator` directory, or update the path in the script.

### Encoding issues
The script uses UTF-8 encoding by default. If you encounter issues, check your system's locale settings.

## 2025 Best Practices

This implementation follows current best practices:
- Uses PyMuPDF4LLM for optimal conversion quality
- Preserves document structure for LLM/RAG applications
- Handles complex formatting (tables, lists, code blocks)
- Efficient memory usage for large documents
- Error handling and fallback mechanisms

## License

Part of the FSM_Generator project for Matter Protocol analysis.
