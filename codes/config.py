"""
Configuration file for Matter PDF TOC Extractor
Customize extraction parameters and settings here
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv('OPENAI_API_KEY')  # Can be any provider's API key
LLM_MODEL = "gpt-5.1"  # Model name (e.g., "gpt-4", "claude-3-5-sonnet", "gemini-2.5-pro")
MODEL_PROVIDER = "openai"  # LangChain model provider (e.g., "openai", "anthropic", "google_genai")
LLM_TEMPERATURE = 0.0  # More deterministic for detailed extraction
LLM_MAX_OUTPUT_TOKENS = 16384  # Significantly increased for comprehensive behavioral extraction

# PDF Processin**STEP 4:**STEP 5: FEATURE VALIDATION**EMANTICS**ation
PDF_FILENAME = "Matter-1.4-Application-Cluster-Specification.pdf"
PDF_PATH = os.path.join(os.path.dirname(__file__), "..", PDF_FILENAME)
MAX_TOC_PAGES = 50  # Maximum pages to scan for TOC content

# Vector Store Configuration
EMBEDDINGS_MODEL = "models/embedding-001"
CHUNK_SIZE = 1500  # Increased for better table capture
CHUNK_OVERLAP = 500  # More overlap for table continuations
VECTOR_SEARCH_K = 15  # More documents for comprehensive context

# Output Configuration
OUTPUT_JSON_FILE = "matter_clusters_toc.json"
RAW_TOC_FILE = "raw_toc.txt"
OUTPUT_DIRECTORY = os.path.dirname(__file__)

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Page buffer for cluster extraction (pages before and after cluster boundaries)
CLUSTER_PAGE_BUFFER = 0  # Increased to capture more context and table continuations

# Page offset - number of pages before actual content starts (TOC pages, covers, etc.)
PDF_PAGE_OFFSET = 4  # Actual content starts at PDF page 5, but TOC refers to logical page 1

# Page buffer for subsection extraction (pages before and after subsection boundaries)
SUBSECTION_PAGE_BUFFER = 0  # Buffer for subsection text extraction

# TOC Pattern Recognition
TOC_INDICATORS = [
    "table of contents",
    "contents", 
    "cluster",
    "section",
    r"\d+\.\d+\..*\.\.\.*\d+",  # Pattern like "6.2. Account Login ... 471"
]

# Manual Cluster Data (fallback) - Complete list based on provided TOC
# This data is used when AI extraction fails
MANUAL_CLUSTER_DATA = [
    # General Clusters (Section 1)
    {"name": "Identify Cluster", "section": "1.2", "start": 26, "end": 31, "category": "General"},
    {"name": "Groups Cluster", "section": "1.3", "start": 31, "end": 39, "category": "General"},
    {"name": "Scenes Management Cluster", "section": "1.4", "start": 39, "end": 60, "category": "General"},
    {"name": "On/Off Cluster", "section": "1.5", "start": 60, "end": 70, "category": "General"},
    {"name": "Level Control Cluster", "section": "1.6", "start": 70, "end": 85, "category": "General"},
    {"name": "Boolean State Cluster", "section": "1.7", "start": 85, "end": 86, "category": "General"},
    {"name": "Boolean State Configuration Cluster", "section": "1.8", "start": 86, "end": 92, "category": "General"},
    {"name": "Mode Select Cluster", "section": "1.9", "start": 92, "end": 97, "category": "General"},
    {"name": "Mode Base Cluster", "section": "1.10", "start": 97, "end": 106, "category": "General"},
    {"name": "Low Power Cluster", "section": "1.11", "start": 106, "end": 107, "category": "General"},
    {"name": "Wake On LAN Cluster", "section": "1.12", "start": 107, "end": 108, "category": "General"},
    {"name": "Switch Cluster", "section": "1.13", "start": 108, "end": 127, "category": "General"},
    {"name": "Operational State Cluster", "section": "1.14", "start": 127, "end": 138, "category": "General"},
    {"name": "Alarm Base Cluster", "section": "1.15", "start": 138, "end": 141, "category": "General"},
    {"name": "Messages Cluster", "section": "1.16", "start": 141, "end": 151, "category": "General"},
    {"name": "Service Area Cluster", "section": "1.17", "start": 151, "end": 167, "category": "General"},
    
    # Measurement and Sensing Clusters (Section 2)
    {"name": "Illuminance Measurement Cluster", "section": "2.2", "start": 173, "end": 175, "category": "Measurement and Sensing"},
    {"name": "Temperature Measurement Cluster", "section": "2.3", "start": 175, "end": 176, "category": "Measurement and Sensing"},
    {"name": "Pressure Measurement Cluster", "section": "2.4", "start": 176, "end": 179, "category": "Measurement and Sensing"},
    {"name": "Flow Measurement Cluster", "section": "2.5", "start": 179, "end": 181, "category": "Measurement and Sensing"},
    {"name": "Water Content Measurement Clusters", "section": "2.6", "start": 181, "end": 182, "category": "Measurement and Sensing"},
    {"name": "Occupancy Sensing Cluster", "section": "2.7", "start": 182, "end": 192, "category": "Measurement and Sensing"},
    {"name": "Resource Monitoring Clusters", "section": "2.8", "start": 192, "end": 197, "category": "Measurement and Sensing"},
    {"name": "Air Quality Cluster", "section": "2.9", "start": 197, "end": 198, "category": "Measurement and Sensing"},
    {"name": "Concentration Measurement Clusters", "section": "2.10", "start": 198, "end": 204, "category": "Measurement and Sensing"},
    {"name": "Smoke CO Alarm Cluster", "section": "2.11", "start": 204, "end": 214, "category": "Measurement and Sensing"},
    {"name": "Electrical Energy Measurement Cluster", "section": "2.12", "start": 214, "end": 222, "category": "Measurement and Sensing"},
    {"name": "Electrical Power Measurement Cluster", "section": "2.13", "start": 222, "end": 235, "category": "Measurement and Sensing"},
    
    # Lighting Clusters (Section 3)
    {"name": "Color Control Cluster", "section": "3.2", "start": 235, "end": 277, "category": "Lighting"},
    {"name": "Ballast Configuration Cluster", "section": "3.3", "start": 277, "end": 285, "category": "Lighting"},
    
    # HVAC Clusters (Section 4)
    {"name": "Pump Configuration and Control Cluster", "section": "4.2", "start": 285, "end": 299, "category": "HVAC"},
    {"name": "Thermostat Cluster", "section": "4.3", "start": 299, "end": 348, "category": "HVAC"},
    {"name": "Fan Control Cluster", "section": "4.4", "start": 348, "end": 357, "category": "HVAC"},
    {"name": "Thermostat User Interface Configuration Cluster", "section": "4.5", "start": 357, "end": 359, "category": "HVAC"},
    {"name": "Valve Configuration and Control Cluster", "section": "4.6", "start": 359, "end": 369, "category": "HVAC"},
    
    # Closures Clusters (Section 5)
    {"name": "Door Lock Cluster", "section": "5.2", "start": 369, "end": 449, "category": "Closures"},
    {"name": "Window Covering Cluster", "section": "5.3", "start": 449, "end": 469, "category": "Closures"},
    
    # Media Clusters (Section 6)
    {"name": "Account Login Cluster", "section": "6.2", "start": 471, "end": 476, "category": "Media"},
    {"name": "Application Basic Cluster", "section": "6.3", "start": 476, "end": 479, "category": "Media"},
    {"name": "Application Launcher Cluster", "section": "6.4", "start": 479, "end": 484, "category": "Media"},
    {"name": "Audio Output Cluster", "section": "6.5", "start": 484, "end": 487, "category": "Media"},
    {"name": "Channel Cluster", "section": "6.6", "start": 487, "end": 503, "category": "Media"},
    {"name": "Content Launcher Cluster", "section": "6.7", "start": 503, "end": 517, "category": "Media"},
    {"name": "Keypad Input Cluster", "section": "6.8", "start": 517, "end": 522, "category": "Media"},
    {"name": "Media Input Cluster", "section": "6.9", "start": 522, "end": 525, "category": "Media"},
    {"name": "Media Playback Cluster", "section": "6.10", "start": 525, "end": 542, "category": "Media"},
    {"name": "Target Navigator Cluster", "section": "6.11", "start": 542, "end": 546, "category": "Media"},
    {"name": "Content App Observer Cluster", "section": "6.12", "start": 546, "end": 548, "category": "Media"},
    {"name": "Content Control Cluster", "section": "6.13", "start": 548, "end": 567, "category": "Media"},
    
    # Robot Clusters (Section 7)
    {"name": "RVC Run Mode Cluster", "section": "7.2", "start": 567, "end": 571, "category": "Robots"},
    {"name": "RVC Clean Mode Cluster", "section": "7.3", "start": 571, "end": 574, "category": "Robots"},
    {"name": "RVC Operational State Cluster", "section": "7.4", "start": 574, "end": 579, "category": "Robots"},
    
    # Home Appliance Clusters (Section 8)
    {"name": "Temperature Control Cluster", "section": "8.2", "start": 580, "end": 584, "category": "Home Appliances"},
    {"name": "Dishwasher Mode Cluster", "section": "8.3", "start": 584, "end": 586, "category": "Home Appliances"},
    {"name": "Dishwasher Alarm Cluster", "section": "8.4", "start": 586, "end": 587, "category": "Home Appliances"},
    {"name": "Laundry Washer Mode Cluster", "section": "8.5", "start": 587, "end": 590, "category": "Home Appliances"},
    {"name": "Laundry Washer Controls Cluster", "section": "8.6", "start": 590, "end": 593, "category": "Home Appliances"},
    {"name": "Refrigerator And Temperature Controlled Cabinet Mode Cluster", "section": "8.7", "start": 593, "end": 595, "category": "Home Appliances"},
    {"name": "Refrigerator Alarm Cluster", "section": "8.8", "start": 595, "end": 597, "category": "Home Appliances"},
    {"name": "Laundry Dryer Controls Cluster", "section": "8.9", "start": 597, "end": 598, "category": "Home Appliances"},
    {"name": "Oven Cavity Operational State Cluster", "section": "8.10", "start": 598, "end": 600, "category": "Home Appliances"},
    {"name": "Oven Mode Cluster", "section": "8.11", "start": 600, "end": 603, "category": "Home Appliances"},
    {"name": "Microwave Oven Mode Cluster", "section": "8.12", "start": 603, "end": 605, "category": "Home Appliances"},
    {"name": "Microwave Oven Control Cluster", "section": "8.13", "start": 605, "end": 613, "category": "Home Appliances"},
    
    # Energy Management Clusters (Section 9)
    {"name": "Device Energy Management Cluster", "section": "9.2", "start": 613, "end": 650, "category": "Energy Management"},
    {"name": "Energy EVSE Cluster", "section": "9.3", "start": 650, "end": 677, "category": "Energy Management"},
    {"name": "Energy EVSE Mode Cluster", "section": "9.4", "start": 677, "end": 680, "category": "Energy Management"},
    {"name": "Water Heater Management Cluster", "section": "9.5", "start": 680, "end": 687, "category": "Energy Management"},
    {"name": "Water Heater Mode Cluster", "section": "9.6", "start": 687, "end": 690, "category": "Energy Management"},
    {"name": "Energy Preference Cluster", "section": "9.7", "start": 690, "end": 694, "category": "Energy Management"},
    {"name": "Device Energy Management Mode Cluster", "section": "9.8", "start": 694, "end": 699, "category": "Energy Management"},
    
    # Network Infrastructure Clusters (Section 10)
    {"name": "Wi-Fi Network Management Cluster", "section": "10.2", "start": 699, "end": 702, "category": "Network Infrastructure"},
    {"name": "Thread Border Router Management Cluster", "section": "10.3", "start": 702, "end": 707, "category": "Network Infrastructure"},
    {"name": "Thread Network Directory Cluster", "section": "10.4", "start": 707, "end": 712, "category": "Network Infrastructure"},
]

# AI Extraction Prompt Template
# Manual extraction configuration - no AI prompts needed

# FSM Generation Configuration
FSM_GENERATION_PROMPT_TEMPLATE = """
You are a Matter IoT protocol expert who generates precise Finite State Machine models from Matter Application Cluster specifications.

CLUSTER SPECIFICATION TO ANALYZE:
{cluster_info}

**UNIVERSAL FSM GENERATION APPROACH:**

**STEP 1: CLUSTER BEHAVIORAL ANALYSIS**
Analyze the cluster specification to determine behavioral patterns:
- **Attribute-driven states**: States correspond to meaningful attribute value combinations
- **Command semantics**: Extract behavioral logic from "effect_on_receipt" descriptions  
- **Timer-based transitions**: Identify countdown timers and automatic state changes
- **Conditional logic**: Commands with if/then/else branches require multiple transitions
- **Feature constraints**: Only use features defined in the specification

**STEP 2: STATE IDENTIFICATION**
Define states based on cluster attributes and operational conditions:
- States represent actual device behavior, not internal processing
- Use attribute values to determine state invariants
- Include timer states if countdown attributes exist
- Model fault/error states if specified in cluster
- Ensure states reflect physical/logical device condition

**STEP 3: TRANSITION MODELING**
Create transitions from command specifications:
- Parse "effect_on_receipt" for exact behavioral steps
- Split conditional commands into multiple guarded transitions
- Model timer expiry as automatic transitions
- Include proper guard conditions for all branching logic
- Set response_command to null (Application Cluster specification)
- **Model event generation**: Include events in transition actions when specified
- **Use data type constraints**: Apply enum values and bitmap constraints in guards
- **Handle scene behaviors**: Model scene store/recall for scene-capable attributes
- **Include stay transitions**: Model state continuation for commands that extend/reset timers
- **Enforce feature constraints**: Block commands when features prohibit execution

**STEP 4: ADVANCED BEHAVIORAL MODELING**
Enhance FSM with detailed cluster information:
- **Data Type Integration**: Use extracted enums for state values, bitmaps for feature validation
- **Quality Flag Handling**: Model read-only vs read-write attribute behaviors
- **Constraint Validation**: Apply attribute constraints as state invariants
- **Feature Enforcement**: Add guard conditions that respect feature flags and limitations
- **Timer Decrement Logic**: Model internal timer decrements with appropriate resolution
- **Event-Driven Transitions**: Model transitions triggered by cluster events
- **Scene Capability**: Include scene store/recall behaviors for scene-capable attributes
- **Fabric Sensitivity**: Model fabric-scoped attribute access patterns

