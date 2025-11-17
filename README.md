# Matter Protocol FSM Generator

An automated system for extracting Finite State Machines (FSMs) from Matter IoT protocol specification using LLM-as-Judge iterative refinement.

## Overview

This system automatically generates precise FSM models from the Matter Application Cluster Specification PDF through a three-stage pipeline:

1. **TOC Extraction** - Extracts Table of Contents with cluster sections and page ranges
2. **Cluster Detail Extraction** - Extracts structured cluster information (attributes, commands, events, behaviors)
3. **FSM Generation with Judge** - Creates FSMs with iterative refinement using LLM-as-judge validation
4. **Multi-Model Support** - Works with any LLM provider (Gemini, GPT, Claude, etc.)

## Architecture

### Pipeline Flow

```
Matter PDF → TOC Extraction → Cluster Detail Extraction → FSM Generation → Judge Validation → Approved FSM
```

### Core Components

1. **`matter_toc_extractor.py`** - Extracts Table of Contents from PDF

   - Manual parsing of PDF structure without AI/RAG
   - Identifies all cluster sections with page ranges
   - Extracts subsections within each cluster
   - Outputs `matter_clusters_toc.json` with navigation data

2. **`cluster_detail_extractor.py`** - Extracts detailed cluster specifications

   - Parses PDF sections (Attributes, Commands, Events, Features, Data Types, etc.)
   - Uses TOC for precise page navigation
   - Outputs individual JSON files per cluster in `cluster_details/`
   - Uses specialized prompts for each section type

3. **`cluster_fsm_generator.py`** - Generates FSMs with LLM-as-judge

   - Takes cluster details as input
   - Generates FSM with behavioral analysis
   - Judge validates correctness iteratively (max 10 attempts)
   - Outputs approved FSMs to `fsm_models/`

4. **`config.py`** - Centralized configuration
   - Model settings (name, provider, temperature, tokens)
   - Extraction prompts for all cluster sections
   - FSM generation prompt template
   - PDF paths and output directories

## Quick Start

### Prerequisites

```bash
# Python 3.8+
python --version

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
python -m pip install -r simple_toc_extractor/requirements.txt
```

### Configuration

1. **Set API Key** (`.env` file):

```bash
GOOGLE_API_KEY=your_api_key_here
```

2. **Configure Model** (`config.py`):

```python
LLM_MODEL = "gemini-2.5-pro"  # or "gpt-4", "claude-3-5-sonnet"
MODEL_PROVIDER = "google_genai"  # or "openai", "anthropic"
LLM_TEMPERATURE = 0.0
LLM_MAX_OUTPUT_TOKENS = 32768
```

### Usage

#### Step 0: Extract TOC (One-time setup)

```bash
cd simple_toc_extractor
python matter_toc_extractor.py
```

**Output**: `matter_clusters_toc.json` - Contains all cluster sections with page ranges and subsections

**What it does**:

- Scans PDF Table of Contents
- Maps cluster sections to page numbers
- Identifies subsections within clusters
- Creates navigation index for extraction

#### Step 1: Extract Cluster Details

```bash
python cluster_detail_extractor.py
```

Edit `main()` function to specify cluster number:

```python
extractor.process_cluster_by_number(cluster_number=4)  # Extract cluster #4
```

**Output**: `cluster_details/{section}_{cluster_name}_detail.json`

**What it does**:

- Reads TOC to locate cluster pages
- Extracts attributes, commands, events, features
- Parses behavioral logic and data types
- Saves structured JSON per cluster

#### Step 2: Generate FSM

```bash
python cluster_fsm_generator.py cluster_details/1.5_OnOff_Cluster_detail.json fsm_models
```

Or use default paths:

```bash
python cluster_fsm_generator.py
```

**Output**: `fsm_models/{section}_{cluster_name}_fsm.json`

**What it does**:

- Analyzes cluster details for state behavior
- Generates FSM with states and transitions
- Judge evaluates and provides feedback
- Iteratively refines until approval (max 10 attempts)

## Project Structure

```
FSM_Generator/
├── simple_toc_extractor/
│   ├── matter_toc_extractor.py        # Extract TOC from PDF (manual parsing)
│   ├── cluster_detail_extractor.py    # Extract cluster specifications (LLM)
│   ├── cluster_fsm_generator.py       # Generate FSMs with judge (LLM)
│   ├── config.py                      # Centralized configuration
│   ├── matter_clusters_toc.json       # Cluster TOC (section numbers, pages)
│   ├── cluster_details/               # Extracted cluster JSON files
│   ├── fsm_models/                    # Generated FSM JSON files
│   ├── requirements.txt               # Python dependencies
│   └── .env                           # API keys
└── README.md                          # This file
```

## Output Formats

### Cluster Detail JSON

```json
{
  "cluster_info": {
    "cluster_name": "On/Off Cluster",
    "cluster_ids": [...],
    "features": [...],
    "attributes": [...],
    "commands": [...],
    "events": [...],
    "data_types": [...],
    "references": [...]
  },
  "metadata": {
    "source_pages": "64-74",
    "section_number": "1.5",
    "category": "General"
  }
}
```

### FSM JSON

