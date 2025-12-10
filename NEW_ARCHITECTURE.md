# New FSM to Tamarin Conversion Architecture

## Overview
Completely restructured the conversion system with a clear separation of concerns and a streamlined flow.

## Architecture Components

### 1. **Generator LLM** (GPT-5.1)
- **Purpose**: Creates Tamarin code from FSM
- **Tool Access**: Only `db_query_tool` for syntax/example queries
- **Behavior**:
  - ALWAYS outputs complete Tamarin code (no partial responses)
  - Can query database when needs help with syntax
  - Receives judge feedback and fixes issues
  - Never saves files directly

### 2. **Validator** (Pure Function)
- **Purpose**: Parse Tamarin code using `tamarin-prover`
- **Input**: Tamarin code string
- **Output**: `(is_valid: bool, parser_output: str)`
- **No LLM involvement** - just runs the parser

### 3. **Judge LLM** (GPT-5.1)
- **Purpose**: Evaluates FSM fidelity and syntax correctness
- **Input**: 3 things - FSM data, Tamarin code, Parser output
- **Output**: `(is_approved: bool, feedback: str)`
- **Behavior**:
  - Checks if ALL FSM elements are correctly mapped
  - Validates syntax from parser output
  - Returns APPROVED or REJECTED with guidance

### 4. **Save Function** (Pure Function)
- **Purpose**: Persists approved code to disk
- **Called**: Only after judge approval
- **Outputs**: `.spthy` file + metadata JSON

## New Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    START: Load FSM                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Generator LLM                                      │
│  - Receives: FSM JSON + System Prompt                       │
│  - Action: Generates Tamarin code                           │
│  - Has access to: db_query_tool only                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
           ┌──────────────┐
           │ Has Tool     │
           │ Calls?       │
           └──┬────────┬──┘
              │ YES    │ NO
              │        │
              ▼        ▼
      ┌────────────┐  ┌─────────────────────────────────────┐
      │ Invoke     │  │ Extract Tamarin Code from Response  │
      │ Tools      │  │ (from triple backticks)             │
      │ (db_query) │  └────────────┬────────────────────────┘
      └─────┬──────┘               │
            │                      ▼
            │           ┌─────────────────────────────────────┐
            │           │ STEP 2: Validator                   │
            │           │ - Parse code with tamarin-prover    │
            │           │ - Returns: (is_valid, output)       │
            │           └─────────────┬───────────────────────┘
            │                         │
            │                         ▼
            │           ┌─────────────────────────────────────┐
            │           │ STEP 3: Judge LLM                   │
            │           │ - Input: FSM + Tamarin + Parser     │
            │           │ - Evaluates FSM fidelity + syntax   │
            │           │ - Returns: (approved, feedback)     │
            │           └─────────────┬───────────────────────┘
            │                         │
            └─────────────────────────┤
                                      ▼
                           ┌────────────────────┐
                           │ Approved?          │
                           └──┬──────────────┬──┘
                              │ YES          │ NO
                              │              │
                              ▼              ▼
                ┌─────────────────────┐  ┌──────────────────────┐
                │ STEP 4: Save        │  │ Send Feedback to     │
                │ - Save .spthy       │  │ Generator LLM        │
                │ - Save metadata     │  │ (Loop back to Step 1)│
                │ - EXIT              │  └──────────┬───────────┘
                └─────────────────────┘             │
                                                    │
                                                    └─────┐
                                                          │
                                      ┌───────────────────┘
                                      │
                                      │ (Max 15 iterations)
                                      │
                                      └──► Back to Generator

```

## Key Improvements

### ✅ Separation of Concerns
- **Generator**: Only generates code
- **Validator**: Only parses syntax
- **Judge**: Only evaluates quality
- **Save**: Only persists files

### ✅ Simplified Tool Usage
- Generator has only ONE tool: `db_query_tool`
- No more validation as a tool
- No more save as a tool

### ✅ Clear Data Flow
1. Generator creates code
2. Validator parses it
3. Judge evaluates all 3 inputs
4. If approved → save and exit
5. If rejected → feedback loop to generator

### ✅ Explicit Control Flow
- Tool calls → invoke and continue
- No tool calls → extract code → validate → judge
- Approved → save and exit
- Rejected → feedback and loop

### ✅ No Ambiguity
- Generator ALWAYS outputs code (never just text)
- Judge ALWAYS starts with "Status: APPROVED" or "Status: REJECTED"
- Clear termination condition (judge approval)

## Configuration

```python
GENERATOR_MODEL = "gpt-5.1"  # Creates Tamarin code
JUDGE_MODEL = "gpt-5.1"      # Evaluates quality
```

## File Structure

```
fsm_to_tamarin_conv.py
├── Config & Setup
├── Helper Functions
│   └── load_fsm_from_file()
├── Tool: db_query_tool (for Generator)
├── Validator: validate_tamarin_syntax()
├── Save: save_tamarin_protocol()
├── Judge: judge_tamarin_code()
├── Generator: create_generator_llm()
├── Main Loop: convert_fsm_to_tamarin()
└── Main Execution
```

## Output Artifacts

When approved, creates:
- `{protocol_name}_{timestamp}.spthy` - Tamarin theory file
- `{protocol_name}_{timestamp}_metadata.json` - Metadata about conversion

## Iteration Limit

- Max iterations: 15
- Each iteration = one attempt to generate and validate
- If limit reached without approval → exits with warning

## Logging

Each step prints detailed progress:
- 🔍 Database queries
- 📤 Generator calls
- ✅ Validation results
- 🧑‍⚖️ Judge evaluations
- 💾 Save operations

## Error Handling

- Generator errors → logged and retried
- Validator errors → reported to judge
- Judge errors → logged and rejected
- Save errors → logged and returned