**STEP 5: TIMER SEMANTICS**
For clusters with timer attributes:
- Model timer countdown behavior with correct resolution
- Create timer expiry transitions when timer reaches zero
- Include internal timer decrement transitions (stay transitions)
- Distinguish between different timer types and their resolutions
- Include timer start/stop logic in command actions
- Model timer reset behaviors for command extensions

**STEP 6: FEATURE VALIDATION**
Apply feature constraints correctly:
- Only use features explicitly defined in cluster specification
- Model feature-dependent command availability with guard conditions
- Include feature validation that blocks prohibited commands
- Avoid inventing non-existent features
- Enforce feature limitations in transition guards

**REQUIRED FSM STRUCTURE:**
{{
  "fsm_model": {{
    "cluster_name": "[extracted from specification]",
    "cluster_id": "[hex ID from specification]", 
    "category": "[cluster category]",
    "states": [
      {{
        "name": "[state name]",
        "description": "[clear behavioral description]",
        "is_initial": true/false,
        "invariants": ["[attribute constraints in this state]"],
        "attributes_monitored": ["[relevant cluster attributes]"]
      }}
    ],
    "transitions": [
      {{
        "from_state": "[source state]",
        "to_state": "[target state]",
        "trigger": "[command name or timer/event trigger]",
        "guard_condition": "[boolean condition with data type constraints]",
        "actions": ["[attribute updates]", "[event generation if applicable]"],
        "response_command": null,
        "timing_requirements": "[timing constraints if applicable or null]"
      }}
    ],
    "initial_state": "[appropriate default state]",
    "attributes_used": ["[all referenced attributes with quality flags]"],
    "commands_handled": ["[all cluster commands]"],
    "events_generated": ["[cluster events from specification]"],
    "data_types_used": ["[enums, bitmaps, structures referenced]"],
    "scene_behaviors": ["[scene store/recall actions if applicable]"],
    "definitions": [
      {{
        "term": "[technical term, function, or concept]",
        "definition": "[clear explanation of meaning and purpose]",
        "usage_context": "[where/how it appears in FSM - states/transitions/actions]"
      }}
    ],
    "references": [
      {{
        "id": "[cluster/attr ID or null if external spec]",
        "name": "[referenced cluster/attribute/specification]",
        "description": "[why referenced - dependency/interaction/constraint]"
      }}
    ],
    "metadata": {{
      "generation_timestamp": "[ISO 8601 timestamp]",
      "generation_attempts": "[number of iterations]",
      "judge_approved": true/false,
      "source_pages": "[from cluster_info]",
      "section_number": "[from cluster_info]"
    }}
  }}
}}

**ANALYSIS METHODOLOGY:**
1. Identify cluster type: state-based, timer-driven, mode-based, measurement, etc.
2. Extract key attributes that define operational states (consider quality flags)
3. Analyze command effects for precise behavioral logic including conditional branches
4. **Integrate data types**: Use enums for state values, bitmaps for feature checks, structures for complex data
5. Map states to meaningful attribute combinations with proper constraints
6. Model conditional command branches as separate transitions with data type validation
7. Add timer-based automatic transitions with correct resolution and decrement logic
8. **Include event modeling**: Add event generation and event-driven transitions
9. **Model scene behaviors**: Include scene store/recall for scene-capable attributes
10. **Add stay transitions**: Include state continuation for timer extensions and command repetitions
11. **Enforce feature constraints**: Add guard conditions that block prohibited commands
12. **Create definitions**: Document all technical terms, functions, and domain-specific concepts
13. Validate against specification features and constraints
14. Ensure complete coverage of commands, events, and data type interactions

**DEFINITIONS REQUIREMENTS:**
Define cluster-specific terms, functions used in actions, feature flags, data type enums, attribute behaviors, and guard condition terms to reduce verbosity and improve clarity.
- **Cluster-specific terms**: Domain concepts
- **Functions/procedures**: Operations used in actions
- **Feature flags**: Feature abbreviations and their meanings
- **Data type enums**: Enum values and their behavioral implications
- **Attribute concepts**: Complex attribute behaviors
- **Guard condition terms**: Special conditions used in transitions
Definitions are optional but encouraged for clarity and to simplify actions/guards by referencing defined terms.

**REFERENCES REQUIREMENTS:**
Document external dependencies and interactions:
- **Other clusters**: Clusters referenced but not defined
- **Core specifications**: Matter Core Spec concepts
- **Shared attributes**: Global attributes
Use hex IDs when known, null for external specifications.

**CRITICAL ACCURACY REQUIREMENTS:**
- States reflect actual device behavior from specification
- Transitions implement exact command semantics with complete guard conditions
- Guard conditions capture all conditional logic including feature enforcement
- Timer behaviors model correct countdown, expiry, and internal decrement
- Features constrain commands as specified with proper blocking
- All attribute interactions are accurate and complete
- Include both state-changing and stay transitions where appropriate
- Model timer reset and extension behaviors correctly
- Use null for response_command in Application Clusters
- **Definitions are clear and helpful**: Each definition explains what the term means in the FSM context
- **Metadata is properly nested**: All generation metadata goes under "metadata" object

Focus on Matter specification accuracy over generic patterns. Generate FSM by analyzing the provided cluster specification systematically.

Return ONLY the JSON structure. No explanations, no markdown blocks, no additional text."""

# Promela Generation Configuration
PROMELA_GENERATION_PROMPT_TEMPLATE = """
You are a formal verification expert who generates Promela models for SPIN model checker from FSM specifications.

GENERATE a Promela model for this FSM that captures its behavioral semantics for formal verification:

FSM MODEL:
{fsm_model}

CLUSTER NAME: {cluster_name}

**PROMELA GENERATION STRUCTURE:**

1. **EXTRACT STATES**: Convert FSM states to mtype enumeration
2. **MODEL COMMANDS**: Create mtype for commands from FSM's commands_handled  
3. **IMPLEMENT TRANSITIONS**: Use if/fi blocks to model FSM transitions with guards
4. **ADD ATTRIBUTES**: Model key attributes as global variables
5. **CREATE PROCESSES**: Main cluster process + user simulation
6. **INCLUDE PROPERTIES**: Add LTL properties for safety/liveness verification

**REQUIRED PROMELA STRUCTURE:**

```promela
/*
 * Promela Model for Matter [CLUSTER_NAME] Cluster  
 * Cluster ID: [CLUSTER_ID]
 * For verification with SPIN model checker
 */

#define MAX_USERS 3
#define MAX_COMMANDS 5

/* State enumeration from FSM states */
mtype = {{ [state1], [state2], [state3] }};

/* Command types from FSM commands_handled */
mtype = {{ [cmd1], [cmd2], [cmd3], nop }};

/* Global cluster state and attributes */
mtype cluster_state = [initial_state];
[attribute_declarations];
chan user_commands = [MAX_COMMANDS] of {{ mtype, byte, byte }};

/* Command processing functions */
[inline_command_functions];

/* Main cluster state machine process */
active proctype ClusterStateMachine() {{
    mtype cmd;
    byte param1, param2;
    
    do
    :: user_commands?cmd, param1, param2 ->
        [command_processing_logic];
    :: [timer_logic_if_applicable];
    od
}}

/* User process for command simulation */
proctype User(byte uid) {{
    do
    :: [command_generation_logic];
    od
}}

/* LTL properties from FSM specification */
[ltl_properties];

init {{
    atomic {{
        run ClusterStateMachine();
        run User(0);
    }}
}}
```

**GENERATION INSTRUCTIONS:**
- Extract exact state names from FSM states array
- Use exact command names from FSM commands_handled array
- Model attribute constraints from FSM invariants and data types
- Include timer logic with proper decrement and expiry handling if timer attributes exist in FSM
- Create guard conditions from FSM transition guard_condition fields (including data type constraints)
- Model actions from FSM transition actions arrays (including event generation)
- **Model data types**: Include enum values and bitmap validations in logic
- **Handle events**: Model event generation and event-driven transitions
- **Include scene behaviors**: Model scene store/recall if present in FSM
- **Model feature constraints**: Include feature flag enforcement in guard conditions
- Generate LTL properties based on FSM safety/liveness properties and data constraints

**FOCUS REQUIREMENTS:**
- Model the SPECIFIC cluster behavior from the provided FSM
- Use exact state and command names from FSM specification
- Include all important state transitions and guards
- Model timer behaviors if present in FSM
- Generate meaningful LTL properties for verification
- Ensure syntactically correct Promela code

Return ONLY the Promela code with proper syntax. No explanations, no markdown blocks, just the .pml model."""

# Cluster Categories for Classification
CLUSTER_CATEGORIES = [
    "General",
    "Measurement and Sensing",
    "Lighting", 
    "HVAC",
    "Closures",
    "Media",
    "Robots", 
    "Home Appliances",
    "Energy Management",
    "Network Infrastructure"
]

# Detailed Cluster Information Extraction Configuration
CLUSTER_DETAIL_EXTRACTION_PROMPT = """
You are extracting comprehensive technical information from a Matter protocol cluster specification for formal verification and fuzzing.

**TASK**: Extract all available information from the cluster specification and return valid JSON only.

**EXTRACTION REQUIREMENTS**:

1. **Attributes** (Section X.Y.6):
   - Extract each attribute with columns: ID, Name, Type, Constraint, Quality, Default, Access, Conformance
   - Look for tables with headers like "ID | Name | Type | Constraint | Quality | Default | Access | Conformance"
   - Include attribute descriptions from surrounding text

2. **Commands** (Section X.Y.7):
   - Extract each command with columns: ID, Name, Direction, Response, Access, Conformance
   - For each command, extract field definitions from command payload tables
   - Look for command field tables with headers like "ID | Name | Type | Constraint | Default | Conformance"
   - Extract "Effect on Receipt" behavioral semantics for every command
   - Look for normative text starting with "On receipt of [CommandName]:" or "Effect on Receipt:"
   - Extract conditional logic (if/then/else), attribute assignments, state changes, timer operations
   - Include behavioral requirements and their conditions

3. **Behavioral State Transitions**:
   - Extract timer-based state changes and countdown behaviors
   - Extract attribute-driven state logic (when attributes change, what happens)
   - Look for state diagrams or state descriptions in the specification
   - Capture timing requirements and resolution specifications
   - Extract conditional behavior based on feature flags and capabilities

4. **Data Types** (Sections X.Y.4-5):
   - **Enumerations**: Extract enum values with hex codes (0x00, 0x01, etc.) and names
   - **Bitmaps**: Extract bit definitions with bit positions and names  
   - **Structures**: Extract field definitions with IDs, names, types, conformance
   - Look for definition tables and include nested structure definitions

5. **Features** (Section X.Y.3):
   - Extract features with bit positions, codes, names, descriptions
   - Include feature dependencies and conformance requirements

6. **Events** (if present):
   - Extract events with IDs, names, priorities, access, conformance
   - Extract event field definitions for each event

**EXTRACTION STRATEGY**:
   - Search the entire cluster text for information, not just the beginning
   - Tables often span multiple pages - capture all rows
   - Look for continuation markers like "Table X.Y continued"  
   - Check for embedded definitions within attribute/command descriptions
   - Extract hex values exactly as shown (0x0000, 0x01, etc.)
   - Preserve technical abbreviations and codes exactly
   - If information exists in the specification, extract it - do not leave arrays empty
   - Extract ALL features with bit positions, codes, names, descriptions
   - Include feature dependencies and conformance requirements

6. EVENTS (if present):
   - Extract ALL events with IDs, names, priorities, access, conformance
   - Extract ALL event field definitions for each event
**BEHAVIORAL EXTRACTION PATTERNS**:

Extract command behavioral semantics including:
- **Command conditionals**: "On receipt: if [condition]==TRUE, [action1] → set [attribute]:=FALSE"
- **Multi-branch logic**: "If [condition1] → [action1]; Else if [condition2] → [action2]; Else → [action3]"
- **Timer behaviors**: "When [timer]→0, server SHALL set [attribute]:=0"
- **State transitions**: "Being [state] while [timer]>0 counts down"
- **Resolution specs**: "Updates happen in [time] steps ([unit] units)"
- **Attribute lifecycle**: "SHALL be set to [value] after any command causing [condition]"

