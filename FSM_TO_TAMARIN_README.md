# FSM to Tamarin Conversion Tool

An intelligent agent-based tool that converts Finite State Machine (FSM) descriptions into Tamarin security protocol models using LangChain and Google Gemini.

## 🎯 Features

- **RAG-Enhanced Conversion**: Queries the Tamarin manual vector database for accurate syntax
- **Automatic Syntax Validation**: Validates generated Tamarin code using `tamarin-prover`
- **Iterative Error Correction**: Automatically fixes syntax errors and re-validates
- **Comprehensive Logging**: Detailed console output for every step
- **Metadata Tracking**: Saves conversion metadata alongside protocol files
- **Tool-Based Architecture**: Uses LangChain tools for modular functionality

## 📋 Prerequisites

### Required Software
1. **Python 3.8+**
2. **Tamarin Prover** - Must be installed and accessible in PATH
   ```bash
   tamarin-prover --version
   ```
3. **Vector Database** - Run RAG ingestion first:
   ```bash
   python tamarin_vector_ingestion.py
   ```

### Required Python Packages
```bash
pip install langchain langchain-google-genai langchain-chroma langchain-core chromadb
```

## 🚀 Quick Start

### 1. Basic Usage
```bash
python fsm_to_tamarin_conv.py
```

This will:
- Load the FSM from `./codes/fsm_models/1.5_OnOff_Cluster_fsm.json`
- Convert it to Tamarin protocol
- Validate the syntax
- Save the output to `tamarin_outputs/` directory

### 2. Custom FSM File
Edit the `FSM_INPUT_FILE` variable in the script:
```python
FSM_INPUT_FILE = "./path/to/your/fsm.json"
```

## 📁 Directory Structure

```
FSM_Generator/
├── fsm_to_tamarin_conv.py      # Main conversion script
├── tamarin_outputs/             # Generated Tamarin protocols (created automatically)
│   ├── protocol_name_20241209_143022.spthy
│   └── protocol_name_20241209_143022_metadata.json
├── temp_tamarin_files/          # Temporary files for validation (created automatically)
│   └── temp_protocol_20241209_143022.spthy
├── tamarin_vectordb/            # RAG vector database
└── codes/fsm_models/            # Input FSM JSON files
```

## 🔧 Available Tools

The agent has access to three specialized tools:

### 1. `db_query_tool`
**Purpose**: Query the Tamarin manual for syntax and best practices

**Parameters**:
- `query` (str): Search query (e.g., "how to define rules")
- `k` (int): Number of results to return (default: 5)
- `section` (str, optional): Filter by section title

**Example**:
```python
db_query_tool("tamarin rule syntax", k=3)
```

### 2. `validate_tamarin_syntax`
**Purpose**: Validate Tamarin code syntax using tamarin-prover

**Parameters**:
- `tamarin_code` (str): Complete Tamarin protocol code
- `protocol_name` (str): Name for temporary file (default: "temp_protocol")

**Returns**: Validation status with stdout/stderr from tamarin-prover

**Example**:
```python
validate_tamarin_syntax(code, "OnOff_Protocol")
```

### 3. `save_tamarin_protocol`
**Purpose**: Save validated protocol to file with metadata

**Parameters**:
- `tamarin_code` (str): Complete Tamarin protocol code
- `protocol_name` (str): Protocol name (used in filename)
- `metadata` (dict, optional): Additional metadata to save

**Returns**: Success message with file paths

**Example**:
```python
save_tamarin_protocol(code, "OnOff_Cluster", {"fsm_source": "1.5_OnOff.json"})
```

## 📊 FSM Input Format

The FSM should be in JSON format with the following structure:

```json
{
  "name": "OnOff_Cluster",
  "states": [
    {
      "name": "Off",
      "type": "initial"
    },
    {
      "name": "On",
      "type": "normal"
    }
  ],
  "transitions": [
    {
      "from": "Off",
      "to": "On",
      "event": "TurnOn",
      "action": "device_on"
    },
    {
      "from": "On",
      "to": "Off",
      "event": "TurnOff",
      "action": "device_off"
    }
  ],
  "initial_state": "Off"
}
```

## 📋 Output Files

### 1. Tamarin Protocol File (.spthy)
Location: `tamarin_outputs/[protocol_name]_[timestamp].spthy`

Contains:
- Theory declaration
- Builtin declarations
- Rule definitions
- Security lemmas

### 2. Metadata File (.json)
Location: `tamarin_outputs/[protocol_name]_[timestamp]_metadata.json`

Contains:
- Protocol name
- Timestamp
- Code length
- Output file path
- Custom metadata (if provided)

### 3. Temporary Validation Files
Location: `temp_tamarin_files/`

These are created during validation and can be deleted after successful conversion.

## 🔍 Logging and Debugging

The tool provides detailed console output:

### Tool Invocation Logs
```
🔍 DB Query Tool called:
   Query: 'tamarin rule syntax'
   Top-k: 5
   Section filter: None
   ✅ Found 5 relevant chunks
   📄 Returning 3456 characters of context
```

### Validation Logs
```
✅ Syntax Validator called:
   Protocol name: OnOff_Protocol
   Code length: 1234 characters
   📝 Writing to: temp_tamarin_files/OnOff_Protocol_20241209_143022.spthy
   🔧 Running tamarin-prover parse...
   ✅ VALID (Return code: 0)
```

### Save Operation Logs
```
💾 Save Protocol Tool called:
   Protocol name: OnOff_Cluster
   Code length: 1234 characters
   📝 Saving Tamarin code to: tamarin_outputs/OnOff_Cluster_20241209_143022.spthy
   📝 Saving metadata to: tamarin_outputs/OnOff_Cluster_20241209_143022_metadata.json
   ✅ Protocol saved successfully!
```

## ⚙️ Configuration

Edit these variables at the top of `fsm_to_tamarin_conv.py`:

```python
# API Configuration
os.environ["GOOGLE_API_KEY"] = "your-api-key-here"

# Model Configuration
EMBED_MODEL = "gemini-embedding-001"

# Vector Database
PERSIST_DIR = "tamarin_vectordb"
COLLECTION_NAME = "tamarin_manual"

# Output Directories
OUTPUT_DIR = "tamarin_outputs"
TEMP_DIR = "temp_tamarin_files"

# LLM Model
model="gemini-2.0-flash-exp"  # In create_fsm_to_tamarin_agent()
temperature=0.1
```

## 🔄 Conversion Process

The agent follows this workflow:

1. **Load FSM** → Parse JSON input file
2. **Query Manual** → Use `db_query_tool` for Tamarin syntax
3. **Generate Code** → Create Tamarin protocol using LLM
4. **Validate** → Use `validate_tamarin_syntax` to check syntax
5. **Fix Errors** → If validation fails, analyze errors and regenerate
6. **Re-validate** → Check fixed code again
7. **Save** → Use `save_tamarin_protocol` to save final valid protocol
8. **Return** → Provide summary and file paths

## 🐛 Troubleshooting

### Issue: "tamarin-prover not found"
**Solution**: Install Tamarin Prover and ensure it's in your PATH
```bash
which tamarin-prover  # On Linux/Mac
where tamarin-prover  # On Windows
```

### Issue: "No relevant documents found"
**Solution**: Ensure the vector database is built
```bash
python tamarin_vector_ingestion.py
```

### Issue: Validation timeout
**Solution**: Increase timeout in `validate_tamarin_syntax`:
```python
timeout=120  # Increase from 60 to 120 seconds
```

### Issue: Max iterations reached
**Solution**: Increase max_iterations in `convert_fsm_to_tamarin`:
```python
max_iterations = 20  # Increase from 15
```

## 📚 Examples

### Example 1: Simple On/Off Protocol
Input FSM: `1.5_OnOff_Cluster_fsm.json`
```json
{
  "name": "OnOff",
  "states": ["Off", "On"],
  "transitions": [
    {"from": "Off", "to": "On", "event": "TurnOn"},
    {"from": "On", "to": "Off", "event": "TurnOff"}
  ]
}
```

Output: Complete Tamarin protocol with rules and lemmas

### Example 2: Custom Conversion
```python
# Load custom FSM
fsm_data = load_fsm_from_file("./my_protocols/custom_fsm.json")

# Convert
result = convert_fsm_to_tamarin(fsm_data, fsm_source="custom_fsm.json")

print(result)
```

## 🎓 Understanding the Code

### Agent Architecture
The tool uses a **tool-calling architecture**:
- LLM receives the conversion request
- LLM decides which tools to call and when
- Tools execute and return results
- LLM processes results and continues or finishes

### Message Flow
```
User Request → System Prompt + User Message
            ↓
         LLM Response
            ↓
    Tool Calls Detected?
      Yes ↓         No → Final Response
   Execute Tools
      ↓
   Tool Results → Back to LLM
      ↓
   Continue Loop
```

## 🚧 Limitations

1. **Tamarin Prover Required**: Must be installed separately
2. **API Limits**: Subject to Google Gemini API rate limits
3. **Complex FSMs**: Very large FSMs may require multiple iterations
4. **Manual Review**: Always review generated protocols before use

## 📈 Performance Tips

1. **Smaller FSMs**: Break large FSMs into smaller components
2. **Specific Queries**: Use targeted queries for RAG lookups
3. **Increase Context**: Adjust `k` parameter in db_query_tool for more context
4. **Temperature**: Lower temperature (0.1) for more deterministic output

## 📝 License

This tool is part of the FSM Generator project for Tamarin security protocol analysis.

## 🤝 Contributing

To improve the tool:
1. Add more specialized tools
2. Enhance error recovery logic
3. Improve FSM parsing
4. Add support for more complex FSM features

## 📞 Support

Check console logs for detailed error messages and debugging information.
