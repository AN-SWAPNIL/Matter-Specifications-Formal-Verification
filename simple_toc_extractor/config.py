"""
Configuration file for Matter PDF TOC Extractor
Customize extraction parameters and settings here
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_TEMPERATURE = 0.0  # More deterministic for detailed extraction
GEMINI_MAX_OUTPUT_TOKENS = 32768  # Significantly increased for comprehensive behavioral extraction

# PDF Processin**STEP 4:**STEP 5: FEATURE VALIDATION**EMANTICS**ation
PDF_FILENAME = "Matter-1.4-Application-Cluster-Specification.pdf"
PDF_PATH = os.path.join(os.path.dirname(__file__), "..", PDF_FILENAME)
MAX_TOC_PAGES = 50  # Maximum pages to scan for TOC content

# Vector Store Configuration
EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1500  # Increased for better table capture
CHUNK_OVERLAP = 500  # More overlap for table continuations
VECTOR_SEARCH_K = 15  # More documents for comprehensive context

# Output Configuration
OUTPUT_JSON_FILE = "matter_clusters_toc.json"
RAW_TOC_FILE = "raw_toc.txt"
OUTPUT_DIRECTORY = os.path.dirname(__file__)

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

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
        "description": "brief change summary (max 100 chars)",
        "date": "revision date if available"
      }}
    ],
    "features": [
      {{
        "bit": "bit number (0-31)",
        "code": "feature code (2-4 chars)",
        "name": "full feature name",
        "summary": "brief feature description (max 80 chars)",
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
        "summary": "brief attribute purpose (max 100 chars)",
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
        "summary": "brief command purpose (max 100 chars)",
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
            "summary": "brief field description (max 50 chars)"
          }}
        ],
        "effect_on_receipt": "Concise algorithmic steps (max 200 chars): state changes, attribute updates, conditions. Example: 'if [condition]==TRUE: [action1], set [attribute]:=FALSE, set [other_attribute]:=[value]'"
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
- Use character limits: summaries max 100 chars, effect_on_receipt max 200 chars
- Close all braces properly - never truncate JSON structure

Extract from the provided cluster specification text and return complete valid JSON only.
"""

# Page buffer for cluster extraction (pages before and after cluster boundaries)
CLUSTER_PAGE_BUFFER = 2  # Increased to capture more context and table continuations