**JSON OUTPUT FORMAT**:
{{
  "cluster_info": {{
    "cluster_name": "exact cluster name",
    "cluster_id": "hex ID with 0x prefix",
    "classification": {{
      "hierarchy": "hierarchy type (Base/Utility/Application)",
      "role": "role type (Client/Server/Both)", 
      "scope": "scope type (Node/Endpoint)",
      "pics_code": "PICS code for testing"
    }},
    "revision_history": [
      {{
        "revision": "revision number",
        "description": "detailed change summary with pseudocode if applicable (max 200 chars)",
        "date": "revision date if available"
      }}
    ],
    "features": [
      {{
        "bit": "bit number (0-31)",
        "code": "feature code (2-4 chars)",
        "name": "full feature name",
        "summary": "detailed feature description with pseudocode if applicable (max 200 chars)",
        "conformance": "M/O/F/C conformance",
        "dependencies": "feature dependencies if any"
      }}
    ],
    "data_types": [
      {{
        "name": "data type name",
        "base_type": "base type (enum8/enum16/map8/map16/struct/etc.)",
        "constraint": "constraints if any",
        "values": [
          {{
            "value": "For ENUMS: hex code (0x00), For BITMAPS: bit number (0-7), For STRUCTS: field order (0,1,2...)",
            "name": "For ENUMS: enum name, For BITMAPS: bit name, For STRUCTS: field name", 
            "summary": "description of enum value/bit/field",
            "conformance": "M/O/F conformance requirement"
          }}
        ]
      }}
    ],
    "attributes": [
      {{
        "id": "hex attribute ID (0x0000)",
        "name": "full attribute name",
        "type": "data type (including custom types)",
        "constraint": "value constraints, ranges, or 'desc'",
        "quality": "quality flags (N/S/P/F/X/C)",
        "default": "default value or 'desc' if varies",
        "access": "access permissions (R/W/RW, may include F for fabric)",
        "conformance": "M/O/F conformance requirement",
        "summary": "detailed attribute purpose with pseudocode notation if applicable (max 200 chars)",
        "fabric_sensitive": "true/false if fabric-scoped",
        "scene_capable": "true/false if supports scenes"
      }}
    ],
    "commands": [
      {{
        "id": "hex command ID (0x00)",
        "name": "full command name",
        "direction": "client→server or server→client",
        "response": "response command name or 'DefaultResponse'",
        "access": "access level (A/V/M/etc.) and fabric requirements",
        "conformance": "M/O/F conformance requirement",
        "summary": "detailed command purpose with pseudocode notation (max 200 chars)",
        "timing": "timing requirements if specified",
        "fields": [
          {{
            "id": "field ID or order",
            "name": "field name",
            "type": "data type",
            "constraint": "constraints or ranges",
            "quality": "quality flags if any",
            "default": "default value if any",
            "conformance": "M/O/F for this field",
            "summary": "detailed field description with pseudocode if applicable (max 200 chars)"
          }}
        ],
        "effect_on_receipt": "Detailed algorithmic steps with pseudocode if applicable (max 400 chars): state changes, attribute updates, conditions, loops. Example: 'if [condition]==TRUE: [action1], set [attribute]:=FALSE; for each [item]: update [field]; else [action2]'"
      }}
    ],
    "events": [
      {{
        "id": "hex event ID (0x00)",
        "name": "full event name", 
        "priority": "event priority (Info/Critical/Debug)",
        "access": "access requirements",
        "conformance": "M/O/F conformance",
        "summary": "event description",
        "fields": [
          {{
            "id": "field ID",
            "name": "field name",
            "type": "data type",
            "conformance": "field conformance"
          }}
        ]
      }}
    ],
    "global_attributes": [
      {{
        "id": "global attribute ID",
        "name": "global attribute name",
        "conformance": "conformance for this cluster"
      }}
    ]
  }}
}}

EXTRACTION STRATEGY:
1. **Section Scanning**: Look for numbered subsections (X.Y.3 Features, X.Y.4 Data Types, X.Y.5 Enums, X.Y.6 Attributes, X.Y.7 Commands)
2. **Deep Subsection Analysis**: Scan X.Y.Z.1, X.Y.Z.2 subsections for detailed definitions (like "1.10.5.1 ModeTagStruct Type")
3. **Table Extraction**: Find tables with column headers and extract ALL rows completely
4. **Structure Field Tables**: Look for field definition tables within structure type subsections
5. **Enum Value Lists**: Extract complete enum value tables with hex codes and names
6. **Command Field Definitions**: Find command payload field tables within command subsections
7. **Status Code Tables**: Extract status code definitions and ranges
8. **Mode/Tag Namespaces**: Look for value namespace tables with semantic meanings
9. **Multi-page Continuations**: Handle tables that span multiple pages or sections
10. **Constraint Details**: Capture detailed constraint specifications (max values, ranges, dependencies)

CRITICAL INSTRUCTIONS:
1. **NEVER RETURN EMPTY ARRAYS IF DATA EXISTS**: Every enum, bitmap, struct, and command with defined values/fields MUST have populated arrays
**VALIDATION REQUIREMENTS**:
- Extract all rows from tables in the specification
- Extract all enum values with hex codes, names, and descriptions
- Extract all structure field definitions with IDs, names, types, conformance
- Extract all command field definitions from command payload tables
- Extract complete "effect_on_receipt" behavioral text for commands
- Return valid JSON only - no markdown blocks, no explanations
- Ensure all JSON strings are properly escaped
- Use character limits: summaries max 200 chars, descriptions max 200 chars, effect_on_receipt max 400 chars
- Close all braces properly - never truncate JSON structure

Extract from the provided cluster specification text and return complete valid JSON only.
"""

# Section-Based Extraction Prompts
# Following the same unbiased structure as CLUSTER_DETAIL_EXTRACTION_PROMPT

REVISION_HISTORY_EXTRACTION_PROMPT = """
You are extracting revision history information from a Matter protocol cluster specification section.

**TASK**: Extract ONLY revision history entries from the provided text and return valid JSON object.

**EXTRACTION REQUIREMENTS**:
- Look for revision tables with "Revision" and "Description" columns
- Extract revision numbers (1, 2, 3, etc.)
- Extract brief change descriptions with pseudocode notation if applicable
- Extract dates if available (often not present)
- Look for text like "The global ClusterRevision attribute value SHALL be the highest revision number"
- **References**: Extract items MENTIONED but NOT defined in this section

**JSON OUTPUT FORMAT**:
{
  "revisions": [
    {
      "revision": "1",
      "description": "detailed summary with pseudocode if applicable (max 200 chars)",
      "date": "date if available or null"
    }
  ],
  "references": [
    {
      "id": "0xFFFC",
      "name": "ClusterRevision",
      "description": "Global attr for cluster version (not defined here)"
    }
  ]
}

**REFERENCES RULES**:
- Include ONLY items MENTIONED in text but NOT fully defined in this section
- Use attribute/cluster ID if known, null if external specification
- Keep descriptions detailed with pseudocode if applicable (max 200 chars)
- Examples: ClusterRevision attribute, other clusters mentioned

**EXTRACTION STRATEGY**:
- Search for numbered revision entries in tables or lists
- Scan for references to attributes/clusters not defined in this section
- Keep descriptions concise, add pseudocode for behavioral changes if applicable
- Use null for missing dates

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

FEATURES_EXTRACTION_PROMPT = """
You are extracting feature information from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster features from the provided text and return valid JSON object.

**EXTRACTION REQUIREMENTS**:
- Look for feature tables with columns like "Bit", "Code", "Feature", "Summary", "Conformance"
- Extract bit positions (0-31 for feature flags)
- Extract feature codes (2-4 character abbreviations like "GN", "OO")
- Extract full feature names and descriptions with pseudocode notation
- Extract conformance requirements (M/O/F/C)
- Look for feature dependencies if any
- **References**: Extract items MENTIONED but NOT defined in this section

**JSON OUTPUT FORMAT**:
{
  "features": [
    {
      "bit": "bit number (0-31)",
      "code": "feature code (2-4 chars)",
      "name": "full feature name",
      "summary": "detailed description with pseudocode if applicable (max 200 chars)",
      "conformance": "M/O/F/C conformance",
      "dependencies": "feature dependencies if any or null"
    }
  ],
  "references": [
    {
      "id": "0xFFFD",
      "name": "FeatureMap",
      "description": "Feature bitmap attr (not defined here)"
    },
    {
      "id": "0x0006",
      "name": "On/Off Cluster",
      "description": "Dependency cluster (if mentioned)"
    }
  ]
}

**REFERENCES RULES**:
- Include ONLY items MENTIONED in text but NOT fully defined in this section
- Use attribute/cluster ID if known, null if external spec
- Keep descriptions detailed with pseudocode if applicable (max 200 chars)
- Examples: FeatureMap attribute, dependent clusters mentioned, related specs

**EXTRACTION STRATEGY**:
- Look for sections titled "Features" or numbered like "X.Y.3 Features"
- Scan for references to clusters/attributes not defined here
- Add pseudocode notation for feature behavior in summaries

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

DATA_TYPES_EXTRACTION_PROMPT = """
You are extracting data type definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY custom data types (enums, bitmaps, structures) from the provided text and return valid JSON object.

**EXTRACTION REQUIREMENTS**:
- **Enumerations**: Extract enum types with value tables (0x00, 0x01, etc.)
- **Bitmaps**: Extract bitmap types with bit definitions (bit 0, bit 1, etc.)
- **Structures**: Extract structure types with field definitions
- Look for sections like "X.Y.4 Data Types" or "X.Y.5 [TypeName] Type"
- Extract type names, base types, and all value/field definitions with pseudocode notation
- **References**: Extract items MENTIONED but NOT defined in this section

**JSON OUTPUT FORMAT**:
{
  "data_types": [
    {
      "name": "data type name (e.g., IdentifyTypeEnum)",
      "base_type": "base type (enum8/enum16/map8/map16/struct/etc.)",
      "constraint": "constraints if any or null",
      "values": [
        {
          "value": "For ENUMS: hex (0x00), For BITMAPS: bit (0-7), For STRUCTS: order",
          "name": "For ENUMS: enum name, For BITMAPS: bit name, For STRUCTS: field name", 
          "summary": "description with pseudocode if applicable (max 200 chars)",
          "conformance": "M/O/F conformance requirement"
        }
      ]
    }
  ],
  "references": [
    {
      "id": null,
      "name": "Data Model Spec",
      "description": "Base types (external spec)"
    }
  ]
}

**REFERENCES RULES**:
- Include ONLY items MENTIONED in text but NOT fully defined in this section
- Use null for external specs, cluster/attr ID if known
- Keep descriptions detailed with pseudocode if applicable (max 200 chars)
- Examples: Data Model Specification, other clusters using these types

**EXTRACTION STRATEGY**:
- Find all enum, bitmap, and struct type definitions
- Scan for references to external specs or other clusters
- Add pseudocode notation in summaries if applicable
- Include ALL types found in the specification text

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

ATTRIBUTES_EXTRACTION_PROMPT = """
You are extracting attribute definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster attributes from the provided text and return valid JSON object.

**EXTRACTION REQUIREMENTS**:
- Look for attribute tables with columns like "ID | Name | Type | Constraint | Quality | Default | Access | Conformance"
- Extract hex attribute IDs (0x0000, 0x0001, etc.)
- Extract attribute names, types, constraints, quality flags
- Extract default values and access permissions
- Look for individual attribute descriptions in subsections
- Extract fabric sensitivity and scene capability information
- Include pseudocode notation for behavioral attributes
- **References**: Extract items MENTIONED but NOT defined in this section

**JSON OUTPUT FORMAT**:
{
  "attributes": [
    {
      "id": "hex attribute ID (0x0000)",
      "name": "full attribute name",
      "type": "data type (including custom types)",
      "constraint": "value constraints, ranges, or 'desc'",
      "quality": "quality flags (N/S/P/F/X/C)",
      "default": "default value or 'desc' if varies",
      "access": "access permissions (R/W/RW, may include F for fabric)",
      "conformance": "M/O/F conformance requirement",
      "summary": "detailed purpose with pseudocode if applicable (max 250 chars)",
      "fabric_sensitive": true/false,
      "scene_capable": true/false
    }
  ],
  "references": [
    {
      "id": "0x0005",
      "name": "Scenes Cluster",
      "description": "Scene storage for scene attrs (if mentioned)"
    },
    {
      "id": "0xF004",
      "name": "Binding Cluster",
      "description": "Attr bindings (if mentioned)"
    }
  ]
}

**REFERENCES RULES**:
- Include ONLY items MENTIONED in text but NOT fully defined in this section
- Use cluster/attr ID if known, null if external spec
- Keep descriptions detailed with pseudocode if applicable (max 200 chars)
- Examples: Scenes Cluster (for scene-capable attrs), Binding Cluster, other clusters

**EXTRACTION STRATEGY**:
- Find attribute definition tables and extract ALL rows
- Scan for references to other clusters/specs not defined here
- Add pseudocode notation for behavioral attributes if applicable
- Use exact hex IDs and preserve technical specifications

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

COMMANDS_EXTRACTION_PROMPT = """
You are extracting command definitions with behavioral logic from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster commands from the provided text and return valid JSON object with pseudocode.

**EXTRACTION REQUIREMENTS**:
- Look for command tables with columns like "ID | Name | Direction | Response | Access | Conformance"
- Extract hex command IDs (0x00, 0x01, etc.)
- Extract command names, directions, response types
- Extract command field definitions from payload tables with pseudocode notation
- **CRITICAL**: Extract "Effect on Receipt" behavioral logic for PSEUDOCODE generation
- **References**: Extract items MENTIONED but NOT defined in this section

**BEHAVIORAL EXTRACTION FOR PSEUDOCODE**:
Convert "Effect on Receipt" behavioral text into algorithmic pseudocode:
- **Conditionals**: "if [condition] then [action] else [action]"
- **Assignments**: "set [attribute] := [value]"
- **Procedures**: "call [function]([params])"
- **State changes**: "[object].state := [new_state]"
- **Timers**: "start_timer([duration])" or "stop_timer()"

**JSON OUTPUT FORMAT**:
{
  "commands": [
    {
      "id": "hex command ID (0x00)",
      "name": "full command name",
      "direction": "client ⇒ server or client ⇐ server",
      "response": "response command name or 'Y'/'N'",
      "access": "access level and fabric requirements",
      "conformance": "M/O/F conformance requirement",
      "summary": "detailed purpose with pseudocode if applicable (max 250 chars)",
      "timing": "timing requirements if specified or null",
      "fields": [
        {
          "id": "field ID or order",
          "name": "field name",
          "type": "data type",
          "constraint": "constraints or ranges",
          "quality": "quality flags if any",
          "default": "default value if any",
          "conformance": "M/O/F for this field",
          "summary": "detailed field description with pseudocode if applicable (max 200 chars)"
        }
      ],
      "effect_on_receipt": "Detailed algorithmic steps with pseudocode if applicable (max 500 chars)"
    }
  ],
  "references": [
    {
      "id": null,
      "name": "Interaction Model",
      "description": "Command invocation (Core Spec)"
    },
    {
      "id": "0x001F",
      "name": "Access Control Cluster",
      "description": "ACL enforcement (if mentioned)"
    }
  ]
}

**REFERENCES RULES**:
- Include ONLY items MENTIONED in text but NOT fully defined in this section
- Use cluster ID if known, null if Core/external spec
- Keep descriptions detailed with pseudocode if applicable (max 200 chars)
- Examples: Interaction Model (Core), Access Control Cluster, other clusters interacted with

