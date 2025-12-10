# Tamarin Manual RAG System

A Retrieval-Augmented Generation (RAG) system for the Tamarin Prover manual with improved chunking and metadata.

## 🚀 Quick Start

### 1. Validate the Markdown Structure (Optional but Recommended)
```bash
python validate_markdown.py
```
This will show you:
- How many headers are detected
- Content size distribution
- Which sections will be chunked
- Estimated number of chunks

### 2. Clean Old Database (if rebuilding)
```bash
cleanup_rag.bat
```
Or manually:
```bash
rmdir /s /q tamarin_vectordb
del ingestion_log.json
```

### 3. Ingest the Manual into Vector Database
```bash
python tamarin_vector_ingestion.py
```
Expected output:
- Section extraction statistics
- Document creation progress
- Batch upload status
- Total documents ingested

### 4. Test the RAG System
```bash
python tamarin-rag-test-improved.py
```
This will:
- Show database statistics
- Run automated test queries
- Enter interactive mode for custom questions

## 📁 Files

### Core Scripts
- **`tamarin_vector_ingestion.py`** - Main ingestion script with improved parsing
- **`tamarin-rag-test-improved.py`** - Enhanced testing and query interface
- **`validate_markdown.py`** - Validation tool for markdown structure

### Utility Scripts
- **`cleanup_rag.bat`** - Convenient cleanup script
- **`RAG_REBUILD_SUMMARY.md`** - Detailed documentation of improvements

### Data Files
- **`tamarin-manual.md`** - Source markdown file (8794 lines)
- **`tamarin_vectordb/`** - Chroma vector database (generated)
- **`ingestion_log.json`** - Processing log with resume capability

## 🔧 Configuration

Edit these values in `tamarin_vector_ingestion.py`:

```python
MAX_SECTION_SIZE = 1000  # Maximum chunk size (characters)
CHUNK_OVERLAP = 150      # Overlap between chunks (characters)
MODEL_NAME = "gemini-embedding-001"  # Embedding model
```

### Tuning Recommendations

**For better precision (more specific results):**
- Decrease `MAX_SECTION_SIZE` to 600-800
- Keep `CHUNK_OVERLAP` at 150

**For better context (more complete answers):**
- Increase `MAX_SECTION_SIZE` to 1500-2000
- Increase `CHUNK_OVERLAP` to 200-250

**For faster processing:**
- Increase `batch_size` in ingestion (default: 5)
- Decrease `delay_seconds` (default: 3)

## 🎯 Key Improvements

### 1. Better Header Detection
- Handles mixed formats: `#`, `##`, `###`, `####`
- Processes bold markers: `### **Title**`
- More accurate section extraction

### 2. Optimized Chunking
- Smaller chunks (1000 vs 3000 chars) for better precision
- Smart overlap (150 chars) preserves context
- Natural break points at sentences and paragraphs

### 3. Enhanced Metadata
Each document includes:
- Section title and path
- Line numbers (start/end)
- Content length
- Chunk information (if split)
- Searchable keywords
- Section hierarchy level

### 4. Context Prepending
Each chunk starts with: `Section: [Title]\n\n[Content]`

This helps the embedding model understand context better.

## 📊 Expected Results

After ingestion, you should have:
- **~300-500 documents** (depending on chunking)
- **~100-150 unique sections**
- **Average chunk size**: 800-1000 characters
- **Processing time**: 5-10 minutes

## 🔍 Usage Examples

### Basic Query
```python
from tamarin_rag_test_improved import query_vectordb, print_results

docs = query_vectordb("How to install Tamarin on Windows?", k=5)
print_results(docs)
```

### Filtered Query (by section title)
```python
docs = query_vectordb(
    "installation steps", 
    k=3,
    filter_dict={"section_title": "Installation on Windows 10"}
)
```

### Database Inspection
```python
from tamarin_rag_test_improved import inspect_database
inspect_database()
```

## 🐛 Troubleshooting

### Issue: No results for queries
**Solution:**
1. Run `validate_markdown.py` to check parsing
2. Verify database exists: `dir tamarin_vectordb`
3. Check log: `type ingestion_log.json`
4. Rebuild database with cleanup script

### Issue: Results are too fragmented
**Solution:**
- Increase `MAX_SECTION_SIZE` to 1500-2000
- Increase overlap to 200-250
- Rebuild database

### Issue: Results are too generic
**Solution:**
- Decrease `MAX_SECTION_SIZE` to 600-800
- Increase `k` parameter in queries (try 10-15)
- Use more specific query terms

### Issue: Slow ingestion
**Solution:**
- Increase `batch_size` to 10
- Decrease `delay_seconds` to 2
- Check internet connection (embedding API calls)

## 📈 Performance Metrics

Track these metrics in `ingestion_log.json`:
- `processed_sections`: List of all processed sections
- `total_documents`: Total chunks in database
- `last_updated`: Last ingestion timestamp

## 🔄 Updating the Database

The system supports **incremental updates**:
1. New sections are automatically detected
2. Already processed sections are skipped
3. Progress is saved after each batch

To force a complete rebuild:
```bash
cleanup_rag.bat
python tamarin_vector_ingestion.py
```

## 💡 Tips

1. **Always validate first**: Run `validate_markdown.py` before ingestion
2. **Test queries**: Use the improved test script for interactive testing
3. **Monitor logs**: Check `ingestion_log.json` for processing details
4. **Adjust chunk size**: Experiment to find optimal size for your queries
5. **Use metadata filters**: Narrow down results by section or level

## 📚 Related Documentation

- `RAG_REBUILD_SUMMARY.md` - Detailed technical improvements
- `tamarin-manual.md` - Source document (Tamarin Prover Manual)

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review `ingestion_log.json` for errors
3. Run validation script to verify markdown parsing
4. Check console output for error messages

## 📝 License

This RAG system is for the Tamarin Prover Manual, which is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