# Page offset - number of pages before actual content starts (TOC pages, covers, etc.)
PDF_PAGE_OFFSET = 4  # Actual content starts at PDF page 5, but TOC refers to logical page 1

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
        "trigger": "[command name or timer/event]",
        "guard_condition": "[boolean condition with data type constraints]",
        "actions": ["[attribute updates]", "[event generation if applicable]"],
        "response_command": null
      }}
    ],
    "initial_state": "[appropriate default state]",
    "attributes_used": ["[all referenced attributes with quality flags]"],
    "commands_handled": ["[all cluster commands]"],
    "events_generated": ["[cluster events from specification]"],
    "data_types_used": ["[enums, bitmaps, structures referenced]"],
    "scene_behaviors": ["[scene store/recall actions if applicable]"],
    "generation_timestamp": "[current timestamp]",
    "source_metadata": {{
      "extraction_method": "AI_behavioral_analysis",
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
12. Validate against specification features and constraints
13. Ensure complete coverage of commands, events, and data type interactions

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

# Section-Based Extraction Prompts
# Following the same unbiased structure as CLUSTER_DETAIL_EXTRACTION_PROMPT

REVISION_HISTORY_EXTRACTION_PROMPT = """
You are extracting revision history information from a Matter protocol cluster specification section.

**TASK**: Extract ONLY revision history entries from the provided text and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for revision tables with "Revision" and "Description" columns
- Extract revision numbers (1, 2, 3, etc.)
- Extract brief change descriptions 
- Extract dates if available (often not present)
- Look for text like "The global ClusterRevision attribute value SHALL be the highest revision number"

**JSON OUTPUT FORMAT**:
[
  {
    "revision": "1",
    "description": "brief change summary (max 100 chars)",
    "date": "date if available or null"
  }
]

**EXTRACTION STRATEGY**:
- Search for numbered revision entries in tables or lists
- Keep descriptions concise and factual
- Use null for missing dates
- If no revision history found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

FEATURES_EXTRACTION_PROMPT = """
You are extracting feature information from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster features from the provided text and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for feature tables with columns like "Bit", "Code", "Feature", "Summary", "Conformance"
- Extract bit positions (0-31 for feature flags)
- Extract feature codes (2-4 character abbreviations like "GN", "OO")
- Extract full feature names and descriptions
- Extract conformance requirements (M/O/F/C)
- Look for feature dependencies if any

**JSON OUTPUT FORMAT**:
[
  {
    "bit": "bit number (0-31)",
    "code": "feature code (2-4 chars)",
    "name": "full feature name",
    "summary": "brief feature description (max 80 chars)",
    "conformance": "M/O/F/C conformance",
    "dependencies": "feature dependencies if any or null"
  }
]

**EXTRACTION STRATEGY**:
- Look for sections titled "Features" or numbered like "X.Y.3 Features"
- Extract from feature definition tables completely
- Capture feature capability descriptions
- If no features found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

DATA_TYPES_EXTRACTION_PROMPT = """
You are extracting data type definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY custom data types (enums, bitmaps, structures) from the provided text and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- **Enumerations**: Extract enum types with value tables (0x00, 0x01, etc.)
- **Bitmaps**: Extract bitmap types with bit definitions (bit 0, bit 1, etc.)
- **Structures**: Extract structure types with field definitions
- Look for sections like "X.Y.4 Data Types" or "X.Y.5 [TypeName] Type"
- Extract type names, base types, and all value/field definitions

**JSON OUTPUT FORMAT**:
[
  {
    "name": "data type name (e.g., IdentifyTypeEnum)",
    "base_type": "base type (enum8/enum16/map8/map16/struct/etc.)",
    "constraint": "constraints if any or null",
    "values": [
      {
        "value": "For ENUMS: hex code (0x00), For BITMAPS: bit number (0-7), For STRUCTS: field order",
        "name": "For ENUMS: enum name, For BITMAPS: bit name, For STRUCTS: field name", 
        "summary": "description of enum value/bit/field",
        "conformance": "M/O/F conformance requirement"
      }
    ]
  }
]

**EXTRACTION STRATEGY**:
- Find all enum, bitmap, and struct type definitions
- Extract complete value/field tables for each type
- Preserve hex values exactly as shown (0x00, 0x01, etc.)
- Include ALL types found in the specification text
- If no data types found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

ATTRIBUTES_EXTRACTION_PROMPT = """
You are extracting attribute definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster attributes from the provided text and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for attribute tables with columns like "ID | Name | Type | Constraint | Quality | Default | Access | Conformance"
- Extract hex attribute IDs (0x0000, 0x0001, etc.)
- Extract attribute names, types, constraints, quality flags
- Extract default values and access permissions
- Look for individual attribute descriptions in subsections
- Extract fabric sensitivity and scene capability information

**JSON OUTPUT FORMAT**:
[
  {
    "id": "hex attribute ID (0x0000)",
    "name": "full attribute name",
    "type": "data type (including custom types)",
    "constraint": "value constraints, ranges, or 'desc'",
    "quality": "quality flags (N/S/P/F/X/C)",
    "default": "default value or 'desc' if varies",
    "access": "access permissions (R/W/RW, may include F for fabric)",
    "conformance": "M/O/F conformance requirement",
    "summary": "brief attribute purpose (max 100 chars)",
    "fabric_sensitive": true/false,
    "scene_capable": true/false
  }
]

**EXTRACTION STRATEGY**:
- Find attribute definition tables and extract ALL rows
- Look for detailed attribute descriptions in subsections
- Extract behavioral descriptions for attribute usage
- Use exact hex IDs and preserve technical specifications
- If no attributes found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

COMMANDS_EXTRACTION_PROMPT = """
You are extracting command definitions with behavioral logic from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster commands from the provided text and return valid JSON array with pseudocode.

**EXTRACTION REQUIREMENTS**:
- Look for command tables with columns like "ID | Name | Direction | Response | Access | Conformance"
- Extract hex command IDs (0x00, 0x01, etc.)
- Extract command names, directions, response types
- Extract command field definitions from payload tables
- **CRITICAL**: Extract "Effect on Receipt" behavioral logic for PSEUDOCODE generation

**BEHAVIORAL EXTRACTION FOR PSEUDOCODE**:
Convert "Effect on Receipt" behavioral text into algorithmic pseudocode:
- **Conditionals**: "if [condition] then [action] else [action]"
- **Assignments**: "set [attribute] := [value]"
- **Procedures**: "call [function]([params])"
- **State changes**: "[object].state := [new_state]"
- **Timers**: "start_timer([duration])" or "stop_timer()"

**JSON OUTPUT FORMAT**:
[
  {
    "id": "hex command ID (0x00)",
    "name": "full command name",
    "direction": "client ⇒ server or client ⇐ server",
    "response": "response command name or 'Y'/'N'",
    "access": "access level and fabric requirements",
    "conformance": "M/O/F conformance requirement",
    "summary": "brief command purpose (max 100 chars)",
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
        "summary": "brief field description (max 50 chars)"
      }
    ],
    "effect_on_receipt": "Algorithmic pseudocode (max 200 chars): set attr := value; if condition then action else action"
  }
]

**EXTRACTION STRATEGY**:
- Find command definition tables and extract ALL commands
- Look for command field tables within command subsections  
- Extract complete "Effect on Receipt" behavioral text
- Convert behavioral logic to concise pseudocode format
- Include both client-to-server and server-to-client commands
- If no commands found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

EVENTS_EXTRACTION_PROMPT = """
You are extracting event definitions from a Matter protocol cluster specification section.

**TASK**: Extract ONLY cluster events from the provided text and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for event tables with columns like "ID | Name | Priority | Access | Conformance"
- Extract hex event IDs (0x00, 0x01, etc.)
- Extract event names, priority levels, access requirements
- Extract event field definitions from payload tables
- Look for sections like "X.Y.8 Events"

**JSON OUTPUT FORMAT**:
[
  {
    "id": "hex event ID (0x00)",
    "name": "full event name", 
    "priority": "event priority (Info/Critical/Debug)",
    "access": "access requirements",
    "conformance": "M/O/F conformance",
    "summary": "event description (max 80 chars)",
    "fields": [
      {
        "id": "field ID",
        "name": "field name",
        "type": "data type",
        "conformance": "field conformance"
      }
    ]
  }
]

**EXTRACTION STRATEGY**:
- Find event definition tables and sections
- Extract event field definitions completely
- Look for event generation conditions and triggers
- If no events found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

CLUSTER_ID_EXTRACTION_PROMPT = """
You are extracting cluster identifier definitions from a Matter protocol specification section.

**TASK**: Extract ONLY cluster ID definitions from the provided text and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for cluster ID tables with columns like "ID | Name"
- Extract hex cluster IDs (0x0000, 0x0001, etc.)
- Extract full cluster names
- Capture ID/name mappings only (no attributes, commands, or events here)
- Include a short summary for each cluster

**JSON OUTPUT FORMAT**:
[
  {
    "id": "hex cluster ID (0x0006)",
    "name": "full cluster name",
    "summary": "brief cluster purpose (max 80 chars)"
  }
]

**EXTRACTION STRATEGY**:
- Find cluster ID tables and extract ALL entries
- Look for sections like "X.Y.Z Cluster ID"
- Preserve exact hex IDs and names as given
- If no clusters found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
"""

CLASSIFICATION_EXTRACTION_PROMPT = """
You are extracting cluster classification definitions from a Matter protocol specification section.

**TASK**: Extract ONLY cluster classification information and return valid JSON array.

**EXTRACTION REQUIREMENTS**:
- Look for classification tables with columns like "Hierarchy | Role | Scope | PICS Code"
- Extract hierarchy (e.g., Base, Functional, Utility)
- Extract role (e.g., Application, Aggregator, Utility)
- Extract scope (e.g., Endpoint, Node, Fabric)
- Extract PICS code (e.g., OO, OT, LV)
- Include a short summary for the classification

**JSON OUTPUT FORMAT**:
[
  {
    "hierarchy": "Base/Functional/Utility/etc.",
    "role": "Application/Aggregator/Utility/etc.",
    "scope": "Endpoint/Node/Fabric/etc.",
    "pics_code": "PICS short code",
    "summary": "brief classification purpose (max 80 chars)"
  }
]

**EXTRACTION STRATEGY**:
- Find classification tables and extract ALL rows
- Look for sections like "X.Y.Z Classification"
- Allow flexible interpretation if column names differ (e.g., 'Layer' for 'Hierarchy', 'Domain' for 'Scope')
- Preserve values exactly as given where possible
- If no classification found, return empty array []

Return ONLY the JSON array. No explanations, no markdown, no additional text.
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
    "summary": "brief purpose (max 100 chars)"
  },
  {
    "category": "mode_tag",
    "id": "hex code (0x4001)",
    "name": "mode tag name",
    "summary": "brief purpose (max 100 chars)"
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
    "effect": "description of resulting behavior (max 150 chars)",
    "pseudocode": "if condition then action; else action",
    "summary": "brief explanation (max 80 chars)"
  }
]

**EXTRACTION STRATEGY**:
- Parse numbered dependency subsections
- Identify involved clusters and attributes
- Extract both trigger conditions and resulting effects
- Translate narrative rules into pseudocode with clear IF/THEN/ELSE logic
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
    "summary": "brief description of the example (max 80 chars)"
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
    "summary": "status meaning (max 100 chars)",
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
    "value_rule": "how value is determined (max 120 chars)",
    "pseudocode": "event.field := derived_value"
  }
]

**EXTRACTION STRATEGY**:
- Parse narrative text describing multi-position event rules
- Group events by which field they set
- Preserve exact event and field names
- Translate descriptions into pseudocode assignments
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
    "pseudocode": "if second_press then emit InitialPress; emit MultiPressOngoing(2); later emit MultiPressComplete(2)"
  }
]

**EXTRACTION STRATEGY**:
- Parse subsections and bullet cases (single press, double press, triple press, long press, aborted sequence, etc.)
- Group scenarios by feature flag context (AS set vs unset)
- List all events generated in sequence order
- List explicitly forbidden/suppressed events
- Translate behavior into short pseudocode (with IF/THEN/ELSE, counters, event.emit)
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
    "pseudocode": "emit InitialPress"
  },
  {
    "case": "MS & MSM",
    "feature_flags": ["MS", "MSM"],
    "outcome": "Ends on LongRelease (if MSL & first press long) or MultiPressComplete",
    "notes": "AS does not change outcome; AS reduces events",
    "pseudocode": "if (first_press_long & MSL) then emit LongRelease else emit MultiPressComplete"
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
    "summary": "MoveToLevel ignored when Off and EiO=0"
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
    "summary": "MoveToLevelWithOnOff turns on device and adjusts brightness"
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
- Translate sequence into pseudocode using IF/THEN and event.emit
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
    "pseudocode": "if mode changes Idle→Cleaning then start_cleaning()"
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
    "pseudocode": "assert AbsMinHeatSetpointLimit <= MinHeatSetpointLimit <= MaxHeatSetpointLimit <= AbsMaxHeatSetpointLimit"
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
      "pseudocode": "call SetUser(UserIndex, user_fields)"
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
    "pseudocode": "on attribute_read/write: filter by accessing_fabric"
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
    "pseudocode": "if endpoint.device_type not in [NIM, TBR] then reject_interaction()"
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
    "pseudocode": "if OnTime != 0xFFFF then every 100ms: OnTime := OnTime - 1"
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


all_subsection_types = [
      "Classification",
      "Revision History",
      "Cluster ID",
      "Attributes",
      "Data Types",
      "Features",
      "Commands",
      "Events",
      "Derived Cluster Namespace",
      "Dependencies",
      "Mode Examples",
      "Status Codes",
      "Cluster IDs",
      "Definitions",
      "Conversion of Temperature Values for Display",
      "Multi Position Details",
      "Sequence of events for MultiPress",
      "Summary of cases for MS feature flag",
      "PIN/RFID Code Format",
      "State Change Table for Lighting",
      "Sequence of generated events",
      "The Dimming Light Curve",
      "Mode Use",
      "Setpoint Limits",
      "Recommended steps for creating a new User",
      "Handling of fabric-scoping",
      "State Description",
      "Mode Namespace",
      "Units of Temperature",
      "Guidance for Fabrics / Commissioners"
    ]

section_prompt_dict = {
  "Classification" : CLASSIFICATION_EXTRACTION_PROMPT,
  "Revision History" : REVISION_HISTORY_EXTRACTION_PROMPT,
  "Cluster ID" : CLUSTER_ID_EXTRACTION_PROMPT,
  "Attributes" : ATTRIBUTES_EXTRACTION_PROMPT,
  "Data Types" : DATA_TYPES_EXTRACTION_PROMPT,
  "Features" : FEATURES_EXTRACTION_PROMPT,
  "Commands" : COMMANDS_EXTRACTION_PROMPT,
  "Events" : EVENTS_EXTRACTION_PROMPT,
  "Derived Cluster Namespace" : DERIVED_CLUSTER_NAMESPACE_EXTRACTION_PROMPT,
  "Dependencies" : DEPENDENCIES_EXTRACTION_PROMPT,
  "Mode Examples" : MODE_EXAMPLES_EXTRACTION_PROMPT,
  "Status Codes" : STATUS_CODES_EXTRACTION_PROMPT,
  "Cluster IDs" : CLUSTER_ID_EXTRACTION_PROMPT,
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