**EXTRACTION STRATEGY**:
- Find command definition tables and extract ALL commands
- Scan for references to other clusters/specs not defined here
- Extract complete "Effect on Receipt" behavioral text
- Convert behavioral logic to concise pseudocode format if applicable
- Add pseudocode notation to summaries and field descriptions if applicable

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

EVENTS_EXTRACTION_PROMPT = """
You are extracting event definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster events from the provided text and return valid JSON object.

**EXTRACTION REQUIREMENTS**:
- Look for event tables with columns like "ID | Name | Priority | Access | Conformance"
- Extract hex event IDs (0x00, 0x01, etc.)
- Extract event names, priority levels, access requirements
- Extract event field definitions from payload tables with pseudocode notation
- Look for sections like "X.Y.8 Events"
- Extract event generation conditions and triggers
- **References**: Extract items MENTIONED but NOT defined in this section

**JSON OUTPUT FORMAT**:
{
  "events": [
    {
      "id": "hex event ID (0x00)",
      "name": "full event name", 
      "priority": "event priority (Info/Critical/Debug)",
      "access": "access requirements",
      "conformance": "M/O/F conformance",
      "summary": "detailed event description with pseudocode if applicable (max 250 chars)",
      "fields": [
        {
          "id": "field ID",
          "name": "field name",
          "type": "data type",
          "conformance": "field conformance",
          "summary": "detailed field description with pseudocode if applicable (max 200 chars)"
        }
      ]
    }
  ],
  "references": [
    {
      "id": null,
      "name": "Event Model",
      "description": "Event generation (Core Spec)"
    },
    {
      "id": null,
      "name": "Interaction Model",
      "description": "Event subscription (Core Spec)"
    }
  ]
}

**REFERENCES RULES**:
- Include ONLY items MENTIONED in text but NOT fully defined in this section
- Use null for Core/external specs, cluster ID if other cluster
- Keep descriptions detailed with pseudocode if applicable (max 200 chars)
- Examples: Event Model (Core), subscription handling, other clusters emitting events

**EXTRACTION STRATEGY**:
- Find event definition tables and sections
- Scan for references to Core specs or other clusters
- Extract event field definitions completely
- Look for event generation conditions and add pseudocode notation if applicable
- Add pseudocode notation to summaries and field descriptions if applicable

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

CLUSTER_OVERVIEW_EXTRACTION_PROMPT = """
You are extracting cluster overview information (ID and classification) from a Matter protocol specification section.

**TASK**: Extract cluster ID and classification information from the provided text and return valid JSON object.

**EXTRACTION REQUIREMENTS**:
- **Cluster IDs**: Look for cluster ID tables with columns like "ID | Name". Extract hex cluster IDs (0x0000, 0x0001, etc.) and full cluster names. Include brief summary for each. Some clusters have multiple IDs - extract ALL of them as array.
- **Classification**: Look for classification table with Hierarchy, Role, Scope, PICS Code
- Extract hierarchy (e.g., Base, Functional, Utility)
- Extract role (e.g., Application, Aggregator, Utility)
- Extract scope (e.g., Endpoint, Node, Fabric)
- Extract PICS code (e.g., OO, OT, LV)
- Include brief summary with pseudocode notation if applicable
- **References**: Extract OTHER clusters/attributes/concepts that are MENTIONED but NOT fully defined in this section

**JSON OUTPUT FORMAT**:
{
  "cluster_ids": [
    {
      "id": "hex cluster ID (0x0006)",
      "name": "full cluster name",
      "summary": "detailed cluster purpose with pseudocode if applicable (max 200 chars)"
    }
  ],
  "classifications": [
    {
      "hierarchy": "Base/Functional/Utility/etc.",
      "role": "Application/Aggregator/Utility/etc.",
      "scope": "Endpoint/Node/Fabric/etc.",
      "pics_code": "PICS short code",
      "summary": "detailed classification purpose with pseudocode if applicable (max 200 chars)"
    }
  ],
  "references": [
    {
      "id": "0xFFFD",
      "name": "FeatureMap",
      "description": "Feature bitmap (not defined here)"
    },
    {
      "id": "0xFFFC",
      "name": "ClusterRevision",
      "description": "Cluster version (not defined here)"
    }
  ]
}

**REFERENCES RULES**:
- Include ONLY items MENTIONED in text but NOT fully defined in this section
- Use cluster ID if known (e.g., "0x0005" for Scenes), null if external spec (e.g., Core Spec)
- Keep descriptions detailed with pseudocode if applicable (max 200 chars)
- Examples: FeatureMap attribute, other clusters referenced, external specifications

**EXTRACTION STRATEGY**:
- Find cluster ID tables and extract ALL entries as array (some clusters have multiple IDs)
- Find classification table and extract ALL fields as array (some sections may have multiple classifications)
- Scan text for references to other clusters/attributes/specs not defined here
- Add pseudocode notation in summaries where behavioral logic applies if applicable
- If no cluster IDs found, return empty array [] for cluster_ids
- If no classification found, return empty array [] for classifications

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

DERIVED_CLUSTER_NAMESPACE_EXTRACTION_PROMPT = """
You are extracting derived cluster namespace definitions from a Matter protocol specification section.

**TASK**: Extract ONLY derived cluster namespace definitions (status codes and mode tags) and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for tables like "Status Code Value Name" and "Mode Tag Value Name"
- Extract hex values (0x41, 0x4000, etc.)
- Extract value names (e.g., Stuck, Cleaning, Mapping)
- Extract descriptions if subsections provide them
- Separate entries into categories: "status_code" or "mode_tag"

**JSON OUTPUT FORMAT**:
[
  {
    "category": "status_code",
    "id": "hex code (0x41)",
    "name": "status code name",
    "summary": "detailed purpose with pseudocode if applicable (max 200 chars)"
  },
  {
    "category": "mode_tag",
    "id": "hex code (0x4001)",
    "name": "mode tag name",
    "summary": "detailed purpose with pseudocode if applicable (max 200 chars)"
  }
]

**EXTRACTION STRATEGY**:
- Parse ALL rows in status code and mode tag tables
- Attach descriptive subsections (e.g., Idle Tag, Cleaning Tag, Mapping Tag) to the correct mode tag entries
- Preserve exact hex IDs and names
- If no derived namespace definitions are found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

DEPENDENCIES_EXTRACTION_PROMPT = """
You are extracting dependency definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster dependencies (inter-cluster relationships, conditional behaviors, coupling rules) and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Each dependency links two or more clusters, attributes, or commands
- Capture trigger conditions (e.g., bit values, attribute settings)
- Capture dependent behavior (what changes, what remains unaffected)
- Convert narrative logic into concise pseudocode for clarity

**JSON OUTPUT FORMAT**:
[
  {
    "id": "dependency section number (e.g., 3.2.5.1)",
    "title": "short dependency title (e.g., Coupling color temperature to Level Control)",
    "clusters_involved": ["ClusterA (0x0008)", "ClusterB (0x0300)"],
    "trigger_condition": "condition under which dependency applies",
    "effect": "description of resulting behavior (max 200 chars)",
    "summary": "detailed explanation with pseudocode if applicable (max 200 chars)"
  }
]

**EXTRACTION STRATEGY**:
- Parse numbered dependency subsections
- Identify involved clusters and attributes
- Extract both trigger conditions and resulting effects
- Add pseudocode notation if applicable for clear logic
- Be tolerant of format variations (bullets, prose, inline text)
- If no dependencies are found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

MODE_EXAMPLES_EXTRACTION_PROMPT = """
You are extracting mode examples from a Matter protocol cluster specification section.

**TASK**: Extract ONLY mode examples with their associated mode tags and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Each example links a mode name to one or more mode tags
- Extract hex tag values (0x4000, 0x4001, etc.)
- Extract tag names if provided
- Mode names must be preserved exactly as written
- Some examples may include multiple tags

**JSON OUTPUT FORMAT**:
[
  {
    "mode": "mode name (e.g., No Energy Management)",
    "tags": [
      {
        "id": "hex tag value (0x4000)",
        "name": "tag name (e.g., NoOptimization)"
      }
    ],
    "summary": "detailed description of the example with pseudocode if applicable (max 200 chars)"
  }
]

**EXTRACTION STRATEGY**:
- Look for bullet lists or prose describing mode examples
- Parse ALL example rows, even if multiple tags are listed
- Preserve exact mode names and tag names
- Be tolerant of different structures (inline text, tables, bullets)
- If no mode examples found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

STATUS_CODES_EXTRACTION_PROMPT = """
You are extracting status code definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY status codes and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for status code tables with columns like "Value | Name | Summary | Conformance"
- Extract hex values (0x02, 0x03, etc.)
- Extract status code names (FailureDueToFault, DUPLICATE, OCCUPIED, etc.)
- Extract summaries (may appear inline in table or in dedicated subsections)
- Extract conformance (M/O/F) if specified
- Ensure summaries are concise but preserve meaning

**JSON OUTPUT FORMAT**:
[
  {
    "id": "hex status code value (0x02)",
    "name": "status code name",
    "summary": "detailed status meaning with pseudocode if applicable (max 200 chars)",
    "conformance": "M/O/F or null"
  }
]

**EXTRACTION STRATEGY**:
- Parse ALL status code values from tables
- Attach additional descriptions from subsections to the correct status code entry
- Preserve exact hex values and names
- Be tolerant of structural differences (tables, prose, split summaries)
- If no status codes found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

DEFINITIONS_EXTRACTION_PROMPT = """
You are extracting cluster definitions from a Matter protocol specification section.

**TASK**: Extract ONLY definition entries (terms with explanations) and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for numbered subsections like "9.2.6.1. Power"
- Extract the term name (e.g., Power, Energy)
- Extract the core definition text
- Extract measurement units if specified (e.g., mW, mWh)
- Capture sign conventions if given (positive/negative meaning)
- Extract example cases (Solar PV inverter, EVSE, BESS, etc.) if present

**JSON OUTPUT FORMAT**:
[
  {
    "term": "term name (e.g., Power)",
    "definition": "main definition text",
    "units": "measurement units or null",
    "sign_convention": "positive/negative meaning or null",
    "examples": [
      "example description 1",
      "example description 2"
    ]
  }
]

**EXTRACTION STRATEGY**:
- Parse all subsections under "Definitions"
- Consolidate paragraphs into a single clean definition
- Collect all examples into a list
- Preserve technical details like units and sign meaning
- Be tolerant of different structures (inline text, prose, tables)
- If no definitions found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

CONVERSIONS_EXTRACTION_PROMPT = """
You are extracting conversion rules from a Matter protocol specification section.

**TASK**: Extract ONLY conversion definitions (e.g., unit conversions, scaling formulas) and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Each entry should specify what is being converted (e.g., Temperature)
- Capture source and target units (e.g., Fahrenheit ⇔ Celsius)
- Include formula or reference if available
- Capture notes such as "see Data Model" or "referenced elsewhere"

**JSON OUTPUT FORMAT**:
[
  {
    "conversion_for": "what is being converted (e.g., Temperature)",
    "source_units": "original units (e.g., Fahrenheit)",
    "target_units": "converted units (e.g., Celsius)",
    "formula": "formula or reference (e.g., see Data Model section)",
    "notes": "additional notes if present"
  }
]

**EXTRACTION STRATEGY**:
- Look for explicit conversion references (temperature, energy, duration, etc.)
- Extract unit names and relationships
- If formula is not given, include reference text (e.g., 'see Data Model')
- Be tolerant of different formats (tables, prose, references)
- If no conversions found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

MULTI_POSITION_DETAILS_EXTRACTION_PROMPT = """
You are extracting multi-position switch behavior rules from a Matter protocol specification section.

**TASK**: Extract ONLY multi-position details (event-to-field mappings and behavioral rules) and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture which events are affected (e.g., SwitchLatched, InitialPress, LongPress, MultiPressOngoing, ShortRelease, LongRelease, MultiPressComplete)
- Capture which field must be set (e.g., NewPosition, PreviousPosition)
- Capture how the field value is determined (e.g., corresponds to new position, corresponds to previous position)
- Translate the behavior into short pseudocode

**JSON OUTPUT FORMAT**:
[
  {
    "event": "event name (e.g., SwitchLatched)",
    "field": "field name (e.g., NewPosition)",
    "value_rule": "how value is determined (max 200 chars)",
    "pseudocode": "pseudocode representation if applicable"
  }
]

**EXTRACTION STRATEGY**:
- Parse narrative text describing multi-position event rules
- Group events by which field they set
- Preserve exact event and field names
- Translate descriptions into pseudocode if applicable
- If no multi-position details found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

MULTIPRESS_SEQUENCE_EXTRACTION_PROMPT = """
You are extracting multi-press sequence behavior rules from a Matter protocol specification section.

**TASK**: Extract ONLY multi-press event sequence definitions and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture feature flags involved (MSM, MSL, MSR, AS)
- Capture conditions (e.g., first press long, AS set/unset, N > MultiPressMax)
- Capture event sequences that SHALL be generated (InitialPress, ShortRelease, MultiPressOngoing, MultiPressComplete, LongPress, LongRelease)
- Capture event suppression rules (events that SHALL NOT be generated)
- Represent event order as pseudocode sequence or ordered list

**JSON OUTPUT FORMAT**:
[
  {
    "scenario": "short scenario name (e.g., Double Press with AS unset)",
    "feature_flags": ["MSM", "MSR"],
    "condition": "trigger condition for this sequence",
    "events_generated": ["InitialPress", "ShortRelease", "MultiPressOngoing(2)", "MultiPressComplete(2)"],
    "events_suppressed": ["LongPress", "LongRelease"],
    "pseudocode": "pseudocode representation if applicable"
  }
]

**EXTRACTION STRATEGY**:
- Parse subsections and bullet cases (single press, double press, triple press, long press, aborted sequence, etc.)
- Group scenarios by feature flag context (AS set vs unset)
- List all events generated in sequence order
- List explicitly forbidden/suppressed events
- Translate behavior into pseudocode if applicable
- If no multi-press sequence rules found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

