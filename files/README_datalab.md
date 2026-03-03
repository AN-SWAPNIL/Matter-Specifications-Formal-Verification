# Datalab.to Result Retrieval

This script retrieves previously processed PDF results from the Datalab.to Marker API playground.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements_datalab.txt
   ```

   Or directly:
   ```bash
   pip install requests
   ```

2. **Get your credentials:**
   - **API Key:** From your Datalab.to account settings
   - **Request ID:** From the playground URL after processing a document
     - Format: `https://www.datalab.to/playground/request_<ID>`
     - Example ID: `AwdqQPOdjhzZPq4W1iBgcA`

## Usage

### Quick Start

```bash
python retrieve_datalab_result.py
```

The script will:
1. Connect to Datalab API with your credentials
2. Retrieve the result for request ID `AwdqQPOdjhzZPq4W1iBgcA`
3. Save output to `./datalab_output/`:
   - `output.md` — Markdown conversion
   - `output.json` — Structured JSON data
   - `metadata.json` — Request metadata

### Custom Request ID

Edit `retrieve_datalab_result.py` and change:
```python
REQUEST_ID = "YOUR_REQUEST_ID_HERE"
```

## Troubleshooting

### "Request not found"
- Verify the request ID is correct (from playground URL)
- Check if the request has expired (Datalab may have retention limits)

### "Invalid API key"
- Get a fresh API key from your Datalab account settings
- Ensure no extra spaces in the key string

### "Still processing"
- Large PDFs can take several minutes
- Wait and run the script again

## Alternative: Using cURL

If you prefer not to use Python:

```bash
curl -X GET "https://www.datalab.to/api/v1/marker/AwdqQPOdjhzZPq4W1iBgcA" \
     -H "X-Api-Key: j8G3sXRcbQkxStJ14E3z2dt0tchKD294hgGtzLlLMwg"
```
The response will be JSON with the complete result including markdown, images (base64), and metadata.
## Output Structure

```
datalab_output/
├── output.md          # Converted markdown
├── output.json        # Structured data (tables, blocks, etc.)
└── metadata.json      # Request info, processing time, etc.
```

## Security Note

⚠️ **Never commit API keys to version control!**

- Move credentials to environment variables:
  ```python
  import os
  DATALAB_API_KEY = os.getenv("DATALAB_API_KEY", "your-default-key")
  REQUEST_ID = os.getenv("DATALAB_REQUEST_ID", "your-default-id")
  ```

- Set environment variables in your shell:
  ```bash
  # Windows PowerShell
  $env:DATALAB_API_KEY="your-key-here"
  $env:DATALAB_REQUEST_ID="your-id-here"
  
  # Linux/Mac
  export DATALAB_API_KEY="your-key-here"
  export DATALAB_REQUEST_ID="your-id-here"
  ```