```json
{
  "fsm_model": {
    "cluster_name": "On/Off Cluster",
    "cluster_id": "0x0006",
    "states": [
      {
        "name": "Off_Idle",
        "description": "Device is off, no timers active",
        "is_initial": true,
        "invariants": ["OnOff == FALSE", "OnTime == 0"],
        "attributes_monitored": ["OnOff", "OnTime"]
      }
    ],
    "transitions": [
      {
        "from_state": "Off_Idle",
        "to_state": "On_Idle",
        "trigger": "On",
        "guard_condition": "FeatureMap.OFFONLY == FALSE",
        "actions": ["set OnOff := TRUE"],
        "response_command": null,
        "timing_requirements": null
      }
    ],
    "initial_state": "Off_Idle",
    "attributes_used": ["OnOff (S,N,R,V)", "OnTime (RW,VO)"],
    "commands_handled": ["Off", "On", "Toggle"],
    "events_generated": [],
    "data_types_used": ["OnOffControlBitmap"],
    "scene_behaviors": ["OnOff attribute is scene-capable"],
    "definitions": [
      {
        "term": "LT Feature",
        "definition": "Lighting feature enabling timer-based operations",
        "usage_context": "Used in guards to check timing availability"
      }
    ],
    "references": [
      {
        "id": "0x0005",
        "name": "Scenes Management Cluster",
        "description": "Scene storage for scene-capable attributes"
      }
    ],
    "metadata": {
      "generation_timestamp": "2025-11-17T...",
      "generation_attempts": 5,
      "judge_approved": true,
      "source_metadata": {
        "extraction_method": "AI_behavioral_analysis",
        "source_pages": "64-74",
        "section_number": "1.5"
      }
    }
  }
}
```

## Key Features

### 1. LLM-as-Judge Validation

- FSM generator creates initial model
- Judge evaluates correctness against specification
- Iterative refinement until approval (max 10 attempts)
- Strict evaluation criteria ensure accuracy

### 2. Model-Agnostic Design

- Supports any LangChain-compatible model
- Easy switching between providers (Gemini, GPT, Claude)
- Consistent interface via `init_chat_model`

### 3. Comprehensive Extraction

- **TOC Parsing**: Manual PDF structure analysis without AI overhead
- **Section-specific prompts**: Dedicated prompts for each cluster component
- Extracts attributes, commands, events, features, data types
- Captures behavioral logic from "Effect on Receipt"
- Documents dependencies and references
- Page-accurate navigation via TOC index

### 4. Structured Metadata

- Generation tracking (attempts, timestamp, approval status)
- Source traceability (pages, sections, extraction method)
- Definitions for technical terms and functions
- References to external clusters/specifications

### 5. Behavioral Modeling

- Timer-based transitions with countdown logic
- Feature-dependent command availability
- Event generation and event-driven transitions
- Scene store/recall behaviors
- Guard conditions with data type constraints

## Configuration Options

### Model Settings (`config.py`)

```python
# API Configuration
API_KEY = os.getenv('GOOGLE_API_KEY')
LLM_MODEL = "gemini-2.5-pro"
MODEL_PROVIDER = "google_genai"
LLM_TEMPERATURE = 0.0
LLM_MAX_OUTPUT_TOKENS = 32768

# Extraction Settings
CLUSTER_PAGE_BUFFER = 0
SUBSECTION_PAGE_BUFFER = 0

# Prompt Templates
FSM_GENERATION_PROMPT_TEMPLATE = """..."""
COMMANDS_EXTRACTION_PROMPT = """..."""
# ... more prompts
```

### Switching Models

```python
# Use GPT-4
LLM_MODEL = "gpt-4"
MODEL_PROVIDER = "openai"
API_KEY = os.getenv('OPENAI_API_KEY')

# Use Claude
LLM_MODEL = "claude-3-5-sonnet-20241022"
MODEL_PROVIDER = "anthropic"
API_KEY = os.getenv('ANTHROPIC_API_KEY')
```

## Advanced Usage

### Complete Pipeline

Run full pipeline for a cluster:

```bash
# Step 0: Extract TOC (once)
python matter_toc_extractor.py

# Step 1: Extract cluster details
python cluster_detail_extractor.py  # Edit main() for cluster number

# Step 2: Generate FSM
python cluster_fsm_generator.py cluster_details/1.5_OnOff_Cluster_detail.json fsm_models
```

### Batch Processing

Extract multiple clusters:

```python
for cluster_num in range(1, 10):
    extractor.process_cluster_by_number(cluster_number=cluster_num)
```

### Custom Prompts

Modify prompts in `config.py` for specific extraction needs:

- `ATTRIBUTES_EXTRACTION_PROMPT`
- `COMMANDS_EXTRACTION_PROMPT`
- `FSM_GENERATION_PROMPT_TEMPLATE`

### Judge Strictness

Adjust judge prompt in `cluster_fsm_generator.py` for different validation levels.

## Dependencies

```txt
PyMuPDF                    # PDF processing
pymupdf4llm                # Markdown extraction
langchain                  # LLM framework
langchain-google-genai     # Google Gemini
langchain-openai           # OpenAI GPT (optional)
langchain-anthropic        # Anthropic Claude (optional)
python-dotenv              # Environment variables
```

## Troubleshooting

### Virtual Environment Issues

If pip fails, use:

```bash
python -m pip install -r requirements.txt
```

### API Key Errors

Ensure `.env` file exists with correct key:

```bash
GOOGLE_API_KEY=your_actual_key_here
```

### Import Errors

Check LangChain version compatibility:

```bash
pip install --upgrade langchain langchain-core langchain-google-genai
```

## Examples

See `fsm_models/` and `cluster_details/` directories for example outputs from different model runs:

- `fsm_models_g2.5p/` - Gemini 2.5 Pro outputs
- `fsm_models_g2.5f/` - Gemini 2.5 Flash outputs
- `fsm_models_gpt4o/` - GPT-4 outputs

## Contributing

This is a research project. Improvements welcome:

- Enhanced prompt engineering
- Additional cluster section handlers
- Better validation logic
- Visualization tools

## License

Research use only. Refer to Matter specification license for specification content.