MS_FEATURE_FLAG_SUMMARY_EXTRACTION_PROMPT = """
You are extracting MS feature flag case summaries from a Matter protocol specification section.

**TASK**: Extract ONLY summarized case rules for MS feature flag and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture feature flag combinations (e.g., MS & !MSR & !MSM)
- Capture resulting event outcomes (which events are generated at end of action cycle)
- Capture any notes about AS feature flag behavior (e.g., backward compatibility, reduced events)
- Represent rule as pseudocode when possible

**JSON OUTPUT FORMAT**:
[
  {
    "case": "MS & !MSR & !MSM",
    "feature_flags": ["MS", "!MSR", "!MSM"],
    "outcome": "Every action cycle is only a single InitialPress event",
    "notes": null,
    "pseudocode": "pseudocode representation if applicable"
  },
  {
    "case": "MS & MSM",
    "feature_flags": ["MS", "MSM"],
    "outcome": "Ends on LongRelease (if MSL & first press long) or MultiPressComplete",
    "notes": "AS does not change outcome; AS reduces events",
    "pseudocode": "pseudocode representation if applicable"
  }
]

**EXTRACTION STRATEGY**:
- Parse bullet lists describing MS feature flag combinations
- Map feature flag logic to concise outcomes
- Add pseudocode representation of event emission rules
- Include AS-related explanatory notes
- If no MS feature flag cases found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

PIN_RFID_CODE_FORMAT_EXTRACTION_PROMPT = """
You are extracting PIN/RFID code format rules from a Matter protocol specification section.

**TASK**: Extract ONLY PIN/RFID code format definitions and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture data type (e.g., octet string)
- Capture encoding requirements (e.g., ASCII)
- Capture allowed value types (numbers, characters)
- Include representation examples (e.g., '1234' → 0x31 0x32 0x33 0x34)

**JSON OUTPUT FORMAT**:
[
  {
    "type": "OctetString",
    "encoding": "ASCII",
    "allowed_values": "numbers and characters",
    "example": {
      "input": "1234",
      "encoded": ["0x31", "0x32", "0x33", "0x34"]
    },
    "notes": "All PIN/RFID codes SHALL be ASCII encoded regardless of being numbers or characters"
  }
]

**EXTRACTION STRATEGY**:
- Parse narrative text describing PIN/RFID code format
- Normalize into structured fields: type, encoding, allowed values, example
- Preserve exact encoding rules and examples
- Be tolerant of prose vs table style
- If no PIN/RFID code format found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

STATE_CHANGE_TABLE_LIGHTING_EXTRACTION_PROMPT = """
You are extracting state change examples for Lighting feature from a Matter protocol specification section.

**TASK**: Extract ONLY state change rules and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture initial conditions: CurrentLevel, EiO, OnOff, PhysicalDevice state
- Capture command applied (including parameters, duration, rate, etc.)
- Capture resulting state: CurrentLevel, OnOff, PhysicalDevice, Output level
- Capture description of effect (e.g., "Stays off", "Turns on and adjusts to half", "Output level adjusts to minimum")
- Normalize "any" into explicit 'any' value

**JSON OUTPUT FORMAT**:
[
  {
    "initial": {
      "current_level": "value or 'any'",
      "EiO": 0,
      "onoff": false,
      "physical_device": "Off"
    },
    "command": "MoveToLevel(l=MID, t=2s)",
    "result": {
      "current_level": "same",
      "onoff": false,
      "physical_device": "Off",
      "output": "Stays off"
    },
    "summary": "brief description of the state change with pseudocode if applicable"
  },
  {
    "initial": {
      "current_level": "any",
      "EiO": 0,
      "onoff": false,
      "physical_device": "Off"
    },
    "command": "MoveToLevelWithOnOff(l=MID, t=2s)",
    "result": {
      "current_level": "MID",
      "onoff": true,
      "physical_device": "On",
      "output": "Turns on at midpoint brightness"
    },
    "summary": "brief description of the state change with pseudocode if applicable"
  }
]

**EXTRACTION STRATEGY**:
- Parse ALL table rows of state change examples
- Map "Before/After" state into structured `initial` and `result`
- Normalize boolean OnOff values into true/false
- Preserve command parameters exactly as written
- Add concise summary per rule
- Be tolerant of formatting differences (line breaks, split words, multi-page tables)
- If no state change rules found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

SEQUENCE_OF_GENERATED_EVENTS_EXTRACTION_PROMPT = """
You are extracting event generation sequences from a Matter protocol specification section.

**TASK**: Extract ONLY event generation sequences and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture switch type (feature flag combinations)
- Capture interaction type (short press, long press, very long press, any press)
- Capture ordered list of events generated
- Capture events explicitly not generated (if mentioned)
- Translate sequence into short pseudocode

**JSON OUTPUT FORMAT**:
[
  {
    "switch_type": "MS + MSL",
    "interaction": "short press",
    "events_generated": ["InitialPress", "ShortRelease (if MSR & !AS)", "MultiPressComplete(1) (if MSM)"],
    "events_suppressed": [],
    "pseudocode": "emit InitialPress; if MSR & !AS then emit ShortRelease; if MSM then emit MultiPressComplete(1)"
  },
  {
    "switch_type": "MS + MSL",
    "interaction": "long/very long press",
    "events_generated": ["InitialPress", "LongPress", "LongRelease"],
    "events_suppressed": ["MultiPressComplete(1)"],
    "pseudocode": "emit InitialPress; emit LongPress; on release emit LongRelease"
  },
  {
    "switch_type": "MS + !MSL",
    "interaction": "any press length",
    "events_generated": ["InitialPress", "ShortRelease (if MSR & !AS)", "MultiPressComplete(1) (if MSM)"],
    "events_suppressed": ["LongPress", "LongRelease"],
    "pseudocode": "emit InitialPress; if MSR & !AS then emit ShortRelease; if MSM then emit MultiPressComplete(1)"
  },
  {
    "switch_type": "MS only (no MSR, MSL, MSM, AS)",
    "interaction": "any press length",
    "events_generated": ["InitialPress"],
    "events_suppressed": ["ShortRelease", "LongPress", "LongRelease"],
    "pseudocode": "emit InitialPress only"
  }
]

**EXTRACTION STRATEGY**:
- Parse subsections describing switches with/without MSL/MSR/MSM/AS
- For each interaction type, list generated events in order
- Capture events explicitly not generated as suppressed
- Translate sequence into pseudocode using if applicable notation
- If no event sequences found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

DIMMING_LIGHT_CURVE_EXTRACTION_PROMPT = """
You are extracting dimming light curve definitions from a Matter protocol specification section.

**TASK**: Extract ONLY dimming light curve details and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture the mathematical formula(s)
- Capture input/output variables and ranges (MinLevel, MaxLevel, CurrentLevel, Level, %Light)
- Capture special notes/exceptions (e.g., Value 255 not used)
- Extract example rows from tables into structured JSON
- Include relationship to attributes (e.g., IntrinsicBallastFactor, BallastFactorAdjustment)

**JSON OUTPUT FORMAT**:
{
  "formula": "Level = (MaxLevel – MinLevel) * CurrentLevel / 253 + (254 * MinLevel – MaxLevel) / 253",
  "variables": {
    "CurrentLevel": "1..254",
    "MinLevel": "configured minimum level",
    "MaxLevel": "configured maximum level",
    "Level": "derived 8-bit value",
    "%Light": "percent light output of ballast"
  },
  "notes": [
    "Value 255 is not used",
    "Output also depends on IntrinsicBallastFactor and BallastFactorAdjustment"
  ],
  "examples": [
    { "MinLevel": 1, "MaxLevel": 254, "CurrentLevel": 1, "Level": 1, "PercentLight": "0.10%" },
    { "MinLevel": 1, "MaxLevel": 254, "CurrentLevel": 10, "Level": 10, "PercentLight": "0.13%" },
    { "MinLevel": 1, "MaxLevel": 254, "CurrentLevel": 100, "Level": 100, "PercentLight": "1.49%" },
    { "MinLevel": 1, "MaxLevel": 254, "CurrentLevel": 254, "Level": 254, "PercentLight": "100%" },
    { "MinLevel": 170, "MaxLevel": 254, "CurrentLevel": 1, "Level": 170, "PercentLight": "10.1%" },
    { "MinLevel": 170, "MaxLevel": 254, "CurrentLevel": 10, "Level": 173, "PercentLight": "11.0%" },
    { "MinLevel": 170, "MaxLevel": 254, "CurrentLevel": 100, "Level": 203, "PercentLight": "24.8%" },
    { "MinLevel": 170, "MaxLevel": 254, "CurrentLevel": 254, "Level": 254, "PercentLight": "100%" },
    { "MinLevel": 170, "MaxLevel": 230, "CurrentLevel": 1, "Level": 170, "PercentLight": "10.1%" },
    { "MinLevel": 170, "MaxLevel": 230, "CurrentLevel": 10, "Level": 172, "PercentLight": "10.7%" },
    { "MinLevel": 170, "MaxLevel": 230, "CurrentLevel": 100, "Level": 193, "PercentLight": "19.2%" },
    { "MinLevel": 170, "MaxLevel": 230, "CurrentLevel": 254, "Level": 230, "PercentLight": "51.9%" }
  ]
}

**EXTRACTION STRATEGY**:
- Extract formula text exactly as given
- Map variables to definitions and ranges
- Parse ALL example rows into structured JSON
- Preserve notes and caveats
- If no dimming curve details found, return empty object {}

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

MODE_USE_EXTRACTION_PROMPT = """
You are extracting mode usage rules from a Matter protocol specification section.

**TASK**: Extract ONLY mode use definitions (rules about transitions between modes and their meaning) and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture starting mode tag and target mode tag
- Capture meaning of the transition (e.g., start cleaning cycle, stop cleaning cycle)
- Indicate if multiple modes per tag are allowed
- Translate into short pseudocode

**JSON OUTPUT FORMAT**:
[
  {
    "from_mode_tag": "Idle",
    "to_mode_tag": "Cleaning",
    "action": "start cleaning cycle",
    "pseudocode": "pseudocode representation if applicable"
  },
  {
    "from_mode_tag": "Cleaning",
    "to_mode_tag": "Idle",
    "action": "stop cleaning cycle",
    "pseudocode": "if mode changes Cleaning→Idle then stop_cleaning()"
  },
  {
    "from_mode_tag": "Idle",
    "to_mode_tag": "Mapping",
    "action": "start mapping cycle",
    "pseudocode": "if mode changes Idle→Mapping then start_mapping()"
  },
  {
    "from_mode_tag": "Mapping",
    "to_mode_tag": "Idle",
    "action": "stop mapping cycle",
    "pseudocode": "if mode changes Mapping→Idle then stop_mapping()"
  }
]

**EXTRACTION STRATEGY**:
- Parse narrative text and bullet lists describing mode transitions
- Normalize each transition into from → to mapping
- Translate behavioral rule into pseudocode form
- Capture optional allowance of multiple modes with same tag
- If no mode use rules found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

SETPOINT_LIMITS_EXTRACTION_PROMPT = """
You are extracting setpoint limit rules from a Matter protocol specification section.

**TASK**: Extract ONLY setpoint constraints and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture each constraint equation exactly
- Group constraints by category:
  • Device/user limit constraints
  • Setpoint-to-limit constraints
  • Auto feature (deadband) constraints
- Extract involved attributes (e.g., MinHeatSetpointLimit, AbsMaxCoolSetpointLimit)
- Provide short pseudocode for enforcement

**JSON OUTPUT FORMAT**:
[
  {
    "category": "device_limit",
    "constraint": "AbsMinHeatSetpointLimit <= MinHeatSetpointLimit <= MaxHeatSetpointLimit <= AbsMaxHeatSetpointLimit",
    "attributes_involved": ["AbsMinHeatSetpointLimit", "MinHeatSetpointLimit", "MaxHeatSetpointLimit", "AbsMaxHeatSetpointLimit"],
    "pseudocode": "pseudocode representation if applicable"
  },
  {
    "category": "setpoint_limit",
    "constraint": "MinHeatSetpointLimit <= OccupiedHeatingSetpoint <= MaxHeatSetpointLimit",
    "attributes_involved": ["MinHeatSetpointLimit", "OccupiedHeatingSetpoint", "MaxHeatSetpointLimit"],
    "pseudocode": "assert MinHeatSetpointLimit <= OccupiedHeatingSetpoint <= MaxHeatSetpointLimit"
  },
  {
    "category": "auto_deadband",
    "constraint": "OccupiedHeatingSetpoint <= (OccupiedCoolingSetpoint - MinSetpointDeadBand)",
    "attributes_involved": ["OccupiedHeatingSetpoint", "OccupiedCoolingSetpoint", "MinSetpointDeadBand"],
    "pseudocode": "assert OccupiedHeatingSetpoint <= (OccupiedCoolingSetpoint - MinSetpointDeadBand)"
  }
]

**EXTRACTION STRATEGY**:
- Parse bullet lists of inequalities into constraints
- Categorize each constraint by its type
- List all attributes referenced in each constraint
- Provide pseudocode `assert` statements to enforce constraints
- If no setpoint limit rules found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

USER_CREATION_STEPS_EXTRACTION_PROMPT = """
You are extracting procedural recommendations for user creation from a Matter protocol specification section.

**TASK**: Extract ONLY recommended steps for creating a new user and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture overall recommendation (e.g., query for available UserIndex first)
- Capture each step in correct order
- Capture command names and parameters (e.g., UserIndex)
- Provide pseudocode workflow

**JSON OUTPUT FORMAT**:
{
  "precondition": "Administrator queries door lock with GetUser to find available UserIndex",
  "steps": [
    {
      "order": 1,
      "action": "Set user record fields",
      "command": "SetUser",
      "parameters": ["UserIndex", "user record fields"],
      "pseudocode": "pseudocode representation if applicable"
    },
    {
      "order": 2,
      "action": "Add one or more credentials",
      "command": "SetCredential",
      "parameters": ["UserIndex", "credentials"],
      "pseudocode": "call SetCredential(UserIndex, credential_list)"
    },
    {
      "order": 3,
      "action": "Add one or more schedule restrictions",
      "command": "SetWeekDaySchedule or SetYearDaySchedule",
      "parameters": ["UserIndex", "schedule"],
      "pseudocode": "call SetWeekDaySchedule(UserIndex, schedule) OR call SetYearDaySchedule(UserIndex, schedule)"
    }
  ]
}

**EXTRACTION STRATEGY**:
- Extract the initial recommendation/precondition
- Parse enumerated steps (1, 2, 3, …)
- Normalize each into action, command, parameters
- Provide pseudocode for automation
- If no user creation steps found, return empty object {}

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

FABRIC_SCOPING_EXTRACTION_PROMPT = """
You are extracting fabric-scoping handling rules from a Matter protocol specification section.

**TASK**: Extract ONLY rules and constraints related to fabric scoping and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture scope rule (e.g., attributes/commands are scoped per fabric)
- Capture exceptions (e.g., SceneValid Field of FabricSceneInfo)
- Capture specific constraints:
  • Behavior when no fabric is available
  • Handling of duplicate Group ID/Scene ID across fabrics
  • Behavior when leaving a fabric
  • Scene Table capacity limits
- Provide pseudocode representation of each rule

**JSON OUTPUT FORMAT**:
[
  {
    "rule": "Attributes and commands are scoped to accessing fabric only",
    "exception": "SceneValid field of FabricSceneInfo",
    "pseudocode": "pseudocode representation if applicable"
  },
  {
    "rule": "Operations without an accessing fabric SHALL fail",
    "status_code": "UNSUPPORTED_ACCESS",
    "pseudocode": "if accessing_fabric == null then return UNSUPPORTED_ACCESS"
  },
  {
    "rule": "Scenes with same Group ID + Scene ID across fabrics are fabric-isolated",
    "pseudocode": "lookup_scene := scene_table[accessing_fabric][group_id][scene_id]"
  },
  {
    "rule": "Removing a fabric clears associated scenes",
    "trigger": "RemoveFabric command (Operational Credentials Cluster)",
    "pseudocode": "on RemoveFabric(fabric): delete scene_table[fabric]"
  },
  {
    "rule": "Scene Table capacity per fabric < half of SceneTableSize (max 253)",
    "pseudocode": "if scene_table[fabric].count >= floor(SceneTableSize/2) or > 253 then apply resource_exhaustion_behavior()"
  }
]

**EXTRACTION STRATEGY**:
- Parse narrative rules into normalized JSON entries
- Capture exceptions separately
- Provide short pseudocode for each constraint
- Include status codes where mentioned
- If no fabric-scoping rules found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

MODE_NAMESPACE_EXTRACTION_PROMPT = """
You are extracting mode namespace definitions from a Matter protocol specification section.

**TASK**: Extract ONLY mode namespace definitions and return valid JSON object.

**EXTRACTION REQUIREMENTS**:
- Capture mode tag ranges (value range, name, summary)
- Capture common standard mode tag values with names and descriptions
- Ensure derived and manufacturer-specific tags are included as ranges
- Provide brief summaries for each tag definition

**JSON OUTPUT FORMAT**:
{
  "ranges": [
    {
      "range": "0x0000-0x3FFF",
      "name": "CommonTags",
      "summary": "Common standard values defined in this cluster specification"
    },
    {
      "range": "0x4000-0x7FFF",
      "name": "DerivedClusterTags",
      "summary": "Derived cluster-specific standard values"
    },
    {
      "range": "0x8000-0xBFFF",
      "name": "MfgTags",
      "summary": "Manufacturer-specific values (or under derived cluster)"
    }
  ],
  "common_tags": [
    { "id": "0x0000", "name": "Auto", "summary": "Device decides options, features and settings" },
    { "id": "0x0001", "name": "Quick", "summary": "Optimizes for faster completion" },
    { "id": "0x0002", "name": "Quiet", "summary": "Silent or barely audible operation" },
    { "id": "0x0003", "name": "LowNoise", "summary": "Mode is low-noise or optimizes for that" },
    { "id": "0x0004", "name": "LowEnergy", "summary": "Optimizes for lower energy usage (Eco mode)" },
    { "id": "0x0005", "name": "Vacation", "summary": "Suitable for use during vacations/absences" },
    { "id": "0x0006", "name": "Min", "summary": "Uses the lowest available setting value" },
    { "id": "0x0007", "name": "Max", "summary": "Uses the highest available setting value" },
    { "id": "0x0008", "name": "Night", "summary": "Recommended for use during night time" },
    { "id": "0x0009", "name": "Day", "summary": "Recommended for use during day time" }
  ]
}

**EXTRACTION STRATEGY**:
- Extract mode tag ranges table
- Extract all standard/common tag values and their textual descriptions
- Normalize into `ranges` and `common_tags`
- Summarize each description in ≤ 15 words
- If no mode namespace found, return empty object {}

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

UNITS_OF_TEMPERATURE_EXTRACTION_PROMPT = """
You are extracting temperature unit and data type rules from a Matter protocol specification section.

**TASK**: Extract ONLY temperature unit and data type definitions, rules, and cautions, and return a valid JSON object.

**EXTRACTION REQUIREMENTS**:
- Capture canonical unit of measurement
- Capture defined temperature-related data types
- Capture transfer vs display rules
- Capture cautions for calculations/comparisons
- Provide short pseudocode if calculation normalization is required

**JSON OUTPUT FORMAT**:
{
  "unit": "Celsius",
  "data_types": [
    "TemperatureDifference",
    "SignedTemperature",
    "UnsignedTemperature"
  ],
  "transfer_rule": "Temperature values MUST be transferred using these types",
  "display_rule": "Thermostats may display/store in other formats; SHOULD follow Conversion of Temperature Values for Display",
  "calculation_caution": "Convert to common type before calculations; integer scaling differs",
  "pseudocode": "convert_to_celsius(value, type) before compare_or_calculate()"
}

**EXTRACTION STRATEGY**:
- Extract canonical unit explicitly (e.g., °C)
- List all defined data types
- Separate transfer, display, and calculation rules
- Provide one pseudocode snippet for normalization
- If no temperature rules found, return empty object {}

Return ONLY the JSON object. No explanations, no markdown, no additional text.
"""

FABRICS_COMMISSIONERS_GUIDANCE_EXTRACTION_PROMPT = """
You are extracting guidance for fabrics and commissioners from a Matter protocol specification section.

**TASK**: Extract ONLY rules, recommendations, and best practices for fabrics/commissioners and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture purpose of the cluster (collaborative directory of ThreadNetworks, PreferredExtendedPanID)
- Capture recommendations for cluster interaction (which device types are valid)
- Capture rules for determining preferred networks (precedence order, primary gateway devices)
- Capture guidance on sensitive data handling (Thread credentials, user consent, contribution restrictions)
- Provide pseudocode for key decision logic

**JSON OUTPUT FORMAT**:
[
  {
    "topic": "Cluster purpose",
    "guidance": "Allows fabrics to share/manage ThreadNetworks and set PreferredExtendedPanID",
    "pseudocode": null
  },
  {
    "topic": "Cluster interaction",
    "guidance": "Fabrics should only use this cluster on endpoints with supported device types (Network Infrastructure Manager, Thread Border Router)",
    "pseudocode": "pseudocode representation if applicable"
  },
  {
    "topic": "Network availability",
    "guidance": "Networks from ThreadNetworks list and Active Dataset from Thread Border Router should be considered available",
    "pseudocode": null
  },
  {
    "topic": "Preferred network precedence",
    "guidance": "Directory on a Network Infrastructure Manager takes precedence; if multiple exist, prefer the one acting as primary Internet gateway",
    "pseudocode": "if multiple NIM: select primary_gateway.NIM as preferred_source"
  },
  {
    "topic": "User consent",
    "guidance": "Obtain user consent before contributing credentials; only contribute reachable networks",
    "pseudocode": "if not user_consent: deny_credential_contribution()"
  }
]

**EXTRACTION STRATEGY**:
- Parse narrative text into structured guidance items
- Normalize each into `topic`, `guidance`, and optional `pseudocode`
- Include precedence and user consent handling explicitly
- If no guidance found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

STATE_DESCRIPTION_EXTRACTION_PROMPT = """
You are extracting state machine descriptions from a Matter protocol specification section.

**TASK**: Extract ONLY state description rules and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Capture involved states (e.g., Timed On, Delayed Off)
- Capture relevant attributes and how they change over time
- Capture exceptions (e.g., value = 0xFFFF means no decrement)
- Provide short pseudocode representation of state behavior

**JSON OUTPUT FORMAT**:
[
  {
    "state": "Timed On",
    "related_command": "OnWithTimedOff",
    "attributes": ["OnTime"],
    "behavior": "OnTime decremented every 1/10s unless 0xFFFF",
    "pseudocode": "pseudocode representation if applicable"
  },
  {
    "state": "Delayed Off",
    "related_command": "OnWithTimedOff",
    "attributes": ["OffWaitTime"],
    "behavior": "OffWaitTime decremented every 1/10s unless 0xFFFF",
    "pseudocode": "if OffWaitTime != 0xFFFF then every 100ms: OffWaitTime := OffWaitTime - 1"
  }
]

**EXTRACTION STRATEGY**:
- Identify state names and their triggers (commands)
- Extract attribute update rules
- Capture exceptions explicitly (0xFFFF)
- Represent behavior as concise pseudocode
- If no state descriptions found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""


# all_subsection_types = [
#       "Classification",
#       "Revision History",
#       "Cluster ID",
#       "Attributes",
#       "Data Types",
#       "Features",
#       "Commands",
#       "Events",
#       "Derived Cluster Namespace",
#       "Dependencies",
#       "Mode Examples",
#       "Status Codes",
#       "Cluster IDs",
#       "Definitions",
#       "Conversion of Temperature Values for Display",
#       "Multi Position Details",
#       "Sequence of events for MultiPress",
#       "Summary of cases for MS feature flag",
#       "PIN/RFID Code Format",
#       "State Change Table for Lighting",
#       "Sequence of generated events",
#       "The Dimming Light Curve",
#       "Mode Use",
#       "Setpoint Limits",
#       "Recommended steps for creating a new User",
#       "Handling of fabric-scoping",
#       "State Description",
#       "Mode Namespace",
#       "Units of Temperature",
#       "Guidance for Fabrics / Commissioners"
#     ]

section_prompt_dict = {
  "Classification" : CLUSTER_OVERVIEW_EXTRACTION_PROMPT,
  "Revision History" : REVISION_HISTORY_EXTRACTION_PROMPT,
  "Cluster ID" : CLUSTER_OVERVIEW_EXTRACTION_PROMPT,
  "Attributes" : ATTRIBUTES_EXTRACTION_PROMPT,
  "Data Types" : DATA_TYPES_EXTRACTION_PROMPT,
  "Features" : FEATURES_EXTRACTION_PROMPT,
  "Commands" : COMMANDS_EXTRACTION_PROMPT,
  "Events" : EVENTS_EXTRACTION_PROMPT,
  "Derived Cluster Namespace" : DERIVED_CLUSTER_NAMESPACE_EXTRACTION_PROMPT,
  "Dependencies" : DEPENDENCIES_EXTRACTION_PROMPT,
  "Mode Examples" : MODE_EXAMPLES_EXTRACTION_PROMPT,
  "Status Codes" : STATUS_CODES_EXTRACTION_PROMPT,
  "Cluster IDs" : CLUSTER_OVERVIEW_EXTRACTION_PROMPT,
  "Definitions" : DEFINITIONS_EXTRACTION_PROMPT,
  "Conversion of Temperature Values for Display" : CONVERSIONS_EXTRACTION_PROMPT,
  "Multi Position Details" : MULTI_POSITION_DETAILS_EXTRACTION_PROMPT,
  "Sequence of events for MultiPress" : MULTIPRESS_SEQUENCE_EXTRACTION_PROMPT,
  "Summary of cases for MS feature flag" : MS_FEATURE_FLAG_SUMMARY_EXTRACTION_PROMPT,
  "PIN/RFID Code Format" : PIN_RFID_CODE_FORMAT_EXTRACTION_PROMPT,
  "State Change Table for Lighting" : STATE_CHANGE_TABLE_LIGHTING_EXTRACTION_PROMPT,
  "Sequence of generated events" : SEQUENCE_OF_GENERATED_EVENTS_EXTRACTION_PROMPT,
  "The Dimming Light Curve" : DIMMING_LIGHT_CURVE_EXTRACTION_PROMPT,
  "Mode Use" : MODE_USE_EXTRACTION_PROMPT,
  "Setpoint Limits" : SETPOINT_LIMITS_EXTRACTION_PROMPT,
  "Recommended steps for creating a new User" : USER_CREATION_STEPS_EXTRACTION_PROMPT,
  "Handling of fabric-scoping" : FABRIC_SCOPING_EXTRACTION_PROMPT,
  "State Description" : STATE_DESCRIPTION_EXTRACTION_PROMPT,
  "Mode Namespace" : MODE_NAMESPACE_EXTRACTION_PROMPT,
  "Units of Temperature" : UNITS_OF_TEMPERATURE_EXTRACTION_PROMPT,
  "Guidance for Fabrics / Commissioners" : FABRICS_COMMISSIONERS_GUIDANCE_EXTRACTION_PROMPT
}

# ==============================================================================
# TAMARIN PROVER MODEL GENERATION CONFIGURATION
# ==============================================================================

# Tamarin Generation Prompt Template (Direct from Cluster Details)
TAMARIN_GENERATION_PROMPT_TEMPLATE = """
You are a formal verification expert who generates Tamarin prover models from Matter IoT protocol cluster specifications.

CLUSTER SPECIFICATION TO ANALYZE:
{cluster_info}

**TAMARIN PROVER OVERVIEW:**

**File Structure:**
theory TheoryName begin
  // 1. Builtins (optional)
  builtins: hashing, symmetric-encryption
  
  // 2. Functions and equations (optional)
  functions: f/1, g/2
  equations: f(g(x, y)) = x
  
  // 3. Rules (protocol model)
  rule RuleName:
    let var = expr in
    [ Premise_Facts ]
  --[ Action_Facts ]->
    [ Conclusion_Facts ]
  
  // 4. Restrictions (optional)
  restriction name: "formula"
  
  // 5. Lemmas (properties to verify)
  lemma property_name [attributes]:
    "formula"
end

**Syntax Rules:**
- **Fresh variables**: Prefix with ~ (e.g., ~tid, ~nonce, ~key)
- **Persistent facts**: Prefix with ! (e.g., !Pk(~ltk)) - never consumed
- **Linear facts**: Default, consumed when used
- **Comments**: C-style (// or /* */)
- **Case-sensitive**: Identifiers are case-sensitive
- **Quoted numerals**: Use '0', '1', '2' for constants
- **Adversary model**: Dolev-Yao (controls network, can read/compose/inject)

**Rule Syntax:**
rule Name:
  let
    // Variable bindings (bottom-up evaluation)
    var1 = expr1
    var2 = expr2
  in
  [ Premises ]         // Linear/persistent facts consumed
--[ Actions ]->
    [ Conclusions ]      // Facts produced

**Lemma Syntax:**
lemma name [attributes]:
  [trace_quantifier]
  "All/Ex vars #i #j. 
     Fact@i & Fact@j ==> 
     conditions"

**Trace quantifiers:**
- **all-traces** (default): Property must hold for ALL traces
- **exists-trace**: Property must hold for SOME trace

**Lemma attributes:** typing, reuse, use_induction, sources

**Temporal operators:**
- @i - fact occurs at timepoint i
- #i < #j - timepoint ordering
- All, Ex - quantifiers over messages/timepoints

**Fact Types:**
- **Linear facts**: St_Cluster(...), most common, consumed when used
- **Persistent facts**: !Pk(...), never consumed
- **Fresh facts**: Fr(~x), for fresh value generation
- **Action facts**: Only in --[Actions]-> for lemma observability, NOT for state transitions

**TAMARIN MODEL GENERATION APPROACH:**

**STEP 1: CLUSTER BEHAVIORAL ANALYSIS**
Analyze the cluster specification to determine behavioral patterns:
- **Attribute-driven states**: States correspond to meaningful attribute value combinations
- **Command semantics**: Extract behavioral logic from "effect_on_receipt" descriptions
- **Timer-based transitions**: Identify countdown timers and automatic state changes with correct resolution
- **Conditional logic**: Commands with if/then/else branches require multiple rules with guards
- **Feature constraints**: Only use features defined in the specification, model as rule guards
- **Data type constraints**: Apply enum values, bitmap flags, and structure constraints
- **Event generation**: Model events as action facts when triggered by commands/states
- **Scene behaviors**: Include scene store/recall if scene-capable attributes exist
- **Fabric sensitivity**: Handle fabric-scoped attribute access patterns
- **Quality flags**: Distinguish read-only vs read-write attribute behaviors

**STEP 2: STATE IDENTIFICATION**
Define states based on cluster attributes and operational conditions:
- States represent actual device behavior, not internal processing
- Use attribute values to determine state invariants
- Include timer states if countdown attributes exist
- Model fault/error states if specified in cluster
- Ensure states reflect physical/logical device condition
- Consider data type enums for state values

**STEP 3: TRANSITION MODELING**
Create rules from command specifications:
- Parse "effect_on_receipt" for exact behavioral steps
- Split conditional commands into multiple guarded rules
- Model timer expiry as automatic transitions
- Include proper guard conditions for all branching logic
- Model event generation in action facts when specified
- Use data type constraints in let blocks and guards
- Handle scene behaviors for scene-capable attributes
- Include stay transitions for commands that extend/reset timers
- Enforce feature constraints by blocking commands when features prohibit execution

**STEP 4: DEFINE TAMARIN STRUCTURE**
theory [ClusterName]_Matter
begin
  // Builtins (if cryptography needed)
  builtins: hashing, symmetric-encryption
  
  // Functions for data types and operations
  functions: f/1, g/2
  equations: f(g(x, y)) = x
  
  // State facts (UNIFIED to prevent arity errors)
  // St_Cluster(~tid, state_enum, attr1, attr2, timer, ...)
  
  // Rules for each command/transition
  // rule <CommandName>_<FromState>_to_<ToState>:
  //   let
  //     // Guard conditions with data type checks
  //   in
  //   [ St_Cluster(~tid, 'from_state', attrs...) ]
  // --[ Command(~tid, '<CommandName>'),
  //     StateChange(~tid, 'from_state', 'to_state'),
  //     // Event generation, attribute updates
  //   ]->
  //   [ St_Cluster(~tid, 'to_state', updated_attrs...) ]
  
  // Timer rules (abstract symbolic)
  // Event generation rules
  // Lemmas for properties
end

**STEP 3: MODEL STATES AS FACTS (UNIFIED)**
- **CRITICAL**: Use a SINGLE fact name St_Cluster for entire cluster to prevent arity errors
- Structure: St_Cluster(~tid, state_enum, attr1, attr2, timer_val, ...)
- First parameter after ~tid MUST be state identifier (quoted: 'st_off', 'st_on', 'st_delayed')
- Ensure SAME NUMBER of attributes in EVERY rule (add placeholders if needed)
- Example: St_Cluster(~tid, 'st_off', onoff:'0', ontime:'0', offwait:'0')
- Pattern match on state enum in premises: St_Cluster(~tid, 'st_off', attrs...)

**STEP 5: MODEL TRANSITIONS AS RULES**
For each command/transition:
rule CommandName_FromState_to_ToState:
  let
    // Variable bindings (bottom-up evaluation)
    // Guard conditions with data type checks
  in
  [ St_Cluster(~tid, 'st_from', attrs...) ]
--[ Command(~tid, 'CommandName'),
    StateChange(~tid, 'st_from', 'st_to'),
    // Additional action facts for observability
  ]->
  [ St_Cluster(~tid, 'st_to', updated_attrs...) ]

**STEP 6: MODEL GUARDS AND CONDITIONS**
- Use 'let' blocks for conditional logic (variables defined later can be used earlier)
- Use pattern matching on state enum and attributes in premises
- Model feature checks with let conditions or separate rules
- Use quoted constants: 'disabled', 'enabled', '0', '1'
- NO arithmetic on timer values (causes parse errors)

**STEP 7: MODEL TIMERS (ABSTRACT SYMBOLIC)**
**CRITICAL**: DO NOT use arithmetic (e.g., "timer - '1'") as it causes parse errors
Model timers using abstract symbolic values:

// Timer start (set to active)
rule Timer_Start:
  [ St_Cluster(~tid, state, 'timer_off', attrs...) ]
--[ TimerStarted(~tid) ]->
  [ St_Cluster(~tid, state, 'timer_active', attrs...) ]

// Timer expiry (transition from active to expired)
rule Timer_Expire:
  [ St_Cluster(~tid, state, 'timer_active', attrs...) ]
--[ TimerExpired(~tid) ]->
  [ St_Cluster(~tid, state, 'timer_expired', attrs...) ]

// State change on timer expiry
rule Timer_Expiry_Transition:
  [ St_Cluster(~tid, 'st_timed', 'timer_expired', attrs...) ]
--[ StateChange(~tid, 'st_timed', 'st_next') ]->
  [ St_Cluster(~tid, 'st_next', 'timer_off', attrs...) ]

**Timer modeling approach:**
- Use symbolic values: 'timer_off', 'timer_active', 'timer_expired'
- For disabled timers: Use 'timer_disabled' (never transitions)
- Add comments explaining timer resolution from specification

**STEP 8: MODEL EVENTS**
**CRITICAL**: Action facts are ONLY for lemma observability, NOT state transitions

rule Generate_EventName:
  [ St_Cluster(~tid, state, attrs...) ]
--[ EventGenerated(~tid, 'EventName', <event_params>),
    // Include event priority in comments (Info/Critical/Debug)
  ]->
  [ St_Cluster(~tid, state, attrs...), Out('EventName') ]

**Model event-driven transitions:** If events trigger state changes, create rules

**STEP 9: ADD LEMMAS FOR VERIFICATION**
Define security/safety/liveness properties with proper syntax:

// Safety: No invalid state transitions (all-traces is default)
lemma state_consistency:
  "All tid s1 s2 #i #j.
    StateChange(tid, s1, s2) @i & StateChange(tid, s1, s2) @j ==> #i = #j"

// Safety: State invariants hold
lemma state_invariants:
  "All tid s #i.
    StateChange(tid, 'st_old', s) @i ==>
    // Invariant conditions from cluster spec
    (s = 'st_valid1' | s = 'st_valid2')"

// Liveness: Eventually reach target state (exists-trace)
lemma reachability:
  exists-trace
  "Ex tid #i. StateChange(tid, 'st_init', 'st_target') @i"

// Feature enforcement: Commands blocked when features prohibit
lemma feature_constraints:
  "All tid cmd #i.
    Command(tid, cmd) @i ==>
    // Feature availability conditions
    Ex #j. FeatureEnabled(tid) @j & #j < #i"

// Timer correctness: Timers eventually expire or reset
lemma timer_progress [reuse]:
  "All tid #i. TimerStarted(tid) @i ==>
    (Ex #j. TimerExpired(tid) @j & #i < #j) |
    (Ex #k. TimerStarted(tid) @k & #i < #k)"

**Lemma attributes:**
- [typing]: For type assertions
- [reuse]: Lemma can be reused by prover
- [use_induction]: Enable induction
- [sources]: Track message sources

**STEP 10: ADD DEFINITIONS AND REFERENCES**
// Add C-style comments explaining:
// - Technical terms from cluster specification
// - Feature flags and their meanings (use persistent facts !Feature(...) if needed)
// - Data type enums and their behavioral implications (quoted: 'enum_value')
// - Timer resolution and units (abstract symbolic, not arithmetic)
// - References to other clusters or specifications
// - Restrictions on valid traces (use restriction keyword)

**REQUIRED TAMARIN STRUCTURE:**
theory ClusterName_Matter
begin

// Cluster: [ClusterName]
// Cluster ID: [0xHEX]
// Generated from Matter cluster specification

builtins: hashing

// Functions for cluster operations (if needed)
functions: f/1, g/2
equations: f(g(x, y)) = x

// Initial state rule with fresh thread ID
rule Init_Cluster:
  [ Fr(~tid) ]
--[ ClusterInit(~tid) ]->
  [ St_Cluster(~tid, 'st_initial', default_attr1, default_attr2, 'timer_off') ]

// Command rules (unified state fact to prevent arity errors)
rule Command_Name:
  let
    // Variable bindings for guards (bottom-up evaluation)
  in
  [ St_Cluster(~tid, 'st_from', attrs...) ]
--[ Command(~tid, 'CommandName'),
    StateChange(~tid, 'st_from', 'st_to')
  ]->
  [ St_Cluster(~tid, 'st_to', new_attrs...) ]

// Timer rules (abstract symbolic - NO arithmetic)
rule Timer_Expire:
  [ St_Cluster(~tid, state, 'timer_active', attrs...) ]
--[ TimerExpired(~tid) ]->
  [ St_Cluster(~tid, state, 'timer_expired', attrs...) ]

// Event generation rules (action facts for observability)
rule Generate_Event:
  [ St_Cluster(~tid, state, attrs...) ]
--[ EventGenerated(~tid, 'EventName', params) ]->
  [ St_Cluster(~tid, state, attrs...), Out('EventName') ]

// Restrictions (optional - constrain valid traces)
restriction valid_transitions:
  "All tid s1 s2 #i. StateChange(tid, s1, s2) @i ==>
    // Define valid state transitions
    (s1 = 'st_init' & s2 = 'st_active') |
    (s1 = 'st_active' & s2 = 'st_off')"

// Lemmas (properties to verify)
lemma safety_no_invalid_transitions:
  "All tid s1 s2 #i. StateChange(tid, s1, s2) @i ==>
    (s1 = 'st_init' & s2 = 'st_active') |
    (s1 = 'st_active' & s2 = 'st_off')"

lemma liveness_reachable:
  exists-trace
  "Ex tid #i. StateChange(tid, 'st_init', 'st_target') @i"

end

**CRITICAL ACCURACY REQUIREMENTS:**
1. **Syntactically valid Tamarin**: Must parse without errors using Tamarin parser
2. **Unified state facts**: Use SINGLE fact St_Cluster(~tid, state_enum, attrs...) to prevent arity errors
3. **Consistent arity**: SAME NUMBER of parameters in every St_Cluster fact across all rules
4. **Action facts**: Only in --[Actions]-> for observability, NOT for state transitions
5. **Rules**: Model all commands, automatic transitions, timer behaviors, stay transitions
6. **Lemmas**: Meaningful safety (all-traces) and liveness (exists-trace) properties
7. **C-style comments**: Use // or /* */ for explanations
8. **Fresh variables**: Prefix with ~ (e.g., ~tid, ~nonce, ~key)
9. **Quoted constants**: Use 'st_off', 'timer_active', '0', '1' for symbolic values
10. **NO arithmetic**: Never use timer - '1' or similar (causes parse errors)
11. **Let blocks**: Bottom-up evaluation, variables defined later can be used earlier
12. **Pattern matching**: Match on quoted state enums in premises
13. **Correct arrow syntax**: Use --[Actions]-> for rules with actions
14. **Timer modeling**: Abstract symbolic ('timer_off', 'timer_active', 'timer_expired')
15. **Feature facts**: Use persistent !Feature(...) if features are global
16. **Event generation**: Action facts for observability, Out(...) for external messages
17. **Restrictions**: Use restriction keyword to constrain valid traces
18. **Lemma attributes**: Use [typing], [reuse], [use_induction] when appropriate
19. **Dolev-Yao adversary**: Network-controlled adversary reads/composes/injects messages
20. **Temporal operators**: Use @i for timepoints, #i < #j for ordering

**ANALYSIS STRATEGY:**
1. Extract cluster states from attributes and behaviors
2. Map each command to transition rules
3. Model attribute updates in rule conclusions
4. Add action facts for observability
5. Include timer decrement and expiry rules if timers exist
6. Model event generation with action facts
7. Add lemmas for key safety/liveness properties
8. Ensure all state transitions are covered

Focus on accurate Tamarin syntax and faithful representation of cluster behavior.

Return ONLY the Tamarin theory code. No explanations, no markdown blocks (except the theory itself), no additional text.
"""

# FSM to Tamarin Conversion Prompt Template
FSM_TO_TAMARIN_PROMPT_TEMPLATE = """
You are a formal verification expert who converts FSM JSON models to Tamarin prover theories.

FSM MODEL TO CONVERT:
{fsm_json}

**CONVERSION OBJECTIVE:**
Transform the FSM JSON structure into a syntactically valid Tamarin theory that preserves all states, transitions, guards, actions, and properties.

**TAMARIN PROVER SYNTAX REFERENCE:**

**Theory Structure:**
theory [ClusterName]_Matter
begin
  builtins: <cryptographic primitives>
  functions: <user-defined functions>
  // Rules
  // Lemmas
end

**Rules (Multiset Rewriting):**
rule <RuleName>:
  let
    <variable bindings>
  in
  [ <Premise Facts> ]
--[ <Action Facts> ]->
  [ <Conclusion Facts> ]

**Facts:**
- State facts: St_<StateName>(~tid, params...)
- In/Out facts: In(msg), Out(msg)
- Fresh names: Fr(~name)
- Action facts (for lemmas): Custom(params...)

**Lemmas:**
lemma <name>:
  "<first-order logic formula>"

lemma <name>:
  exists-trace
  "<first-order logic formula>"

**CONVERSION STRATEGY:**

**STEP 1: EXTRACT FSM METADATA**
- Cluster name → theory name
- Cluster ID → comment
- Category → comment
- Initial state → Init rule target
- Metadata (timestamps, attempts, source pages) → comments
- Definitions[] → explanatory comments in theory
- References[] → dependency comments

**STEP 2: MAP STATES TO FACTS**
For each FSM state:
- State name → St_<StateName>(~tid, ...)
- Invariants[] → guard conditions in rules or lemma formulas
- Attributes_monitored[] → fact parameters (match FSM attributes_used[])
- Description → comment above state first usage
- Is_initial → determines Init rule target

**STEP 3: CONVERT TRANSITIONS TO RULES**
For each FSM transition:
rule <Trigger>_<FromState>_to_<ToState>:
  let
    // Guard condition logic from FSM
  in
  [ St_<FromState>(~tid, attrs) ]
--[ Command(~tid, '<Trigger>'),
    StateChange(~tid, '<FromState>', '<ToState>'),
    // Additional facts from FSM actions
  ]->
  [ St_<ToState>(~tid, updated_attrs) ]

**STEP 4: MODEL FSM GUARDS**
- Boolean conditions → let bindings (bottom-up evaluation)
- Feature checks (bitmap flags) → let conditions or persistent !Feature(...) facts
- Timer checks → pattern matching on symbolic values ('timer_active', 'timer_off')
- Enum value checks → pattern matching on quoted state enum in premises
- Data type constraints → let block validation with quoted constants
- Conditional branches (if/then/else) → separate rules with complementary guards
- Use quoted constants: 'disabled', 'enabled', 'st_off', 'st_on'

**STEP 5: MODEL FSM ACTIONS**
For each action in transition.actions[]:
- Attribute updates → new state fact parameters with updated values
- Event generation → EventGenerated action facts (observability only)
- Timer operations → symbolic state changes ('timer_off', 'timer_active', 'timer_expired')
- Scene store/recall → SceneStored/SceneRecalled action facts
- Feature validation → FeatureChecked action facts or persistent !Feature(...)
- Attribute read/write → AttributeAccessed action facts

**STEP 6: HANDLE TIMING REQUIREMENTS (ABSTRACT SYMBOLIC)**
**CRITICAL**: NO arithmetic on timer values (causes parse errors)
If timing_requirements field is not null:
- Parse resolution (100ms, 1s, etc.) → add C-style comment explaining units
- Model timer as symbolic: 'timer_off', 'timer_active', 'timer_expired', 'timer_disabled'
- Timer start → transition to 'timer_active'
- Timer expiry → transition from 'timer_active' to 'timer_expired'
- Timer reset → transition from any state back to 'timer_active'
- Use action facts: TimerStarted, TimerExpired (for lemma observability)
- Disabled timers (0xFFFF) → use 'timer_disabled' (never transitions)

**STEP 7: MODEL STAY TRANSITIONS**
For transitions where from_state == to_state:
- These are stay transitions (state continuation)
- Model timer extensions, attribute updates without state change
- Include appropriate action facts (TimerReset, AttributeUpdated)

**STEP 8: MODEL FSM EVENTS**
For each event in events_generated[]:
- Create EventGenerated action facts with event name and parameters
- If event triggers transitions, model as separate rules
- Use Out(<EventName>) facts for external observability
- Include event priority in comments (Info/Critical/Debug)

**STEP 9: INTEGRATE FSM DATA TYPES**
For each data type in data_types_used[]:
- Enums → pattern matching on specific values in let blocks
- Bitmaps → feature flag checks in guards
- Structures → nested parameters in state facts
- Add comments explaining enum meanings and bitmap flags

**STEP 10: MODEL SCENE BEHAVIORS**
For each scene behavior in scene_behaviors[]:
- Create SceneStored/SceneRecalled action facts
- Model scene-capable attribute store/recall transitions
- Link to scene cluster if referenced

**STEP 11: ADD DEFINITIONS AND REFERENCES**
From FSM definitions[] and references[]:
- Add comments explaining technical terms and functions
- Document feature flags and their meanings
- Explain data type enums and behavioral implications
- Document timer resolution and units
- Add comments for referenced clusters/specifications

**STEP 12: GENERATE LEMMAS FROM FSM**
- From state.invariants[] → safety lemmas (state_invariants)
- From reachability goals → exists-trace lemmas (state_reachability)
- From commands_handled[] → command validity lemmas
- From timing_requirements → timer progress lemmas
- From feature constraints → feature enforcement lemmas
- From definitions[] → explanatory comments in lemmas
- From events_generated[] → event generation lemmas
- From scene_behaviors[] → scene capability lemmas

**FSM TO TAMARIN MAPPING:**

| FSM Element | Tamarin Equivalent |
|-------------|-------------------|
| states[] | St_Cluster(~tid, 'state_enum', attrs...) unified fact |
| transitions[] | rule Name: [...] --[Actions]-> [...] |
| initial_state | Init rule → St_Cluster(~tid, 'st_initial', ...) |
| guard_condition | let blocks (bottom-up), pattern matching on quoted values |
| actions[] | Conclusion facts, action facts (observability only) |
| events_generated[] | Action facts: EventGenerated(...), Out('event') |
| attributes_used[] | State fact parameters (SAME arity in all rules) |
| commands_handled[] | Rule names/triggers, Command action facts |
| definitions[] | C-style comments (// or /* */) throughout theory |
| timing_requirements | Abstract symbolic timers (NO arithmetic) |
| data_types_used[] | Quoted enum patterns, feature guards |
| scene_behaviors[] | SceneStored/SceneRecalled action facts |
| references[] | Dependency comments, persistent !Facts if needed |
| invariants[] | Safety lemmas (all-traces), restrictions |
| is_initial flag | Target of Init rule |
| metadata | Comments with generation info |
| definitions[] | Explanatory comments throughout theory |
| timing_requirements | Timer decrement/expiry/reset rules, comments |
| data_types_used[] | Enum patterns, bitmap guards, structure parameters |
| scene_behaviors[] | SceneStored/SceneRecalled action facts |
| references[] | Dependency comments, related cluster notes |
| invariants[] | Safety lemmas, state_invariants formulas |
| is_initial flag | Target of Init rule |
| metadata | Comments with generation info |

**REQUIRED TAMARIN OUTPUT:**

theory {cluster_name}_Matter
begin

// Cluster: {cluster_name}
// Cluster ID: {cluster_id}
// Source: FSM JSON model
// Generated: {generation_timestamp}

builtins: hashing

// Functions for operations (if needed)
functions: f/1

// === INITIALIZATION ===
rule Init_{cluster_name}:
  [ Fr(~tid) ]
--[ ClusterInit(~tid) ]->
  [ St_Cluster(~tid, 'st_{initial_state}', <initial_attribute_values>) ]

// === STATE TRANSITIONS (from FSM transitions[]) ===
// CRITICAL: Use unified St_Cluster fact with SAME arity in all rules
// For each transition in FSM:
rule {trigger}_{from_state}_to_{to_state}:
  let
    // Guard condition from FSM guard_condition (bottom-up evaluation)
    // Use quoted constants: 'value', 'st_name'
  in
  [ St_Cluster(~tid, 'st_{from_state}', {attributes}) ]
--[ Command(~tid, '{trigger}'),
    StateChange(~tid, 'st_{from_state}', 'st_{to_state}'),
    // Action facts from FSM actions[] (observability only)
  ]->
  [ St_Cluster(~tid, 'st_{to_state}', {updated_attributes}) ]

// === TIMER BEHAVIORS (ABSTRACT SYMBOLIC - NO ARITHMETIC) ===
rule Timer_Start:
  [ St_Cluster(~tid, state, 'timer_off', attrs...) ]
--[ TimerStarted(~tid) ]->
  [ St_Cluster(~tid, state, 'timer_active', attrs...) ]

rule Timer_Expire:
  [ St_Cluster(~tid, state, 'timer_active', attrs...) ]
--[ TimerExpired(~tid) ]->
  [ St_Cluster(~tid, state, 'timer_expired', attrs...) ]

rule Timer_Expiry_Transition:
  [ St_Cluster(~tid, 'st_{timed_state}', 'timer_expired', attrs...) ]
--[ StateChange(~tid, 'st_{timed_state}', 'st_{next_state}') ]->
  [ St_Cluster(~tid, 'st_{next_state}', 'timer_off', attrs...) ]

// === EVENT GENERATION (from FSM events_generated[]) ===
// Action facts are ONLY for observability in lemmas
rule Generate_{event_name}:
  [ St_Cluster(~tid, state, attrs...) ]
--[ EventGenerated(~tid, '{event_name}', <params>) ]->
  [ St_Cluster(~tid, state, attrs...), Out('{event_name}') ]

// === RESTRICTIONS (optional - constrain valid traces) ===
restriction valid_state_transitions:
  "All tid s1 s2 #i. StateChange(tid, s1, s2) @i ==>
    // Define valid transitions from FSM
    (s1 = 'st_init' & s2 = 'st_active') |
    (s1 = 'st_active' & s2 = 'st_off')"

// === LEMMAS (derived from FSM invariants and properties) ===

// Safety: State invariants preserved (all-traces default)
lemma state_invariants:
  "All tid s #i. StateChange(tid, 'st_old', s) @i ==>
    // Derived from FSM state invariants[]
    (s = 'st_valid1' | s = 'st_valid2')"

// Liveness: All states reachable (exists-trace)
lemma state_reachability:
  exists-trace
  "Ex tid #i. StateChange(tid, 'st_init', 'st_{target_state}') @i"

// Command execution: Commands only in valid states
lemma command_validity:
  "All tid cmd state #i #j.
    Command(tid, cmd) @i & StateChange(tid, state, 'st_any') @j & #j < #i ==>
    // Commands only execute from valid states per FSM
    (state = 'st_valid1' | state = 'st_valid2')"

// Timer progress: Timers eventually expire or reset
lemma timer_progress [reuse]:
  "All tid #i. TimerStarted(tid) @i ==>
    (Ex #j. TimerExpired(tid) @j & #i < #j) |
    (Ex #k. TimerStarted(tid) @k & #i < #k)"

end

**CONVERSION CHECKLIST:**
✓ Theory name matches cluster name
✓ Unified state fact: St_Cluster(~tid, state_enum, attrs...) used throughout
✓ Consistent arity: SAME number of parameters in all St_Cluster facts
✓ All FSM states converted with quoted enums ('st_off', 'st_on')
✓ All FSM transitions converted to rules (including stay transitions)
✓ Guard conditions use let blocks (bottom-up evaluation) and pattern matching
✓ Actions mapped to conclusion facts and action facts (observability only)
✓ Timer behaviors use abstract symbolic values (NO arithmetic)
✓ Events captured as EventGenerated action facts and Out('event') facts
✓ Data types integrated with quoted enum patterns and feature guards
✓ Scene behaviors modeled (store/recall if applicable)
✓ Feature constraints use persistent !Feature(...) or let conditions
✓ Lemmas derive from FSM properties with proper syntax
✓ Definitions and references documented in C-style comments
✓ Syntactically valid Tamarin code (parseable with Tamarin tool)
✓ Fresh variables consistently use ~ prefix (~tid, ~nonce)
✓ Comments explain FSM-to-Tamarin mappings and complex logic
✓ Stay transitions included where from_state == to_state
✓ Conditional branches (if/then/else) split into separate rules
✓ Metadata preserved in theory header comments
✓ Restrictions added to constrain valid traces (if needed)
✓ Lemma attributes used appropriately ([typing], [reuse], etc.)

**CRITICAL REQUIREMENTS:**
1. **Preserve FSM semantics**: Exact behavioral equivalence between FSM and Tamarin
2. **Valid Tamarin syntax**: Must parse without errors using Tamarin parser
3. **Complete coverage**: All FSM elements mapped (states, transitions, events, data types)
4. **Correct guards**: Conditional logic faithfully translated with data type checks
5. **Action facts**: Observable events captured (commands, state changes, events, timers)
6. **Meaningful lemmas**: Verify key properties from FSM invariants and requirements
7. **Documentation**: Comments explain FSM-to-Tamarin mappings, definitions, references
8. **Timer semantics**: Decrement, expiry, reset, extension correctly modeled with resolution
9. **Feature enforcement**: Feature constraints from FSM enforced in rule guards
10. **Event generation**: All FSM events_generated[] mapped to action facts
11. **Data type integration**: Enums, bitmaps, structures properly handled in guards/parameters
12. **Scene behaviors**: Scene store/recall modeled if scene_behaviors[] present
13. **Stay transitions**: State continuation (from_state==to_state) modeled for timers/attributes
14. **Conditional branches**: If/then/else logic split into separate guarded rules
15. **Thread isolation**: Consistent use of thread IDs (~tid) for independent instances

Analyze the FSM JSON systematically and generate the corresponding Tamarin theory.

Return ONLY the Tamarin theory code. No explanations, no markdown blocks (except the theory), no additional text.
"""