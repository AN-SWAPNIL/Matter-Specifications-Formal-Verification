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
# Model name (e.g., "gpt-4", "claude-3-5-sonnet", "gemini-2.5-pro")
LLM_MODEL = "gpt-5.1"
# LangChain model provider (e.g., "openai", "anthropic", "google_genai")
MODEL_PROVIDER = "openai"
LLM_TEMPERATURE = 0.0  # More deterministic for detailed extraction
# Significantly increased for comprehensive behavioral extraction
LLM_MAX_OUTPUT_TOKENS = 32768

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
    {"name": "Identify Cluster", "section": "1.2",
        "start": 26, "end": 31, "category": "General"},
    {"name": "Groups Cluster", "section": "1.3",
        "start": 31, "end": 39, "category": "General"},
    {"name": "Scenes Management Cluster", "section": "1.4",
        "start": 39, "end": 60, "category": "General"},
    {"name": "On/Off Cluster", "section": "1.5",
        "start": 60, "end": 70, "category": "General"},
    {"name": "Level Control Cluster", "section": "1.6",
        "start": 70, "end": 85, "category": "General"},
    {"name": "Boolean State Cluster", "section": "1.7",
        "start": 85, "end": 86, "category": "General"},
    {"name": "Boolean State Configuration Cluster", "section": "1.8",
        "start": 86, "end": 92, "category": "General"},
    {"name": "Mode Select Cluster", "section": "1.9",
        "start": 92, "end": 97, "category": "General"},
    {"name": "Mode Base Cluster", "section": "1.10",
        "start": 97, "end": 106, "category": "General"},
    {"name": "Low Power Cluster", "section": "1.11",
        "start": 106, "end": 107, "category": "General"},
    {"name": "Wake On LAN Cluster", "section": "1.12",
        "start": 107, "end": 108, "category": "General"},
    {"name": "Switch Cluster", "section": "1.13",
        "start": 108, "end": 127, "category": "General"},
    {"name": "Operational State Cluster", "section": "1.14",
        "start": 127, "end": 138, "category": "General"},
    {"name": "Alarm Base Cluster", "section": "1.15",
        "start": 138, "end": 141, "category": "General"},
    {"name": "Messages Cluster", "section": "1.16",
        "start": 141, "end": 151, "category": "General"},
    {"name": "Service Area Cluster", "section": "1.17",
        "start": 151, "end": 167, "category": "General"},

    # Measurement and Sensing Clusters (Section 2)
    {"name": "Illuminance Measurement Cluster", "section": "2.2",
        "start": 173, "end": 175, "category": "Measurement and Sensing"},
    {"name": "Temperature Measurement Cluster", "section": "2.3",
        "start": 175, "end": 176, "category": "Measurement and Sensing"},
    {"name": "Pressure Measurement Cluster", "section": "2.4",
        "start": 176, "end": 179, "category": "Measurement and Sensing"},
    {"name": "Flow Measurement Cluster", "section": "2.5", "start": 179,
        "end": 181, "category": "Measurement and Sensing"},
    {"name": "Water Content Measurement Clusters", "section": "2.6",
        "start": 181, "end": 182, "category": "Measurement and Sensing"},
    {"name": "Occupancy Sensing Cluster", "section": "2.7",
        "start": 182, "end": 192, "category": "Measurement and Sensing"},
    {"name": "Resource Monitoring Clusters", "section": "2.8",
        "start": 192, "end": 197, "category": "Measurement and Sensing"},
    {"name": "Air Quality Cluster", "section": "2.9", "start": 197,
        "end": 198, "category": "Measurement and Sensing"},
    {"name": "Concentration Measurement Clusters", "section": "2.10",
        "start": 198, "end": 204, "category": "Measurement and Sensing"},
    {"name": "Smoke CO Alarm Cluster", "section": "2.11", "start": 204,
        "end": 214, "category": "Measurement and Sensing"},
    {"name": "Electrical Energy Measurement Cluster", "section": "2.12",
        "start": 214, "end": 222, "category": "Measurement and Sensing"},
    {"name": "Electrical Power Measurement Cluster", "section": "2.13",
        "start": 222, "end": 235, "category": "Measurement and Sensing"},

    # Lighting Clusters (Section 3)
    {"name": "Color Control Cluster", "section": "3.2",
        "start": 235, "end": 277, "category": "Lighting"},
    {"name": "Ballast Configuration Cluster", "section": "3.3",
        "start": 277, "end": 285, "category": "Lighting"},

    # HVAC Clusters (Section 4)
    {"name": "Pump Configuration and Control Cluster",
        "section": "4.2", "start": 285, "end": 299, "category": "HVAC"},
    {"name": "Thermostat Cluster", "section": "4.3",
        "start": 299, "end": 348, "category": "HVAC"},
    {"name": "Fan Control Cluster", "section": "4.4",
        "start": 348, "end": 357, "category": "HVAC"},
    {"name": "Thermostat User Interface Configuration Cluster",
        "section": "4.5", "start": 357, "end": 359, "category": "HVAC"},
    {"name": "Valve Configuration and Control Cluster",
        "section": "4.6", "start": 359, "end": 369, "category": "HVAC"},

    # Closures Clusters (Section 5)
    {"name": "Door Lock Cluster", "section": "5.2",
        "start": 369, "end": 449, "category": "Closures"},
    {"name": "Window Covering Cluster", "section": "5.3",
        "start": 449, "end": 469, "category": "Closures"},

    # Media Clusters (Section 6)
    {"name": "Account Login Cluster", "section": "6.2",
        "start": 471, "end": 476, "category": "Media"},
    {"name": "Application Basic Cluster", "section": "6.3",
        "start": 476, "end": 479, "category": "Media"},
    {"name": "Application Launcher Cluster", "section": "6.4",
        "start": 479, "end": 484, "category": "Media"},
    {"name": "Audio Output Cluster", "section": "6.5",
        "start": 484, "end": 487, "category": "Media"},
    {"name": "Channel Cluster", "section": "6.6",
        "start": 487, "end": 503, "category": "Media"},
    {"name": "Content Launcher Cluster", "section": "6.7",
        "start": 503, "end": 517, "category": "Media"},
    {"name": "Keypad Input Cluster", "section": "6.8",
        "start": 517, "end": 522, "category": "Media"},
    {"name": "Media Input Cluster", "section": "6.9",
        "start": 522, "end": 525, "category": "Media"},
    {"name": "Media Playback Cluster", "section": "6.10",
        "start": 525, "end": 542, "category": "Media"},
    {"name": "Target Navigator Cluster", "section": "6.11",
        "start": 542, "end": 546, "category": "Media"},
    {"name": "Content App Observer Cluster", "section": "6.12",
        "start": 546, "end": 548, "category": "Media"},
    {"name": "Content Control Cluster", "section": "6.13",
        "start": 548, "end": 567, "category": "Media"},

    # Robot Clusters (Section 7)
    {"name": "RVC Run Mode Cluster", "section": "7.2",
        "start": 567, "end": 571, "category": "Robots"},
    {"name": "RVC Clean Mode Cluster", "section": "7.3",
        "start": 571, "end": 574, "category": "Robots"},
    {"name": "RVC Operational State Cluster", "section": "7.4",
        "start": 574, "end": 579, "category": "Robots"},

    # Home Appliance Clusters (Section 8)
    {"name": "Temperature Control Cluster", "section": "8.2",
        "start": 580, "end": 584, "category": "Home Appliances"},
    {"name": "Dishwasher Mode Cluster", "section": "8.3",
        "start": 584, "end": 586, "category": "Home Appliances"},
    {"name": "Dishwasher Alarm Cluster", "section": "8.4",
        "start": 586, "end": 587, "category": "Home Appliances"},
    {"name": "Laundry Washer Mode Cluster", "section": "8.5",
        "start": 587, "end": 590, "category": "Home Appliances"},
    {"name": "Laundry Washer Controls Cluster", "section": "8.6",
        "start": 590, "end": 593, "category": "Home Appliances"},
    {"name": "Refrigerator And Temperature Controlled Cabinet Mode Cluster",
        "section": "8.7", "start": 593, "end": 595, "category": "Home Appliances"},
    {"name": "Refrigerator Alarm Cluster", "section": "8.8",
        "start": 595, "end": 597, "category": "Home Appliances"},
    {"name": "Laundry Dryer Controls Cluster", "section": "8.9",
        "start": 597, "end": 598, "category": "Home Appliances"},
    {"name": "Oven Cavity Operational State Cluster", "section": "8.10",
        "start": 598, "end": 600, "category": "Home Appliances"},
    {"name": "Oven Mode Cluster", "section": "8.11",
        "start": 600, "end": 603, "category": "Home Appliances"},
    {"name": "Microwave Oven Mode Cluster", "section": "8.12",
        "start": 603, "end": 605, "category": "Home Appliances"},
    {"name": "Microwave Oven Control Cluster", "section": "8.13",
        "start": 605, "end": 613, "category": "Home Appliances"},

    # Energy Management Clusters (Section 9)
    {"name": "Device Energy Management Cluster", "section": "9.2",
        "start": 613, "end": 650, "category": "Energy Management"},
    {"name": "Energy EVSE Cluster", "section": "9.3",
        "start": 650, "end": 677, "category": "Energy Management"},
    {"name": "Energy EVSE Mode Cluster", "section": "9.4",
        "start": 677, "end": 680, "category": "Energy Management"},
    {"name": "Water Heater Management Cluster", "section": "9.5",
        "start": 680, "end": 687, "category": "Energy Management"},
    {"name": "Water Heater Mode Cluster", "section": "9.6",
        "start": 687, "end": 690, "category": "Energy Management"},
    {"name": "Energy Preference Cluster", "section": "9.7",
        "start": 690, "end": 694, "category": "Energy Management"},
    {"name": "Device Energy Management Mode Cluster", "section": "9.8",
        "start": 694, "end": 699, "category": "Energy Management"},

    # Network Infrastructure Clusters (Section 10)
    {"name": "Wi-Fi Network Management Cluster", "section": "10.2",
        "start": 699, "end": 702, "category": "Network Infrastructure"},
    {"name": "Thread Border Router Management Cluster", "section": "10.3",
        "start": 702, "end": 707, "category": "Network Infrastructure"},
    {"name": "Thread Network Directory Cluster", "section": "10.4",
        "start": 707, "end": 712, "category": "Network Infrastructure"},
]

# AI Extraction Prompt Template
# Manual extraction configuration - no AI prompts needed


# =============================================================================
# FSM GENERATION FOR TAMARIN SECURITY ANALYSIS
# =============================================================================

FSM_GENERATION_PROMPT_TEMPLATE_PARSER = """
You are a Matter IoT protocol security expert. Generate a Finite State Machine model from a Matter Application Cluster specification that will be converted to Tamarin protocol verification code for SECURITY ANALYSIS.

CLUSTER SPECIFICATION TO ANALYZE:
{cluster_info}

================================================================================
## CRITICAL: SECURITY ANALYSIS REQUIREMENTS
================================================================================

This FSM will be used for FORMAL SECURITY VERIFICATION with Tamarin Prover.
The generated model MUST support verification of:
- Authentication properties (who performed an action)
- Authorization properties (permission checks before actions)
- Confidentiality properties (secrets not leaked)
- Rate limiting and temporal properties

================================================================================
## FSM STRUCTURE FOR TAMARIN CONVERSION
================================================================================

### CORE PRINCIPLE: EVERY SECURITY-RELEVANT EVENT MUST BE TRACEABLE

For Tamarin verification, we need:
1. **Action Facts** - Events emitted during transitions (become Tamarin action labels)
2. **Variables** - Parameters bound from inputs (become Tamarin variables)
3. **Consistency** - Security properties ONLY reference action facts that transitions emit

--------------------------------------------------------------------------------
### STRUCTURE 1: PROTOCOL MESSAGES
--------------------------------------------------------------------------------

Define all command request/response messages with their parameters:

```json
"protocol_messages": [
  {{
    "name": "GetSetupPIN_Request",
    "direction": "client_to_server",
    "fields": [
      {{"name": "temp_account_id", "type": "string", "security_relevant": true}}
    ]
  }},
  {{
    "name": "GetSetupPIN_Response",
    "direction": "server_to_client",
    "fields": [
      {{"name": "setup_pin", "type": "string", "security_relevant": true}}
    ]
  }}
]
```

**Rules:**
- Extract from cluster_info.Commands
- Mark fields as `security_relevant: true` if they contain credentials, identifiers, or secrets
- Include both request and response messages

--------------------------------------------------------------------------------
### STRUCTURE 2: ACTION FACTS (CRITICAL FOR SECURITY)
--------------------------------------------------------------------------------

Define ALL security-relevant events that can occur. These become Tamarin action labels.

```json
"action_facts": [
  {{
    "name": "GetSetupPINReceived",
    "params": ["endpoint", "temp_id"],
    "description": "Server received GetSetupPIN request"
  }},
  {{
    "name": "GetSetupPINAccepted",
    "params": ["endpoint", "temp_id"],
    "description": "GetSetupPIN passed rate limit check"
  }},
  {{
    "name": "SetupPINReturned",
    "params": ["endpoint", "temp_id", "setup_pin"],
    "description": "Non-empty SetupPIN returned to client"
  }},
  {{
    "name": "EmptyPINReturned",
    "params": ["endpoint", "temp_id"],
    "description": "Empty SetupPIN returned (mismatch or expired)"
  }},
  {{
    "name": "RateLimitExceeded",
    "params": ["endpoint", "scope"],
    "description": "Request rejected due to rate limiting"
  }},
  {{
    "name": "TempIdValidated",
    "params": ["temp_id"],
    "description": "Temporary Account Identifier confirmed not expired"
  }},
  {{
    "name": "TempIdExpired",
    "params": ["temp_id"],
    "description": "Temporary Account Identifier has expired"
  }},
  {{
    "name": "AccountLookupSuccess",
    "params": ["temp_id", "account"],
    "description": "Account found for given TempAccountIdentifier"
  }},
  {{
    "name": "AccountLookupFailed",
    "params": ["temp_id"],
    "description": "No account found for TempAccountIdentifier"
  }},
  {{
    "name": "SetupPINValidated",
    "params": ["account", "setup_pin"],
    "description": "SetupPIN confirmed valid for account"
  }},
  {{
    "name": "SetupPINInvalid",
    "params": ["account", "setup_pin"],
    "description": "SetupPIN not valid for account"
  }},
  {{
    "name": "LoginSuccess",
    "params": ["endpoint", "temp_id", "account"],
    "description": "Login completed successfully, account activated"
  }},
  {{
    "name": "LoginFailed",
    "params": ["endpoint", "temp_id", "reason"],
    "description": "Login rejected with reason"
  }},
  {{
    "name": "AccountActivated",
    "params": ["endpoint", "account"],
    "description": "Account set as active for Content App"
  }},
  {{
    "name": "NodeAccessGranted",
    "params": ["endpoint", "account", "node"],
    "description": "Node granted access to Content App"
  }},
  {{
    "name": "LogoutReceived",
    "params": ["endpoint", "node_or_null"],
    "description": "Logout command received"
  }},
  {{
    "name": "AccountDeactivated",
    "params": ["endpoint", "account"],
    "description": "Account cleared from Content App"
  }},
  {{
    "name": "NodeAccessRevoked",
    "params": ["endpoint", "account", "node"],
    "description": "Node access to Content App revoked"
  }},
  {{
    "name": "LoggedOutEvent",
    "params": ["endpoint", "node_or_null", "account"],
    "description": "LoggedOut event emitted"
  }}
]
```

**Rules:**
- Extract from effect_on_receipt pseudocode - each decision point becomes an action fact
- Include BOTH success and failure cases
- Parameters must be lowercase (Tamarin variable convention)
- Names must be CamelCase (Tamarin action fact convention)

--------------------------------------------------------------------------------
### STRUCTURE 3: TRANSITIONS WITH ACTION FACTS
--------------------------------------------------------------------------------

Each transition MUST specify which action facts it emits:

```json
"transitions": [
  {{
    "transition_id": "T1",
    "from_state": "NoActiveAccount",
    "to_state": "NoActiveAccount",
    "trigger": "GetSetupPIN",
    "guard_condition": "rate_limit_exceeded == FALSE && temp_id_valid == TRUE && account_match == TRUE",
    "input_message": {{
      "name": "GetSetupPIN_Request",
      "bindings": {{"temp_id": "temp_account_id"}}
    }},
    "output_message": {{
      "name": "GetSetupPIN_Response",
      "values": {{"setup_pin": "valid_setup_pin"}}
    }},
    "action_facts_emitted": [
      {{"name": "GetSetupPINReceived", "args": ["endpoint", "temp_id"]}},
      {{"name": "GetSetupPINAccepted", "args": ["endpoint", "temp_id"]}},
      {{"name": "TempIdValidated", "args": ["temp_id"]}},
      {{"name": "AccountLookupSuccess", "args": ["temp_id", "account"]}},
      {{"name": "SetupPINReturned", "args": ["endpoint", "temp_id", "setup_pin"]}}
    ],
    "state_updates": [
      {{"attribute": "last_temp_id", "value": "temp_id"}}
    ],
    "description": "GetSetupPIN succeeds: rate limit OK, temp_id valid, account matches"
  }},
  {{
    "transition_id": "T2",
    "from_state": "BaseOff",
    "to_state": "BaseOff",
    "trigger": "On",
    "guard_condition": "feature_OFFONLY == TRUE",
    "guard_features": [
      {{"name": "OFFONLY", "value": "TRUE"}}
    ],
    "guard_attributes": [],
    "input_message": {{
      "name": "On_Request",
      "bindings": {{}}
    }},
    "output_message": {{
      "name": "On_Response",
      "values": {{"status": "UNSUPPORTED_COMMAND"}}
    }},
    "action_facts_emitted": [
      {{"name": "OnReceived", "args": ["endpoint"]}},
      {{"name": "OnNotSupportedOffOnly", "args": ["endpoint"]}}
    ],
    "state_updates": [],
    "description": "On command rejected: OffOnly feature enabled"
  }}
]
```

**CRITICAL RULES:**
- `guard_condition` is human-readable, `guard_features` + `guard_attributes` are machine-parseable
- `guard_features`: Extract from conditions like "feature_LT == TRUE" → {{"name": "LT", "value": "TRUE"}}
- `guard_attributes`: Extract from conditions like "OnTime > 0" → {{"name": "OnTime", "operator": ">", "value": "0"}}
- If no feature/attribute guards, use empty arrays: `"guard_features": [], "guard_attributes": []`
- `action_facts_emitted` MUST list all security-relevant events for this transition
- Arguments in `args` MUST match variable names bound from input or state
- EVERY branch of conditional logic in effect_on_receipt → separate transition
- Each transition has a unique `transition_id`

--------------------------------------------------------------------------------
### STRUCTURE 4: SECURITY PROPERTIES (MUST REFERENCE DEFINED ACTION FACTS)
--------------------------------------------------------------------------------

**CRITICAL: DO NOT FABRICATE SECURITY PROPERTIES**
- If the cluster specification does NOT contain explicit security requirements (rate limits, validation checks, SHALL statements), leave `security_properties` as an EMPTY array: `"security_properties": []`
- Only create security properties when you can directly cite the source from the specification
- Never invent security requirements that are not in the specification
- It is BETTER to have an empty security_properties array than to include fabricated properties

Security properties MUST only reference action facts defined in `action_facts`:

```json
"security_properties": [
  {{
    "property_id": "SP1",
    "property_name": "rate_limit_enforced",
    "property_type": "safety",
    "description": "Accepted requests must not exceed rate limit",
    "formula_type": "requires_previous",
    "formula": {{
      "quantifier": "All",
      "variables": ["endpoint", "temp_id"],
      "trigger": {{"fact": "GetSetupPINAccepted", "args": ["endpoint", "temp_id"]}},
      "requirement": {{"fact": "RateLimitWindowActive", "args": ["endpoint"]}},
      "temporal": "before"
    }},
    "referenced_action_facts": ["GetSetupPINAccepted", "RateLimitWindowActive"],
    "source": "timing: ≤10 unique requests per 10 minutes"
  }},
  {{
    "property_id": "SP2",
    "property_name": "setup_pin_requires_valid_temp_id",
    "property_type": "authentication",
    "description": "Non-empty SetupPIN returned only if temp_id was validated",
    "formula_type": "requires_simultaneous",
    "formula": {{
      "quantifier": "All",
      "variables": ["endpoint", "temp_id", "setup_pin"],
      "trigger": {{"fact": "SetupPINReturned", "args": ["endpoint", "temp_id", "setup_pin"]}},
      "requirement": {{"fact": "TempIdValidated", "args": ["temp_id"]}},
      "temporal": "same_time"
    }},
    "referenced_action_facts": ["SetupPINReturned", "TempIdValidated"],
    "source": "effect_on_receipt: temp_id_not_expired check"
  }},
  {{
    "property_id": "SP3",
    "property_name": "login_requires_valid_credentials",
    "property_type": "authentication",
    "description": "Login success requires valid temp_id and valid setup_pin",
    "formula_type": "requires_all",
    "formula": {{
      "quantifier": "All",
      "variables": ["endpoint", "temp_id", "account"],
      "trigger": {{"fact": "LoginSuccess", "args": ["endpoint", "temp_id", "account"]}},
      "requirements": [
        {{"fact": "TempIdValidated", "args": ["temp_id"]}},
        {{"fact": "AccountLookupSuccess", "args": ["temp_id", "account"]}},
        {{"fact": "SetupPINValidated", "args": ["account", "setup_pin"]}}
      ],
      "temporal": "same_time"
    }},
    "referenced_action_facts": ["LoginSuccess", "TempIdValidated", "AccountLookupSuccess", "SetupPINValidated"],
    "source": "effect_on_receipt: Login validation steps"
  }},
  {{
    "property_id": "SP4",
    "property_name": "logout_triggers_access_revocation",
    "property_type": "authorization",
    "description": "LoggedOut event leads to access revocation",
    "formula_type": "leads_to",
    "formula": {{
      "quantifier": "All",
      "variables": ["endpoint", "node", "account"],
      "trigger": {{"fact": "LoggedOutEvent", "args": ["endpoint", "node", "account"]}},
      "consequence": {{"fact": "NodeAccessRevoked", "args": ["endpoint", "account", "node"]}},
      "temporal": "eventually_after"
    }},
    "referenced_action_facts": ["LoggedOutEvent", "NodeAccessRevoked"],
    "source": "events: Fabric Admin SHALL remove access"
  }}
]
```

**CRITICAL RULES:**
- `referenced_action_facts` MUST only contain names from the `action_facts` array
- Every fact referenced in `formula` MUST exist in `action_facts`
- Variable names in formulas MUST be lowercase
- Fact names MUST be CamelCase

--------------------------------------------------------------------------------
### STRUCTURE 5: VARIABLES AND FRESH VALUES
--------------------------------------------------------------------------------

Define which values are fresh (newly generated) vs bound from input:

```json
"variables": {{
  "fresh_values": [
    {{"name": "setup_pin", "description": "Generated Setup PIN for PASE"}},
    {{"name": "session_id", "description": "Session identifier"}}
  ],
  "input_bound": [
    {{"name": "temp_id", "source": "GetSetupPIN_Request.temp_account_id"}},
    {{"name": "provided_pin", "source": "Login_Request.setup_pin"}},
    {{"name": "node", "source": "Login_Request.node"}}
  ],
  "state_bound": [
    {{"name": "account", "source": "lookup from temp_id"}},
    {{"name": "endpoint", "source": "server endpoint identity"}}
  ]
}}
```

================================================================================
## EXTRACTION METHODOLOGY
================================================================================

### STEP 1: EXTRACT PROTOCOL MESSAGES
From `cluster_info.Commands`:
- Each command with direction "client ⇒ server" → Request message
- Each command with direction "client ⇐ server" → Response message
- Extract all fields with types

### STEP 2: IDENTIFY ACTION FACTS
From `cluster_info.Commands[].effect_on_receipt`:
- Each conditional check → action fact for pass AND fail
- Each state modification → action fact
- Each response sent → action fact
- Each event generated → action fact

Example from GetSetupPIN effect_on_receipt:
```
1. if rate_limiter.too_many_unique_requests(last_10_min) then...
   → RateLimitExceeded (fail case)
   → RateLimitOK (implicit pass case for step 2)
2. account_req := lookup_account_by_temp_id(TempAccountIdentifier);
   → AccountLookupSuccess / AccountLookupFailed
3. account_active := get_active_account_for_content_app();
4. if account_req = account_active and temp_id_not_expired...
   → TempIdValidated / TempIdExpired
   → AccountMatch / AccountMismatch
   → SetupPINReturned / EmptyPINReturned
```

### STEP 3: BUILD TRANSITIONS
For each unique execution path through effect_on_receipt:
- Create one transition
- List all action facts emitted along that path
- Specify guard conditions that select this path

### STEP 3.5: MODEL STARTUP/POWER-CYCLE BEHAVIOR (CRITICAL)
**IMPORTANT**: Many Matter clusters have power-cycle/startup behavior defined by StartUp* attributes.

**Check for these patterns in cluster_info:**
1. **StartUpOnOff attribute** (On/Off Cluster): Controls device state after power cycle
2. **StartUpCurrentLevel attribute** (Level Control): Controls level after power cycle
3. **StartUpColorTemperatureMireds** (Color Control): Controls color temp after startup
4. Any attribute with "StartUp" prefix or descriptions mentioning "power-up", "startup", "reboot"

**For each StartUp attribute found, create Startup transitions:**

Example for StartUpOnOff (On/Off Cluster):
```json
// If StartUpOnOff is null → restore previous OnOff value
{{
  "transition_id": "T_Startup_RestorePrevOn",
  "from_state": "BaseOff",
  "to_state": "BaseOn",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff_is_null == TRUE && PreviousOnOff == TRUE",
  "guard_features": [],
  "guard_attributes": [{{"name": "StartUpOnOff", "operator": "==", "value": "null"}}, {{"name": "PreviousOnOff", "operator": "==", "value": "TRUE"}}],
  "input_message": null,
  "output_message": null,
  "action_facts_emitted": [
    {{"name": "StartupOccurred", "args": ["endpoint"]}},
    {{"name": "StartupRestorePrevious", "args": ["endpoint", "TRUE"]}}
  ],
  "state_updates": [{{"attribute": "OnOff", "value": "TRUE"}}],
  "description": "Power cycle with StartUpOnOff=null restores previous ON state"
}},
// If StartUpOnOff is null → restore previous OnOff value (was OFF)
{{
  "transition_id": "T_Startup_RestorePrevOff",
  "from_state": "BaseOff",
  "to_state": "BaseOff",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff_is_null == TRUE && PreviousOnOff == FALSE",
  ...
}},
// If StartUpOnOff == Off → force OFF
{{
  "transition_id": "T_Startup_ForceOff",
  "from_state": "BaseOff",
  "to_state": "BaseOff",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == StartUpOnOffEnum_Off",
  ...
}},
// If StartUpOnOff == On → force ON
{{
  "transition_id": "T_Startup_ForceOn",
  "from_state": "BaseOff",
  "to_state": "BaseOn",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == StartUpOnOffEnum_On",
  ...
}},
// If StartUpOnOff == Toggle → toggle from previous state
{{
  "transition_id": "T_Startup_ToggleToOn",
  "from_state": "BaseOff",
  "to_state": "BaseOn",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == StartUpOnOffEnum_Toggle && PreviousOnOff == FALSE",
  ...
}},
{{
  "transition_id": "T_Startup_ToggleToOff",
  "from_state": "BaseOff",
  "to_state": "BaseOff",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == StartUpOnOffEnum_Toggle && PreviousOnOff == TRUE",
  ...
}}
```

**Action Facts for Startup:**
- Add `StartupOccurred` action fact: {{"name": "StartupOccurred", "params": ["endpoint"], "description": "Device powered on/rebooted"}}
- Add specific startup behavior facts (e.g., `StartupRestorePrevious`, `StartupForceOn`, `StartupForceOff`, `StartupToggle`)

**Rules:**
- Startup transitions have trigger = "Startup" (not a command, an internal event)
- from_state is typically the initial state (e.g., "BaseOff")
- to_state depends on StartUp attribute value and previous state
- input_message and output_message are null (no client command)
- Create one transition for each possible StartUp enum value or null case
- Include PreviousOnOff (or equivalent) in guards when behavior depends on prior state

### STEP 4: DERIVE SECURITY PROPERTIES
From `cluster_info.Commands[].timing`:
- Rate limit requirements → safety properties

From `cluster_info.Commands[].effect_on_receipt`:
- Validation checks → authentication properties

From `cluster_info.Events[].summary`:
- SHALL requirements → authorization/safety properties

From `cluster_info.Commands[].access`:
- Access control levels → authorization properties

### STEP 5: VALIDATE CONSISTENCY
Before outputting:
1. Every fact in `security_properties.referenced_action_facts` EXISTS in `action_facts`
2. Every `action_facts_emitted` item in transitions references a defined action fact
3. All variable names are lowercase, all fact names are CamelCase
4. No action fact is defined but never emitted by any transition

================================================================================
## OUTPUT JSON STRUCTURE
================================================================================

**CRITICAL JSON REQUIREMENTS:**
- Output ONLY valid JSON (no markdown, no comments)
- NO trailing commas
- Validate before outputting

```json
{{
  "fsm_model": {{
    "cluster_name": "string",
    "cluster_id": "hex_string",
    "revision": "number",
    "category": "string",
    
    "features": [
      {{"name": "FEATURE_NAME", "full_name": "Full Feature Name", "description": "string"}}
    ],
    
    "protocol_messages": [
      {{
        "name": "string",
        "direction": "client_to_server | server_to_client",
        "command_id": "hex_string",
        "fields": [
          {{"name": "string", "type": "string", "security_relevant": boolean}}
        ]
      }}
    ],
    
    "action_facts": [
      {{
        "name": "CamelCase",
        "params": ["lowercase_param1", "lowercase_param2"],
        "description": "string"
      }}
    ],
    
    "states": [
      {{
        "name": "string",
        "description": "string",
        "is_initial": boolean,
        "invariants": ["string"]
      }}
    ],
    
    "transitions": [
      {{
        "transition_id": "T1",
        "from_state": "string",
        "to_state": "string",
        "trigger": "string",
        "guard_condition": "string",
        "guard_features": [{{"name": "FEATURE", "value": "TRUE | FALSE"}}],
        "guard_attributes": [{{"name": "attr", "operator": "== | != | > | <", "value": "val"}}],
        "input_message": {{
          "name": "string",
          "bindings": {{"var_name": "field_name"}}
        }},
        "output_message": {{
          "name": "string",
          "values": {{"field_name": "value_or_var"}}
        }},
        "action_facts_emitted": [
          {{"name": "CamelCase", "args": ["var1", "var2"]}}
        ],
        "state_updates": [
          {{"attribute": "string", "value": "string"}}
        ],
        "description": "string"
      }}
    ],
    
    "initial_state": "string",
    
    "variables": {{
      "fresh_values": [{{"name": "string", "description": "string"}}],
      "input_bound": [{{"name": "string", "source": "string"}}],
      "state_bound": [{{"name": "string", "source": "string"}}]
    }},
    
    "security_properties": [
      {{
        "property_id": "SP1",
        "property_name": "snake_case",
        "property_type": "safety | authentication | authorization | secrecy",
        "description": "string",
        "formula_type": "requires_previous | requires_simultaneous | requires_all | leads_to | never | always",
        "formula": {{
          "quantifier": "All | Ex",
          "variables": ["string"],
          "trigger": {{"fact": "CamelCase", "args": ["var"]}},
          "requirement": {{"fact": "CamelCase", "args": ["var"]}},
          "temporal": "before | same_time | eventually_after"
        }},
        "referenced_action_facts": ["CamelCase"],
        "source": "string"
      }}
    ],
    
    "commands_handled": ["string"],
    "events_generated": ["string"],
    
    "metadata": {{
      "fsm_version": "2.0",
      "tamarin_compatible": true,
      "section_number": "string"
    }}
  }}
}}
```

================================================================================
## VALIDATION CHECKLIST (MUST ALL PASS)
================================================================================

- [ ] Features section lists all feature flags from specification
- [ ] Every guard_features entry references a defined feature
- [ ] Guard conditions with "feature_X" have corresponding guard_features entry
- [ ] Guard conditions with "attr op value" have corresponding guard_attributes entry
- [ ] Every action fact in security_properties.referenced_action_facts exists in action_facts
- [ ] Every action_facts_emitted in transitions references a defined action fact
- [ ] All variable names are lowercase
- [ ] All action fact names are CamelCase
- [ ] Every conditional branch in effect_on_receipt has a corresponding transition
- [ ] Both success and failure paths have action facts
- [ ] No action fact defined but never used
- [ ] JSON is valid with no trailing commas
- [ ] No markdown code blocks in output
- [ ] Security properties are ONLY from specification - if no security details exist, security_properties is EMPTY array

================================================================================
## EXAMPLE: MINIMAL CORRECT OUTPUT
================================================================================

For a simple cluster with one command:

```json
{{
  "fsm_model": {{
    "cluster_name": "Example",
    "cluster_id": "0x0001",
    "revision": 1,
    "category": "Example",
    "protocol_messages": [
      {{"name": "Cmd_Request", "direction": "client_to_server", "command_id": "0x00", "fields": [{{"name": "param", "type": "string", "security_relevant": true}}]}}
    ],
    "action_facts": [
      {{"name": "CmdReceived", "params": ["endpoint", "param"], "description": "Command received"}},
      {{"name": "CmdSuccess", "params": ["endpoint", "param"], "description": "Command succeeded"}}
    ],
    "states": [
      {{"name": "Idle", "description": "Initial state", "is_initial": true, "invariants": []}}
    ],
    "transitions": [
      {{
        "transition_id": "T1",
        "from_state": "Idle",
        "to_state": "Idle",
        "trigger": "Cmd",
        "guard_condition": "TRUE",
        "input_message": {{"name": "Cmd_Request", "bindings": {{"param": "param"}}}},
        "output_message": {{"name": "Cmd_Response", "values": {{}}}},
        "action_facts_emitted": [
          {{"name": "CmdReceived", "args": ["endpoint", "param"]}},
          {{"name": "CmdSuccess", "args": ["endpoint", "param"]}}
        ],
        "state_updates": [],
        "description": "Command processed"
      }}
    ],
    "initial_state": "Idle",
    "variables": {{
      "fresh_values": [],
      "input_bound": [{{"name": "param", "source": "Cmd_Request.param"}}],
      "state_bound": [{{"name": "endpoint", "source": "server identity"}}]
    }},
    "security_properties": [
      {{
        "property_id": "SP1",
        "property_name": "cmd_received_before_success",
        "property_type": "safety",
        "description": "Success requires receipt",
        "formula_type": "requires_simultaneous",
        "formula": {{
          "quantifier": "All",
          "variables": ["endpoint", "param"],
          "trigger": {{"fact": "CmdSuccess", "args": ["endpoint", "param"]}},
          "requirement": {{"fact": "CmdReceived", "args": ["endpoint", "param"]}},
          "temporal": "same_time"
        }},
        "referenced_action_facts": ["CmdSuccess", "CmdReceived"],
        "source": "basic protocol flow"
      }}
    ],
    "commands_handled": ["Cmd"],
    "events_generated": [],
    "metadata": {{"fsm_version": "2.0", "tamarin_compatible": true, "section_number": "1.1"}}
  }}
}}
```

================================================================================

Now generate the FSM model for the provided cluster specification.
Output ONLY the JSON, no explanation, no markdown blocks.
"""


FSM_GENERATION_PROMPT_TEMPLATE_LLM = """
You are a Matter IoT protocol expert generating precise Finite State Machine models from Matter Application Cluster specifications.

CLUSTER SPECIFICATION TO ANALYZE:
{cluster_info}

---
## UNIVERSAL FSM GENERATION APPROACH

### STEP 1: CLUSTER BEHAVIORAL ANALYSIS
- **Attribute-driven states**: States from meaningful attribute value combinations
- **Command semantics**: Extract "effect_on_receipt" descriptions  
- **Timer-based transitions**: Identify countdown timers and automatic state changes
- **Conditional logic**: Commands with if/then/else → multiple transitions with exclusive guards
- **Feature constraints**: Only use features defined in specification
- **Data type integration**: Use enums for state values, bitmaps for feature checks

### STEP 2: STATE IDENTIFICATION
- States represent actual device behavior, not internal processing
- Use attribute values to determine state invariants
- Include timer states for countdown attributes
- Model fault/error states if specified
- Ensure states reflect physical/logical device condition
- Example: "MovingToLevel" (RemainingTime > 0), "IdleOn" (RemainingTime == 0 && OnOff == true)

### STEP 3: TRANSITION MODELING
- Parse "effect_on_receipt" for exact behavioral steps
- **Split conditional commands**: Each if/else branch → separate transition with unique guard
- **Model timer expiry**: Automatic transitions when timer reaches zero
- **Include guard conditions**: Data type constraints, feature flags, attribute ranges
- **Set response_command to null** (Application Cluster specification)
- **Model event generation**: Add events in transition actions when specified
- **Handle scene behaviors**: Model scene store/recall for scene-capable attributes
- **Include stay transitions**: State continuation for timer extensions/resets
- **Enforce feature constraints**: Block commands when features prohibit execution

### STEP 4: ACTION REQUIREMENTS (TAMARIN-COMPATIBLE)
**Actions MUST be atomic:**
- Simple assignments: `CurrentLevel := TargetLevel`
- Event generation: `generate_event(EventName)`
- Function calls from definitions: `apply_options(tempOptions)`

**NO Control Flow in Actions:**
- ❌ WRONG: `["if x then y := 1 else y := 0"]`
- ❌ WRONG: `["for each item in list, set value"]`
- ✅ CORRECT: Split into separate transitions with guard conditions

**All Conditionals → Guard Conditions:**
- ❌ Action: `"if Rate != 0 then start_movement()"`
- ✅ Guard: `"Rate != 0"`, Action: `["start_movement()"]`
- ✅ Add second transition with Guard: `"Rate == 0"` to handle the else case

### STEP 5: DEFINITION REQUIREMENTS (TAMARIN-COMPATIBLE)
**NO Control Flow in Definitions:**
- ❌ WRONG: "if Rate != null then use Rate, else use DefaultRate"
- ❌ WRONG: "for each bit in OptionsBitmap, apply it"
- ✅ CORRECT: "EffectiveRate: The rate value determined by Rate parameter, DefaultMoveRate attribute, or MAX_PRACTICAL_RATE constant"

**Definitions are Term/Concept Explanations:**
- Explain domain terms and constants
- Describe complex attribute behaviors (but NOT algorithms)
- Document helper functions referenced in actions
- Use plain English + minimal notation

**Examples:**
- ✅ "TargetLevel: The desired level for the device, clamped within [MinLevel, MaxLevel] range"
- ✅ "RemainingTime: Countdown timer (in 1/10 second units) indicating movement duration until completion"
- ✅ "DerivedTransitionTime: Effective duration obtained from TransitionTime parameter, OnOffTransitionTime attribute, or default if neither provided"

### STEP 6: ADVANCED BEHAVIORAL MODELING
Enhance FSM with detailed cluster information:
- **Data Type Integration**: Use extracted enums for state values, bitmaps for feature validation
- **Quality Flag Handling**: Model read-only vs read-write attribute behaviors
- **Constraint Validation**: Apply attribute constraints as state invariants
- **Feature Enforcement**: Add guard conditions that respect feature flags and limitations
- **Timer Decrement Logic**: Model internal timer decrements with appropriate resolution
- **Event-Driven Transitions**: Model transitions triggered by cluster events
- **Scene Capability**: Include scene store/recall behaviors for scene-capable attributes
- **Fabric Sensitivity**: Model fabric-scoped attribute access patterns

### STEP 7: TIMER SEMANTICS
- Model timer countdown behavior with correct resolution
- Create timer expiry transitions (timer == 0)
- Include internal timer decrement (stay transitions with timer > 0)
- Distinguish timer types and resolutions
- Model timer start/stop logic in command actions
- Model timer reset/extension behaviors

### STEP 8: FEATURE VALIDATION
- Only use features explicitly defined in specification
- Model feature-dependent command availability with guard conditions
- Block prohibited commands via guards
- Never invent non-existent features
- Enforce feature limitations in transitions

### STEP 9: TRANSITION DECOMPOSITION (CRITICAL)
**Conditional Logic Splitting:**
Example from LevelControl:
```
FSM Spec: "If ExecuteIfOff == 1 AND OnOff == false, move level. Else if ExecuteIfOff == 0, no effect."
```
Split into **TWO transitions:**
1. Guard: "ExecuteIfOff == 1 && OnOff == false" → Actions: ["TargetLevel := value"]
2. Guard: "ExecuteIfOff == 0 && OnOff == false" → Actions: ["send_response(SUCCESS)"] (no state change)

**Loop Handling:**
- ❌ Action: "for each bit in OptionsBitmap, set corresponding flag"
- ✅ Create function in definitions: `apply_options(bitmap)` → returns processed state
- ✅ Action: `["tempOptions := apply_options(...)"]`

---
## ANALYSIS METHODOLOGY (15-STEP PROCEDURE)

1. **Identify cluster type**: state-based, timer-driven, mode-based, measurement, etc.
2. **Extract key attributes**: Attributes that define operational states (consider quality flags: read-only, reportable, writable)
3. **Analyze command effects**: Parse "effect_on_receipt" for precise behavioral logic including conditional branches
4. **Integrate data types**: Use enums for state values, bitmaps for feature checks, structures for complex data
5. **Map states**: Create meaningful attribute combinations with proper invariants
6. **Model conditional branches**: Each if/else in spec → separate transition with data type validation
7. **Split complex actions**: Break down if/else and loops into multiple transitions with guards
8. **Add timer transitions**: Include both expiry (timer == 0) and stay transitions (timer > 0, decrement)
9. **Include event modeling**: Add event generation and event-driven transitions
10. **Model scene behaviors**: Include scene store/recall for scene-capable attributes
11. **Add stay transitions**: Include state continuation for timer extensions and command repetitions
12. **Enforce feature constraints**: Add guard conditions that block prohibited commands
13. **Create definitions**: Document all technical terms, functions, and domain-specific concepts
14. **Validate against spec**: Ensure all features and constraints are correctly represented
15. **Ensure complete coverage**: All commands, events, and data type interactions included

---
## OUTPUT STRUCTURE

**CRITICAL JSON REQUIREMENTS:**
- Output ONLY valid JSON
- NO markdown code blocks (```json or ```)
- NO comments in JSON (no // or #)
- NO trailing commas
- Validate JSON structure before outputting

Return raw JSON only:

{{
  "fsm_model": {{
    "cluster_name": "string",
    "cluster_id": "hex_string",
    "category": "string",
    "states": [
      {{
        "name": "state_name",
        "description": "behavioral_summary",
        "is_initial": boolean,
        "invariants": ["attr constraints"],
        "attributes_monitored": ["relevant_attributes"]
      }}
    ],
    "transitions": [
      {{
        "from_state": "source",
        "to_state": "target",
        "trigger": "command_or_timer_or_event",
        "guard_condition": "boolean_expr (use && OR condition || OR syntax)",
        "actions": ["attr := value", "generate_event(name)", "function_call()"],
        "response_command": null,
        "timing_requirements": "string_or_null"
      }}
    ],
    "initial_state": "state_name",
    "attributes_used": ["attr1", "attr2", ...],
    "commands_handled": ["cmd1", "cmd2", ...],
    "events_generated": ["event1", "event2", ...],
    "data_types_used": ["enum_type", "bitmap_type", ...],
    "scene_behaviors": ["scene_store_details", "scene_recall_details"],
    "definitions": [
      {{
        "term": "concept_name",
        "definition": "plain_english_explanation_no_pseudocode",
        "usage_context": "where_used_in_fsm"
      }}
    ],
    "references": [
      {{
        "id": "id_or_null",
        "name": "cluster_or_spec_name",
        "description": "reason_for_dependency"
      }}
    ],
    "metadata": {{
      "generation_timestamp": "ISO_8601",
      "generation_attempts": 1,
      "judge_approved": true,
      "source_pages": "string",
      "section_number": "string"
    }}
  }}
}}

---
## VALIDATION CHECKLIST

- [ ] No if/then/else in actions
- [ ] No loops in actions
- [ ] No if/then/else in definitions
- [ ] All conditional logic split into separate transitions
- [ ] Guard conditions cover all branching (mutually exclusive or exhaustive)
- [ ] Timer states correctly modeled (both expiry and stay transitions)
- [ ] Feature constraints enforced in guards
- [ ] Quality flags (read-only, writable, reportable) considered in attribute modeling
- [ ] Constraint validation applied in state invariants
- [ ] Event-driven transitions included
- [ ] Scene behaviors included if applicable
- [ ] All attributes in states are referenced in attributes_used
- [ ] All commands in transitions are in commands_handled
- [ ] Data type enums/bitmaps applied in guards
- [ ] Definitions explain terms clearly (no algorithms)
- [ ] References properly document external dependencies
- [ ] Metadata complete and accurate
- [ ] JSON is valid and parseable
- [ ] NO markdown code blocks in output
- [ ] NO comments (// or #) in JSON
- [ ] response_command is null in ALL transitions

---
## CRITICAL REMINDERS

1. **Tamarin Compatibility**: This FSM will be converted to Tamarin. Actions must be atomic.
2. **Specification Accuracy**: Adhere strictly to provided text. Do not hallucinate features.
3. **Completeness**: Cover all commands, events, timers, and feature combinations.
4. **Clarity**: States and transitions should be self-documenting.
5. **Data Type Usage**: Apply enums, bitmaps, and constraints from specification.
6. **Quality Flags**: Model read-only, writable, and reportable attribute behaviors.
7. **Fabric Sensitivity**: Consider fabric-scoped attributes where applicable.
"""


# =============================================================================
# PARSER-OPTIMIZED FSM GENERATION PROMPT (Rule-Based Tamarin Conversion)
# =============================================================================
# This prompt enhances the base FSM generation with parser-friendly constraints.
# Use this when generating FSMs for rule-based Tamarin conversion.
# Maintains generalization while adding structure for easier parsing.

FSM_GENERATION_PARSER_OPTIMIZED_PROMPT = """
You are a Matter IoT protocol expert generating Finite State Machine models optimized for RULE-BASED parsing to Tamarin protocol code.

CLUSTER SPECIFICATION TO ANALYZE:
{cluster_info}

---
## CORE DESIGN PRINCIPLE

**PREFER EXPLICITNESS OVER ABSTRACTION**: When complexity arises, consider adding states rather than complex expressions.

The cluster specification already provides:
- Attribute types, defaults, and constraints in "Attributes" section
- Command behavior in "effect_on_receipt" descriptions
- Data type enumerations in "Data Types" section
- Feature flags in "Features" section

Your FSM should leverage this information to create parser-friendly structures.

---
## PARSER-FRIENDLY FSM GUIDELINES

### GUIDELINE 1: LEVERAGE CLUSTER ATTRIBUTE METADATA
**Extract attribute information from cluster specification's "Attributes" section.**

The cluster spec provides:
- `type`: bool, uint8, uint16, enum, bitmap, etc.
- `default`: Initial value
- `constraint`: Value constraints
- `conformance`: When attribute is present (M=mandatory, O=optional, feature-dependent)

✅ Use this to understand attribute domains and initial values.

### GUIDELINE 2: EXPLICIT INVARIANTS WITH CLEAR SEMANTICS
**State invariants should be parseable expressions.**

✅ GOOD (parser can handle):
```json
"invariants": [
  "OnOff == FALSE",
  "OnTime == 0 || OnTime == 0xFFFF",
  "feature_LT == TRUE"
]
```

⚠️ ACCEPTABLE (may need splitting for complex parsers):
```json
"invariants": [
  "OnOff == TRUE",
  "OnTime > 0 && OnTime < 0xFFFF"
]
```

❌ TOO ABSTRACT (avoid):
```json
"invariants": [
  "device is in intermediate transition state",
  "waiting for external confirmation"
]
```

### GUIDELINE 3: SIMPLE ASSIGNMENT ACTIONS
**Actions should be atomic assignments. Complex operations can be abstracted.**

✅ GOOD:
```json
"actions": [
  "OnOff := FALSE",
  "OnTime := 0"
]
```

✅ ACCEPTABLE (can be abstracted by parser):
```json
"actions": [
  "OnTime := OnTimeField",
  "OffWaitTime := OffWaitTimeField"
]
```

⚠️ NEEDS CARE (parser may need to abstract):
```json
"actions": [
  "OnTime := max(OnTime, OnTimeField)"
]
```
*For such cases, add clarification in timing_requirements or definitions*

❌ AVOID:
```json
"actions": [
  "if OnTime > 0 then decrement OnTime",
  "for each bit in bitmap set corresponding flag"
]
```

### GUIDELINE 4: GUARD CONDITIONS - BALANCE SIMPLICITY AND COMPLETENESS
**Guards can use boolean operators, but very complex expressions may warrant state splitting.**

✅ SIMPLE (ideal):
```json
"guard_condition": "OnOff == FALSE"
"guard_condition": "feature_LT == TRUE"
```

✅ MODERATE (acceptable):
```json
"guard_condition": "feature_LT == TRUE && GlobalSceneControl == FALSE"
"guard_condition": "OnTime != 0 && OnTime != 0xFFFF"
```

⚠️ COMPLEX (consider splitting if parser struggles):
```json
"guard_condition": "feature_LT == TRUE && !(OnTime == 0 && OffWaitTime > 0)"
```

**If a guard becomes very complex, consider:**
- Splitting into multiple transitions from different states
- Creating intermediate states that capture sub-conditions

### GUIDELINE 5: FEATURE FLAGS AS PART OF STATE SPACE
**When features significantly change behavior, consider feature-specific states.**

Example: Lighting feature (feature_LT) enables OnTime/OffWaitTime behavior

✅ OPTION 1 - Feature in guards (compact):
```json
{{
  "name": "On_Idle",
  "invariants": ["OnOff == TRUE"],
  "transitions": [
    {{
      "trigger": "Off",
      "guard_condition": "feature_LT == TRUE",
      "actions": ["OnOff := FALSE", "OnTime := 0"]
    }},
    {{
      "trigger": "Off",
      "guard_condition": "feature_LT == FALSE",
      "actions": ["OnOff := FALSE"]
    }}
  ]
}}
```

✅ OPTION 2 - Feature in state space (more explicit):
```json
{{
  "name": "On_Idle_WithLighting",
  "invariants": ["OnOff == TRUE", "feature_LT == TRUE"]
}},
{{
  "name": "On_Idle_NoLighting",
  "invariants": ["OnOff == TRUE", "feature_LT == FALSE"]
}}
```

Choose based on:
- Feature impact: High impact → separate states
- Transition count: Many feature-dependent transitions → separate states
- Clarity: Which makes behavior clearer?

### GUIDELINE 6: TIMER MODELING FOR PARSING
**Timers are common in Matter clusters. Model them clearly.**

For timer attributes (e.g., OnTime, OffWaitTime):

✅ DISCRETE TIMER VALUES:
```json
{{
  "name": "Timed_On",
  "invariants": ["OnOff == TRUE", "OnTime > 0", "OnTime != 0xFFFF"],
  "description": "Timer actively counting down"
}},
{{
  "name": "On_Idle",
  "invariants": ["OnOff == TRUE", "OnTime == 0"],
  "description": "Timer expired or not set"
}},
{{
  "name": "On_TimerDisabled",
  "invariants": ["OnOff == TRUE", "OnTime == 0xFFFF"],
  "description": "Timer disabled (sentinel value)"
}}
```

✅ TIMER TRANSITIONS:
```json
{{
  "from_state": "Timed_On",
  "to_state": "Timed_On",
  "trigger": "OnWithTimedOff_timer_tick",
  "guard_condition": "OnTime > 1",
  "actions": [],
  "timing_requirements": "Timer decrements by 1 each 0.1s; parser models as abstract state transition"
}},
{{
  "from_state": "Timed_On",
  "to_state": "Off_Idle",
  "trigger": "OnWithTimedOff_timer_expiry",
  "guard_condition": "OnTime == 1",
  "actions": ["OnTime := 0", "OffWaitTime := 0", "OnOff := FALSE"],
  "timing_requirements": "Timer reaches 0, transition to off"
}}
```

**Note**: Parser may abstract timer decrements. Focus on modeling state changes at key timer values (0, >0, 0xFFFF).

### GUIDELINE 6.5: STARTUP/POWER-CYCLE TRANSITIONS (CRITICAL)
**Many Matter clusters define power-cycle behavior via StartUp* attributes.**

**Detection**: Look for attributes starting with "StartUp" in cluster specification:
- `StartUpOnOff` (On/Off Cluster) - controls on/off state after power cycle
- `StartUpCurrentLevel` (Level Control) - controls level after power cycle
- `StartUpColorTemperatureMireds` (Color Control) - controls color temp after startup

**Modeling Requirements:**
1. Create transitions with `trigger: "Startup"` (internal event, not a command)
2. Model ALL possible StartUp enum values (Off, On, Toggle, null/previous)
3. Use `from_state` as initial state, `to_state` depends on StartUp value
4. Set `input_message: null` and `output_message: null` (no client interaction)

**Example for OnOff Cluster with StartUpOnOff:**
```json
// StartUpOnOff is null - restore previous ON state
{{
  "from_state": "BaseOff",
  "to_state": "BaseOn",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff_is_null == TRUE && PreviousOnOff == TRUE",
  "guard_features": [],
  "guard_attributes": [{{"name": "StartUpOnOff", "operator": "==", "value": "null"}}],
  "input_message": null,
  "output_message": null,
  "action_facts_emitted": [
    {{"name": "StartupOccurred", "args": ["endpoint"]}},
    {{"name": "StartupRestorePrevious", "args": ["endpoint", "on"]}}
  ],
  "state_updates": [{{"attribute": "OnOff", "value": "TRUE"}}],
  "description": "Power cycle restores previous ON state (StartUpOnOff=null)"
}},
// StartUpOnOff is null - restore previous OFF state  
{{
  "from_state": "BaseOff",
  "to_state": "BaseOff",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff_is_null == TRUE && PreviousOnOff == FALSE",
  ...
}},
// StartUpOnOff = Off - force device OFF
{{
  "from_state": "BaseOff",
  "to_state": "BaseOff",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == Off",
  ...
}},
// StartUpOnOff = On - force device ON
{{
  "from_state": "BaseOff",
  "to_state": "BaseOn",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == On",
  ...
}},
// StartUpOnOff = Toggle - toggle from previous (was OFF → ON)
{{
  "from_state": "BaseOff",
  "to_state": "BaseOn",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == Toggle && PreviousOnOff == FALSE",
  ...
}},
// StartUpOnOff = Toggle - toggle from previous (was ON → OFF)
{{
  "from_state": "BaseOff",
  "to_state": "BaseOff",
  "trigger": "Startup",
  "guard_condition": "StartUpOnOff == Toggle && PreviousOnOff == TRUE",
  ...
}}
```

**Action Facts for Startup:**
Add these to `action_facts` when cluster has StartUp behavior:
```json
{{"name": "StartupOccurred", "params": ["endpoint"], "description": "Device completed power-on sequence"}},
{{"name": "StartupRestorePrevious", "params": ["endpoint", "previous_state"], "description": "StartUp restored previous state"}},
{{"name": "StartupForceOn", "params": ["endpoint"], "description": "StartUp forced device ON"}},
{{"name": "StartupForceOff", "params": ["endpoint"], "description": "StartUp forced device OFF"}},
{{"name": "StartupToggle", "params": ["endpoint", "new_state"], "description": "StartUp toggled device state"}}
```

**If NO StartUp attribute exists**: No Startup transitions needed for that cluster.

### GUIDELINE 7: FUNCTION CALLS AND ABSTRACTIONS
**Some commands involve external interactions (e.g., scene management).**

✅ MODEL AS STATE EFFECT with explanation:
```json
{{
  "from_state": "On_Idle",
  "to_state": "Off_SceneStored",
  "trigger": "OffWithEffect",
  "guard_condition": "GlobalSceneControl == TRUE",
  "actions": [
    "GlobalSceneControl := FALSE",
    "OnOff := FALSE"
  ],
  "timing_requirements": "Global scene stored before turning off"
}},

// In definitions:
{{
  "term": "Off_SceneStored",
  "definition": "State after OffWithEffect stores global scene. Represents: store_global_scene() was called. Parser abstracts actual scene storage.",
  "usage_context": "Enables proper scene recall behavior"
}}
```

**Principle**: State transitions capture the effect, definitions explain the abstraction.

### GUIDELINE 8: RESPONSE_COMMAND FIELD
**CRITICAL: Always set response_command to null in all transitions.**

Application Cluster specification does not define response commands in transition modeling.

```json
"response_command": null  // ALWAYS null - no exceptions
```

### GUIDELINE 9: SECURITY PROPERTIES (STRUCTURED FORMAT)
**Extract security requirements as structured event patterns - NO Tamarin code.**

**Sources:**
1. **timing**: Rate limits, expiry constraints
2. **access**: Access control requirements  
3. **effect_on_receipt**: Authentication/authorization checks
4. **events**: Mandatory behaviors (SHALL requirements)

**Property Types:**
- **safety**: Bad thing never happens
- **liveness**: Good thing eventually happens
- **secrecy**: Attacker never learns
- **authentication**: Identity verified before action
- **authorization**: Permission required for access

**Event Pattern Types (Structured - Parser converts to Tamarin):**

1. **happens**: Something occurs in execution
   - Fields: `type`, `event`, `params`
2. **never**: Event must not occur
   - Fields: `type`, `event`, `params`
3. **requires_previous**: Event requires prior event
   - Fields: `type`, `trigger_event`, `trigger_params`, `required_event`, `required_params`
4. **conditional**: Event under condition implies consequence
   - Fields: `type`, `trigger_event`, `trigger_params`, `condition`, `consequence`

**Extraction Strategy:**
- Scan `timing` for rate limits → **safety property** (no more than N requests)
- Scan `timing` for expiry → **safety property** (credentials expire after T)
- Scan `access` for privilege levels → **authorization property** (command requires level L)
- Scan `effect_on_receipt` for validation checks → **authentication/authorization properties**
- Scan event `summary` for "SHALL" requirements → **safety/authorization properties**
- Extract from references if security-critical (PASE, ACL, etc.)

**Format Requirements:**
- `property_id`: Unique identifier (SP1, SP2, ...)
- `property_name`: Snake_case name for Tamarin lemma
- `property_type`: One of 5 types above
- `description`: Clear natural language (max 200 chars)
- `constraint_type`: "universal" (All) or "existential" (Ex)
- `event_pattern`: Structured pattern - **MUST match field requirements for pattern type!**
- `source`: Where in cluster_details this was extracted from

**CRITICAL - Pattern Field Requirements:**
- `happens`/`never`: Use `event` + `params`
- `requires_previous`: Use `trigger_event` + `trigger_params` + `required_event` + `required_params`
- `conditional`: Use `trigger_event` + `trigger_params` + `condition` + `consequence`

**Examples (Structured Event Pattern - Parser Converts):**
```json
// Example 1: Something must happen
{{
  "property_id": "SP1",
  "property_name": "credential_validated_on_login",
  "property_type": "authentication",
  "description": "Login requires credential validation",
  "constraint_type": "universal",
  "event_pattern": {{
    "type": "requires_previous",
    "trigger_event": "LoginSuccess",
    "trigger_params": ["user"],
    "required_event": "CredentialValidated",
    "required_params": ["user"]
  }},
  "source": "effect_on_receipt: validate credentials before login"
}}

// Example 2: Something must never happen
{{
  "property_id": "SP2",
  "property_name": "no_empty_pin_returned",
  "property_type": "secrecy",
  "description": "Empty PIN never sent if account found",
  "constraint_type": "universal",
  "event_pattern": {{
    "type": "never",
    "event": "SendEmptyPINWhenAccountExists",
    "params": ["account"]
  }},
  "source": "effect_on_receipt: return empty if no match"
}}

// Example 3: Temporal constraint
{{
  "property_id": "SP3",
  "property_name": "rate_limit_enforced",
  "property_type": "safety",
  "description": "Rate limit enforced before accepting request",
  "constraint_type": "universal",
  "event_pattern": {{
    "type": "requires_previous",
    "trigger_event": "RequestAccepted",
    "trigger_params": ["scope"],
    "required_event": "WindowStarted",
    "required_params": ["scope"]
  }},
  "source": "timing: ≤10 unique requests per window"
}}
```

**If No Security Properties:**
- If cluster has NO security-critical requirements (e.g., simple on/off control), set `"security_properties": []`
- Do NOT invent security properties that aren't in the specification

### GUIDELINE 10: ARITHMETIC AND COMPLEX EXPRESSIONS
**When commands involve arithmetic (max, min, etc.), document clearly.**

❌ NOT PARSEABLE DIRECTLY:
```json
"actions": ["OnTime := max(OnTime, OnTimeField)"]
```

✅ PARSER-FRIENDLY APPROACH:
```json
// Split into two transitions
{{
  "from_state": "Timed_On",
  "to_state": "Timed_On_Extended",
  "trigger": "OnWithTimedOff",
  "guard_condition": "OnTimeField > OnTime",
  "actions": ["OnTime := OnTimeField"],
  "timing_requirements": "Extend timer when new value is greater"
}},
{{
  Simple clusters (OnOff) have `"security_properties": []`**
**Do NOT invent properties not in specification**
  "guard_condition": "OnTimeField <= OnTime",
  "actions": [],
  "timing_requirements": "Keep current timer when new value is not greater"
}}
```

**OR** document as abstract operation:
```json
{{
  "actions": ["OnTime := max(OnTime, OnTimeField)"],
  "timing_requirements": "Parser models max() as: if OnTimeField > OnTime, use OnTimeField; else keep OnTime"
}}
```

---
## ENHANCED OUTPUT STRUCTURE

**CRITICAL JSON REQUIREMENTS:**
- Output ONLY valid JSON
- NO markdown code blocks (```json or ```)
- NO comments in JSON
- NO trailing commas
- Validate JSON structure before outputting

Use the standard FSM structure with these enhancements:

```json
{{
  "fsm_model": {{"
    "cluster_name": "string",
    "cluster_id": "hex_string",
    "category": "string",
    
    "states": [
      {{
        "name": "state_name",
        "description": "Clear behavioral description",
        "is_initial": boolean,
        "invariants": ["parseable_expression"],
        "attributes_monitored": ["attr1", "attr2"]
      }}
    ],
    
    "transitions": [
      {{
        "from_state": "source",
        "to_state": "target",
        "trigger": "command_or_event",
        "guard_condition": "simple_or_moderate_expression",
        "actions": ["attr := value"],
        "response_command": null,
        "timing_requirements": "string_or_null (explain abstractions here)",
        "description": "what_this_transition_represents"
      }}
    ],
    
    "initial_state": "state_name",
    "attributes_used": ["attr1", "attr2"],
    "commands_handled": ["cmd1", "cmd2"],
    "events_generated": ["event1"],
    "data_types_used": ["enum1", "bitmap1"],
    "scene_behaviors": ["scene_description"],
    
    "security_properties": [
      // CRITICAL: Match event_pattern structure to type!
      // Type 'happens' or 'never':
      {{
        "property_id": "SP1",
        "property_name": "snake_case_name",
        "property_type": "safety",
        "description": "Brief description",
        "constraint_type": "existential",
        "event_pattern": {{
          "type": "happens",
          "event": "EventName",
          "params": ["param1"]
        }},
        "source": "timing"
      }},
      // Type 'requires_previous':
      {{
        "property_id": "SP2",
        "property_name": "another_property",
        "property_type": "authentication",
        "description": "Requires prior event",
        "constraint_type": "universal",
        "event_pattern": {{
          "type": "requires_previous",
          "trigger_event": "TriggerEvent",
          "trigger_params": ["param1"],
          "required_event": "RequiredEvent",
          "required_params": ["param1"]
        }},
        "source": "effect_on_receipt"
      }}
    ],
    
    "definitions": [
      {{
        "term": "term_name",
        "definition": "Clear explanation. For attributes: TYPE: <type>. VALUES: <values>. DEFAULT: <default>. For abstractions: explain what parser should model.",
        "usage_context": "where_and_how_used"
      }}
    ],
    
    "references": [
      {{
        "id": "id_or_null",
        "name": "referenced_entity",
        "description": "why_referenced"
      }}
    ],
    
    "metadata": {{
      "generator_version": "2.0",
      "section_number": "string",
      "parser_optimized": true
    }}
  }}
}}
```

---
## GENERATION STRATEGY (ENHANCED)

Follow the original 15-step analysis methodology, with these additions:

**Before Step 1**: Extract attribute metadata from cluster spec
- Parse "Attributes" section for types, defaults, constraints
- Parse "Data Types" section for enums and bitmaps
- Parse "Features" section for feature flags

**During Step 5**: Consider state space size
- If state space explodes due to many attributes, prioritize key attributes
- Use feature flags judiciously (separate states vs guards)
- Balance explicitness with manageability

**During Step 7**: Document complex operations
- Use timing_requirements to explain abstractions
- Use definitions to clarify parser expectations
- Keep actions as simple assignments when possible

**After Step 15**: Add parser guidance to definitions
- For each key attribute, add TYPE/VALUES/DEFAULT
- For complex operations, explain abstraction approach
- For timer behaviors, clarify discrete value modeling

---
## BALANCE PRINCIPLE

**NOT all complexity needs elimination**. The goal is **PARSEABLE**, not **TRIVIAL**.

✅ Parsers can handle:
- Boolean operators (&&, ||, !)
- Comparisons (==, !=, <, >, <=, >=)
- Moderate expression nesting
- Range expressions (OnTime > 0 && OnTime < 100)

⚠️ Parsers may struggle with:
- Deep nesting (3+ levels)
- Complex arithmetic in guards
- Conditional logic in actions
- Unstructured free-form descriptions

**Solution**: When in doubt, add a clarifying comment in `timing_requirements` or `definitions` explaining how the parser should interpret complex expressions.

---
## VALIDATION CHECKLIST (PARSER-OPTIMIZED)

- [ ] All attributes have type information (from cluster spec or definitions)
- [ ] State invariants use parseable expressions (not prose)
- [ ] Actions are atomic assignments (or clearly documented abstractions)
- [ ] Guards use boolean/comparison operators (complexity is moderate)
- [ ] Complex operations documented in timing_requirements/definitions
- [ ] Timer states distinguish between 0, >0, and disabled values
- [ ] Feature flags handled (via guards or state space)
- [ ] Function calls explained as state effects in definitions
- [ ] All attribute defaults extractable from cluster spec
- [ ] State space is manageable (not exponential explosion)
- [ ] Transitions cover all command branches from specification
- [ ] Security properties extracted from timing/access/effect_on_receipt/events
- [ ] Security properties follow strict format (property_id, property_name, property_type, etc.)
- [ ] Tamarin formulas use ONLY allowed syntax:
  - [ ] Timepoints: #i, #j, #k (# prefix mandatory)
  - [ ] Facts: CapitalCase(args)@timepoint
  - [ ] Predicates: NO @timepoint suffix (IsNonEmpty(pin), NOT IsNonEmpty(pin)@i)
  - [ ] NO arithmetic: count <= 10, #i + 600
  - [ ] NO string literals: pin != ""
  - [ ] NO inequality operators: !=, <, >, <=, >=
- [ ] Follows original 15-step analysis methodology
- [ ] Maintains generalization (works for any cluster type)
- [ ] Leverages cluster spec structure (Attributes, Commands, Data Types)

---
## CRITICAL REMINDERS

1. **Build on existing structure**: The cluster spec provides rich metadata - use it!
2. **Keep generalization**: Must work for any Matter cluster type
3. **Balance simplicity and completeness**: Don't sacrifice correctness for simplicity
4. **Document abstractions**: Parser can handle "abstract" operations if documented
5. **State count is negotiable**: Prefer clarity over minimalism - 10 states is fine!

---
## FINAL SECURITY CHECKLIST

- [ ] Security properties use STRUCTURED format (event_pattern with type/event/params)
- [ ] NO Tamarin code in FSM (parser converts structured format)
- [ ] property_id, property_name, property_type, constraint_type, event_pattern all present
- [ ] Event names are CapitalCase, params lowercase
"""

# FSM Judge Prompt Template

FSM_JUDGE_PROMPT_TEMPLATE = """You are an FSM validator for Matter IoT protocols. Validate FSM structure for TAMARIN SECURITY ANALYSIS.

FSM (JSON):
{fsm}

Cluster Specification:
{cluster_info}

================================================================================
## CRITICAL VALIDATION FOR TAMARIN COMPATIBILITY (v2.0 FORMAT)
================================================================================

### REQUIRED TOP-LEVEL STRUCTURE:
{{
  "fsm_model": {{
    "cluster_name": "string",
    "cluster_id": "hex",
    "initial_state": "state_name",
    "features": [...],               // REQUIRED if cluster has feature flags
    "states": [...],
    "transitions": [...],
    "action_facts": [...],           // REQUIRED for Tamarin
    "security_properties": [...],    // Must reference action_facts
    "variables": {{...}},            // fresh/input/state-bound vars
    "metadata": {{"fsm_version": "2.0", "tamarin_compatible": true}}
  }}
}}

### VALIDATION CHECKLIST:

**1. FEATURES SECTION (CRITICAL FOR FEATURE-DEPENDENT CLUSTERS):**
- [ ] IF cluster specification mentions features (LT, DF, OFFONLY, etc.), `features` array MUST exist
- [ ] Each feature has: name, full_name, description
- [ ] Feature names match those referenced in guard_features
- [ ] Example: {{"name": "OFFONLY", "full_name": "OffOnly", "description": "Only Off command supported"}}

**2. ACTION FACTS (CRITICAL):**
- [ ] `action_facts` array exists and is non-empty
- [ ] Each action fact has: name (CamelCase), params (lowercase array), description
- [ ] Every security-relevant event has an action fact (success AND failure cases)
- [ ] Examples: LoginSuccess, LoginFailed, TempIdValidated, TempIdExpired, RateLimitTriggered

**3. TRANSITIONS WITH STRUCTURED GUARDS (CRITICAL):**
- [ ] Each transition has `guard_condition` (human-readable string)
- [ ] Each transition has `guard_features` array (can be empty if no feature guards)
- [ ] Each transition has `guard_attributes` array (can be empty if no attribute guards)
- [ ] IF guard_condition contains "feature_X == VALUE", guard_features MUST contain {{"name": "X", "value": "VALUE"}}
- [ ] IF guard_condition contains "attr op value", guard_attributes MUST contain {{"name": "attr", "operator": "op", "value": "value"}}
- [ ] Feature values are "TRUE" or "FALSE" (strings, uppercase)
- [ ] Format: {{"name": "OFFONLY", "value": "TRUE"}} or {{"name": "OnTime", "operator": ">", "value": "0"}}

**4. TRANSITIONS WITH ACTION_FACTS_EMITTED:**
- [ ] Each transition has `action_facts_emitted` array (can be empty for internal transitions)
- [ ] Each emitted fact references a defined action fact by name
- [ ] Args in emitted facts use lowercase variable names
- [ ] Format: {{"name": "ActionFactName", "args": ["var1", "var2"]}}

**5. SECURITY PROPERTIES CONSISTENCY:**
- [ ] IF no security requirements in specification, `security_properties` MUST be EMPTY array: []
- [ ] IF security_properties exist, `security_properties[].referenced_action_facts` ONLY contains names from `action_facts`
- [ ] Formula `trigger.fact` and `requirement.fact` names exist in `action_facts`
- [ ] No undefined action facts referenced anywhere
- [ ] Security properties are ONLY from specification - never fabricated or invented

**6. VARIABLES SECTION:**
- [ ] `variables.fresh_values` - server-generated values (setup_pin, session_id)
- [ ] `variables.input_bound` - values from client messages (temp_id, node)
- [ ] `variables.state_bound` - values from server state (account, endpoint)

**7. BASIC FSM STRUCTURE:**
- [ ] States represent cluster conditions (not abstract processing states)
- [ ] Initial state is set and exists in states array
- [ ] Major commands from specification are handled
- [ ] Guard conditions use simple expressions (no ||, split into multiple transitions)
- [ ] Actions in state_updates are simple assignments {{"attribute": "name", "value": "val"}}

**7.5. STARTUP TRANSITIONS (CRITICAL FOR CLUSTERS WITH StartUp* ATTRIBUTES):**
- [ ] IF cluster has StartUpOnOff, StartUpCurrentLevel, or other StartUp* attributes → Startup transitions MUST exist
- [ ] Startup transitions have trigger = "Startup" (not a command)
- [ ] Startup transitions have input_message = null and output_message = null
- [ ] Create transitions for ALL possible StartUp enum values (Off, On, Toggle, null/previous)
- [ ] Include guards for PreviousOnOff or equivalent when behavior depends on prior state
- [ ] Action facts like StartupOccurred, StartupForceOn, etc. should be defined and emitted

**8. FORMULA STRUCTURE (for security_properties):**
- [ ] formula_type is one of: requires_previous, requires_simultaneous, requires_all, leads_to, never, always
- [ ] formula.trigger and formula.requirement use a structure like {{"fact": "CamelCase", "args": ["var1", ...]}}
- [ ] All args are lowercase variable names
- [ ] All fact names are CamelCase

================================================================================
## COMMON ERRORS TO CHECK
================================================================================

**ERROR 1: Missing features section when cluster has features**
❌ Specification mentions "LT feature" or "OFFONLY feature" but no `features` array
→ REJECT with message: "Add features array with all feature flags from specification"

**ERROR 2: Missing action_facts**
❌ No action_facts array → REJECT

**ERROR 3: Undefined action fact in security_properties**
❌ referenced_action_facts contains "LoginAccepted" but action_facts has no "LoginAccepted"
→ REJECT with message: "Add LoginAccepted to action_facts or remove from security_properties"

**ERROR 4: Missing guard_features or guard_attributes**
❌ Transition has guard_condition "feature_OFFONLY == TRUE" but no guard_features array
→ REJECT with message: "Add guard_features: [{{'name': 'OFFONLY', 'value': 'TRUE'}}]"

**ERROR 5: Missing action_facts_emitted in transitions**
❌ Transition has no action_facts_emitted array → REJECT

**ERROR 6: Guard inconsistency**
❌ guard_condition says "feature_LT == TRUE" but guard_features has {{"name": "LT", "value": "FALSE"}}
→ REJECT: guard_condition and guard_features must match

**ERROR 7: Feature not declared**
❌ guard_features references "OFFONLY" but features array doesn't include it
→ REJECT: "Add OFFONLY to top-level features array"

**ERROR 8: Inconsistent parameter naming**
❌ action_facts has params: ["endpoint", "temp_id"]
   security_properties uses args: ["server", "tempAccountId"]
→ REJECT: variable names must match

**ERROR 9: Missing Startup transitions when StartUp attributes exist**
❌ Cluster specification has StartUpOnOff or StartUpCurrentLevel attribute but FSM has no transitions with trigger = "Startup"
→ REJECT: "Add Startup transitions for all StartUp enum values (Off, On, Toggle, null)"

================================================================================
## JUDGMENT CRITERIA
================================================================================

**APPROVE** if:
1. fsm_model.metadata.fsm_version == "2.0" OR tamarin_compatible == true
2. IF specification mentions features, `features` array exists with all feature flags
3. action_facts array exists with proper structure
4. All transitions have guard_features and guard_attributes arrays (can be empty)
5. Guard_features entries match guard_condition and reference declared features
6. All transitions have action_facts_emitted
7. security_properties is either EMPTY array (if no security requirements in spec) OR all references are defined in action_facts
8. Variables section properly categorizes fresh/input/state values
9. Basic FSM structure is sound (states, transitions, initial_state)
10. Security properties (if any) are derived from specification, not fabricated
11. IF cluster has StartUp* attributes, Startup transitions exist covering all enum values

**REJECT** if:
1. Cluster has features but missing features array
2. Missing action_facts array
3. Security properties reference undefined action facts
4. Security properties are fabricated (not from specification)
5. Missing guard_features or guard_attributes in transitions
6. guard_features references undeclared feature
7. guard_condition inconsistent with guard_features/guard_attributes
8. Missing action_facts_emitted in transitions
9. Using old event_pattern format instead of formula
10. Guards contain || operators (must split transitions)
11. state_updates contain control flow (if/for/while)
12. Cluster has StartUp* attributes but missing Startup transitions

================================================================================

Output JSON (NO markdown):
{{
    "correct": true/false,
    "explanation": "Brief reason for approval/rejection with specific issues found"
}}
"""


# **2. Transition Logic (Semantics)**
# * Parse "effect_on_receipt" of commands to determine transitions.
# * **Conditional Logic:** Convert `if/then/else` logic from the spec into **separate transitions** with mutually exclusive `guard_conditions`.
# * **Feature Constraints:** Use guard conditions to block commands if specific Feature Map bits are not set.
# * **Timers:** Model timer expiration as automatic transitions; model timer extensions as "stay" transitions.


# **3. Action & Definition Constraints (Tamarin-Compatible)**
# * **Atomic Actions Only:** Actions are simple assignments (`attribute := value`) or external calls (`send_response(Status)`).
# * **NO Control Flow in Actions:** Never use `if`, `else`, `for`, `while`, `:=`, or complex logic inside action strings.
# * **NO Control Flow in Definitions:** Definitions must NOT contain pseudocode, if/else, loops, or assignments.
# * **All Conditional Logic Goes to Guard Conditions:** Every `if/else` branch from the spec becomes a separate transition with unique, mutually exclusive guards.
# * **Definitions are Term/Concept Explanations Only:** Explain domain terms and constants, not algorithms.


# ### OUTPUT JSON STRUCTURE


# Return **ONLY** the raw JSON object matching this schema:


# {{
#   "fsm_model": {{
#     "cluster_name": "String",
#     "cluster_id": "Hex String",
#     "category": "String",
#     "states": [
#       {{
#         "name": "State Name",
#         "description": "Behavioral summary",
#         "is_initial": Boolean,
#         "invariants": ["Attribute constraints active in this state"],
#         "attributes_monitored": ["Attributes defining this state"]
#       }}
#     ],
#     "transitions": [
#       {{
#         "from_state": "Source State",
#         "to_state": "Target State",
#         "trigger": "Command Name | Timer Expiry | Event",
#         "guard_condition": "Boolean condition (e.g., 'Level > 0 && FeatureMap.Has(ABC)')",
#         "actions": ["attribute := value", "generate_event(Name)"],
#         "response_command": null,
#         "timing_requirements": "String or null"
#       }}
#     ],
#     "initial_state": "String",
#     "attributes_used": ["List of all referenced attributes"],
#     "commands_handled": ["List of all handled commands"],
#     "events_generated": ["List of generated events"],
#     "data_types_used": ["Enums, Bitmaps, Structs used"],
#     "scene_behaviors": ["Scene store/recall details if applicable"],
#     "definitions": [
#       {{
#         "term": "Concept or Constant Name",
#         "definition": "Plain English explanation (NO pseudocode, NO if/else, NO loops)",
#         "usage_context": "Where this term is used in the FSM"
#       }}
#     ],
#     "references": [
#       {{
#         "id": "ID or Null",
#         "name": "External Standard/Cluster",
#         "description": "Reason for dependency"
#       }}
#     ],
#     "metadata": {{
#       "generation_timestamp": "ISO 8601",
#       "generation_attempts": Integer,
#       "judge_approved": Boolean,
#       "source_pages": "String",
#       "section_number": "String"
#     }}
#   }}
# }}


# ### CRITICAL RULES REMINDER
# 1.  **Split Conditionals (Mandatory for Tamarin):**
#     * *Bad:* Action ["if x > 5 then y = 1"]
#     * *Good:* Transition 1 (Guard: "x > 5", Action: ["y := 1"]), Transition 2 (Guard: "x <= 5", Action: ["y := 0"])
# 2.  **Split Loops:**
#     * *Bad:* Action ["for each item in list, set value"]
#     * *Good:* Create separate transitions for each bit/item, or use guard conditions to handle all cases.
# 3.  **Definitions are NOT Algorithms:**
#     * *Bad:* "if Rate != null then effectiveRate := Rate else effectiveRate := DefaultRate"
#     * *Good:* "effectiveRate: The rate value used for continuous movement, determined by Rate parameter, DefaultMoveRate attribute, or MAX_PRACTICAL_RATE constant."
# 4.  **Accuracy:** Adhere strictly to the provided text. Do not hallucinate features not present in `{cluster_info}`.
# """

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
    "Classification": CLUSTER_OVERVIEW_EXTRACTION_PROMPT,
    "Revision History": REVISION_HISTORY_EXTRACTION_PROMPT,
    "Cluster ID": CLUSTER_OVERVIEW_EXTRACTION_PROMPT,
    "Attributes": ATTRIBUTES_EXTRACTION_PROMPT,
    "Data Types": DATA_TYPES_EXTRACTION_PROMPT,
    "Features": FEATURES_EXTRACTION_PROMPT,
    "Commands": COMMANDS_EXTRACTION_PROMPT,
    "Events": EVENTS_EXTRACTION_PROMPT,
    "Derived Cluster Namespace": DERIVED_CLUSTER_NAMESPACE_EXTRACTION_PROMPT,
    "Dependencies": DEPENDENCIES_EXTRACTION_PROMPT,
    "Mode Examples": MODE_EXAMPLES_EXTRACTION_PROMPT,
    "Status Codes": STATUS_CODES_EXTRACTION_PROMPT,
    "Cluster IDs": CLUSTER_OVERVIEW_EXTRACTION_PROMPT,
    "Definitions": DEFINITIONS_EXTRACTION_PROMPT,
    "Conversion of Temperature Values for Display": CONVERSIONS_EXTRACTION_PROMPT,
    "Multi Position Details": MULTI_POSITION_DETAILS_EXTRACTION_PROMPT,
    "Sequence of events for MultiPress": MULTIPRESS_SEQUENCE_EXTRACTION_PROMPT,
    "Summary of cases for MS feature flag": MS_FEATURE_FLAG_SUMMARY_EXTRACTION_PROMPT,
    "PIN/RFID Code Format": PIN_RFID_CODE_FORMAT_EXTRACTION_PROMPT,
    "State Change Table for Lighting": STATE_CHANGE_TABLE_LIGHTING_EXTRACTION_PROMPT,
    "Sequence of generated events": SEQUENCE_OF_GENERATED_EVENTS_EXTRACTION_PROMPT,
    "The Dimming Light Curve": DIMMING_LIGHT_CURVE_EXTRACTION_PROMPT,
    "Mode Use": MODE_USE_EXTRACTION_PROMPT,
    "Setpoint Limits": SETPOINT_LIMITS_EXTRACTION_PROMPT,
    "Recommended steps for creating a new User": USER_CREATION_STEPS_EXTRACTION_PROMPT,
    "Handling of fabric-scoping": FABRIC_SCOPING_EXTRACTION_PROMPT,
    "State Description": STATE_DESCRIPTION_EXTRACTION_PROMPT,
    "Mode Namespace": MODE_NAMESPACE_EXTRACTION_PROMPT,
    "Units of Temperature": UNITS_OF_TEMPERATURE_EXTRACTION_PROMPT,
    "Guidance for Fabrics / Commissioners": FABRICS_COMMISSIONERS_GUIDANCE_EXTRACTION_PROMPT
}

# ==============================================================================
# TAMARIN PROVER MODEL GENERATION CONFIGURATION
# ==============================================================================

# FSM to Tamarin Conversion Prompt Template
FSM_TO_TAMARIN_PROMPT_TEMPLATE = """
# MATTER FSM TO TAMARIN - COMPACT REFERENCE

Expert converter for Matter FSM → Tamarin theories. Focus: **termination, efficiency, correctness**.

**FSM INPUT**: {fsm_json}

---
## CORE PRINCIPLES

1. **Termination First**: Avoid looping rules, state explosion, missing sources.
2. **Efficiency**: Minimize rules, use persistent facts (`!Fact`), abstract timers.
3. **Correctness**: Every FSM transition → rule, faithful guards, preserved invariants.

---
## CRITICAL TAMARIN SYNTAX

### ✅ VALID Patterns
```tamarin
// Single functions block
functions: b_true/0, b_false/0, st_Off/0, st_On/0, tv_zero/0, tv_pos/0, tv_ffff/0

// Rule structure - premises are ONLY facts, no logic operators
rule RuleName:
  let var1 = term1 in
  [ Premise(x), !Config(tid, f) ]
--[ Action(x) ]->
  [ Conclusion(z) ]

// Persistent config: !Config(tid, feature1, feature2)
// Fresh vars: Fr(~tid), Public vars: In($A)
// Inequality ONLY in formulas: restriction ex: "not (x = y)"
```

### ❌ INVALID Patterns (PARSING ERRORS)
```tamarin
functions: true/0
functions: false/0   // WRONG: multiple blocks

[ St(tid, s1) | St(tid, s2) ]  // WRONG: disjunctions in premises
[ St(~tid, _, GSC) ]           // WRONG: underscore wildcards
lemma test [typing]:           // WRONG: use [sources]

// CRITICAL ERROR - not() in premises:
[ St(~tid, S, X), not (X = tv_ffff) ]  // WRONG: WILL NOT PARSE!
```

### ⚠️ HANDLING "NOT EQUAL" GUARDS (CRITICAL)
**You CANNOT use `not`, negation, or inequality in rule PREMISES - only in formulas.**

FSM guard `X != value` must be modeled by **splitting into separate rules**:
```tamarin
// FSM says: "guard: OnTime != 0xFFFF" 
// WRONG - parsing error:
rule Bad: [ St(~tid, s, OT), not (OT = tv_ffff) ] --> [ St(~tid, s2, OT) ]

// CORRECT - create rules for each ALLOWED value only:
rule Case_OT_zero: [ St(~tid, s, tv_zero, OW) ] --> [ St(~tid, s2, tv_zero, OW) ]
rule Case_OT_pos:  [ St(~tid, s, tv_pos, OW) ]  --> [ St(~tid, s2, tv_pos, OW) ]
// tv_ffff excluded by simply NOT having a rule for it
```

---
## OPTIMIZATION STRATEGIES

### Strategy 1: Unified State Fact
```tamarin
// Single fact type for all cluster state
St(~tid, state_enum, attr1, attr2, ...)
// Examples:
St(~tid, st_OffIdle, GSC, OT, OW)      // OnOff
St(~tid, st_Idle, Level, RT, SOL)       // LevelControl
St(~tid, st_Locked, LockState, AutoRT)  // DoorLock
```

### Strategy 2: Abstract Timers (NO ARITHMETIC)
```tamarin
functions: tv_zero/0, tv_pos/0, tv_ffff/0

// Timer conditions via pattern matching:
[ St(~tid, st_OnIdle, tv_pos) ]  // OnTime > 0
[ St(~tid, st_OnIdle, tv_zero) ] // OnTime == 0
```

### Strategy 3: Feature Combinations via Config
```tamarin
// At init, create ONE config fact for all features
rule Init_LT_DF:
  [ Fr(~tid) ]
--[ ClusterInit(~tid) ]->
  [ St(~tid, st_OffIdle, b_true, tv_zero, tv_zero),
    !Config(~tid, f_LT, f_DF) ]

// Rules check config
rule Cmd_On [requires LT]:
  [ St(~tid, st_OffIdle, GSC, OT, OW), !Config(~tid, f_LT, DF) ]
--[ Command(~tid, 'On') ]->
  [ St(~tid, st_OnIdle, GSC, OT, OW) ]
```

### Strategy 4: Minimal State Tracking
Track ONLY attributes that affect transitions:
- OnOff: GlobalSceneControl, OnTime, OffWaitTime
- LevelControl: CurrentLevel, RemainingTime
- DoorLock: LockState, AutoRelockTime

### Strategy 5: Guard Consolidation
```tamarin
// GOOD: Separate rules for different guards
rule Cmd_Toggle_WhenOff:
  [ St(~tid, st_Off) ] --[ ]-> [ St(~tid, st_On) ]

rule Cmd_Toggle_WhenOn:
  [ St(~tid, st_On) ] --[ ]-> [ St(~tid, st_Off) ]

// BAD: Complex conditionals in single rule
```

### Strategy 6: Sources Lemma (REQUIRED)
```tamarin
lemma sources [sources]:
  "All tid s1 s2 #i. StateTransition(tid, s1, s2)@i ==>
     Ex #j. ClusterInit(tid)@j & #j < #i"
```

---
## GUARD → PATTERN MAPPING

| Guard Condition | Tamarin Pattern |
|----------------|-----------------|
| `OnOff == true` | `St(~tid, State, b_true, ...)` |
| `OnOff == false` | `St(~tid, State, b_false, ...)` |
| `OnTime > 0` | `St(~tid, State, tv_pos, ...)` |
| `OnTime == 0` | `St(~tid, State, tv_zero, ...)` |
| `OnTime != 0xFFFF` | **Create rules for tv_zero and tv_pos only (omit tv_ffff rule)** |
| `feature_LT` | `!Config(~tid, f_LT, ...)` |
| `state == OffIdle` | `St(~tid, st_OffIdle, ...)` |
| `X OR Y` | **Split into separate rules** |
| `X != value` | **Split into rules for allowed values only** |

**⚠️ NEVER use `not()` in premises - Tamarin cannot parse it!**

---
## ACTION → STATE EFFECT MAPPING

| Action | Tamarin Effect |
|--------|----------------|
| `set OnOff := true` | `St(..., b_true, ...)` |
| `set OnOff := false` | `St(..., b_false, ...)` |
| `start timer(OnTime)` | `St(..., tv_pos, ...)` |
| `stop timer` | `St(..., tv_zero, ...)` |
| `timer expires` | Separate rule with `tv_zero` |

---
## COMPLETE TEMPLATE

```tamarin
theory {{ClusterName}}_Matter_FSM
begin

/* 
 * {{CLUSTER_NAME}} Cluster ({{CLUSTER_ID}})
 * Features: {{FEATURES}}
 * Auto-generated from FSM
 */

//========================================
// SECTION 1: Function Declarations (SINGLE BLOCK)
//========================================
functions:
  // Boolean values
  b_true/0, b_false/0,
  // State enumerations
  st_State1/0, st_State2/0, ...,
  // Abstract timer values
  tv_zero/0, tv_pos/0, tv_ffff/0,
  // Feature flags
  f_Feature1/0, f_Feature2/0

//========================================
// SECTION 2: Initialization Rules
//========================================
rule Init_FeatureCombo:
  [ Fr(~tid) ]
--[ ClusterInit(~tid) ]->
  [ St(~tid, st_InitialState, initial_attrs...),
    !Config(~tid, features...) ]

//========================================
// SECTION 3: Command Rules
//========================================
rule Cmd_CommandName_GuardVariant:
  [ St(~tid, st_SourceState, attrs...), !Config(~tid, features...) ]
--[ Command(~tid, 'CommandName'), StateTransition(~tid, st_Source, st_Target) ]->
  [ St(~tid, st_TargetState, new_attrs...) ]

//========================================
// SECTION 4: Timer Rules
//========================================
rule Timer_Expires_StateName:
  [ St(~tid, st_TimedState, tv_zero, other_attrs...) ]
--[ TimerExpired(~tid), StateTransition(~tid, st_Timed, st_Next) ]->
  [ St(~tid, st_NextState, updated_attrs...) ]

//========================================
// SECTION 5: Restrictions
//========================================
restriction unique_init:
  "All tid #i #j. ClusterInit(tid)@i & ClusterInit(tid)@j ==> #i = #j"

//========================================
// SECTION 6: Source Lemmas (REQUIRED)
//========================================
lemma sources [sources]:
  "All tid s1 s2 #i. StateTransition(tid, s1, s2)@i ==>
     Ex #j. ClusterInit(tid)@j & #j < #i"

//========================================
// SECTION 7: Verification Lemmas
//========================================
lemma exec_command_name:
  exists-trace
  "Ex tid #i. Command(tid, 'CommandName')@i"

lemma state_reachable:
  exists-trace
  "Ex tid #i. StateTransition(tid, st_Source, st_Target)@i"

end
```

---
## VALIDATION CHECKLIST

- [ ] Single `functions:` block
- [ ] No underscore `_` wildcards
- [ ] No `|` disjunctions in premises
- [ ] **No `not()` or negation in PREMISES** (split into separate rules instead!)
- [ ] All rules: same St fact arity
- [ ] Fresh vars: `~`, public: `$`
- [ ] Inequality only in FORMULAS: `not (x = y)` - NEVER in premises!
- [ ] Lemmas use `[sources]` not `[typing]`
- [ ] Every FSM state → `st_*/0` constant
- [ ] Every transition → rule(s)
- [ ] Config facts: `!` persistent
- [ ] Sources lemma present
- [ ] `X != value` guards → split into rules for allowed values only

---
## TROUBLESHOOTING

- **Parse error "unexpected ("**: You used `not()` in rule PREMISES - split into separate rules instead!
- **Parse error "facts must start with upper-case"**: Same cause - `not()` in premises is invalid
- **Non-termination**: Add sources lemma, check cycles, use `--precompute-only`
- **Partial deconstructions**: Add sources lemma, try `--auto-sources`
- **Rule not firing**: Check pattern matching, verify init creates needed facts
- **Memory issues**: Reduce feature combos, use `--heuristic=s`

---
## FSM INPUT FORMAT (JSON Schema)

```json
{{
  "cluster_name": "string",
  "cluster_id": "hex_string",
  "features": ["feature_list"],
  "states": [
    {{
      "name": "state_name",
      "description": "string",
      "attributes": {{
        "attr_name": {{ "type": "type", "value": "value" }}
      }}
    }}
  ],
  "transitions": [
    {{
      "id": "transition_id",
      "source": "source_state",
      "target": "target_state",
      "trigger": {{ "type": "command|timer|internal", "name": "trigger_name" }},
      "guards": [{{ "condition": "expression", "description": "string" }}],
      "actions": [{{ "type": "action_type", "target": "target", "value": "value" }}]
    }}
  ]
}}
```

---
## FEATURE COMBINATION GENERATION

For N boolean features, generate 2^N init rules:
```python
def generate_feature_combinations(features: list[str]) -> list[dict]:
    combinations = []
    for i in range(2 ** len(features)):
        combo = {{}}
        for j, feature in enumerate(features):
            combo[feature] = bool((i >> j) & 1)
        combinations.append(combo)
    return combinations
# Example: ['LT', 'DF', 'OffOnly'] → 8 combinations
```

---
## CROSS-CLUSTER DEPENDENCIES

Some clusters depend on others (e.g., LevelControl depends on OnOff):
```tamarin
rule Cmd_MoveToLevel_RequiresOnOff:
  [ !Config_LevelControl(~tid, ...),
    St_LevelControl(~tid, level, ...),
    St_OnOff(~tid, b_true, ...) ]  // OnOff must be ON
--[ Command(~tid, 'MoveToLevel') ]->
  [ St_LevelControl(~tid, newLevel, ...),
    St_OnOff(~tid, b_true, ...) ]  // Preserve OnOff
```
Options: Full modeling | Interface abstraction | Assume independence

---
## COMMAND PARAMETERS

For commands with parameters (e.g., `MoveToLevel(level, time)`):
```tamarin
functions: param_low/0, param_mid/0, param_high/0, param_max/0

rule Cmd_MoveToLevel_Low:
  [ St(~tid, state, level, ...), In(<param_low, time>) ]
--[ Command(~tid, 'MoveToLevel'), ParamUsed(~tid, param_low) ]->
  [ St(~tid, state, param_low, ...) ]
```

---
## TIMER STATE INVARIANT

```tamarin
restriction timer_state_invariant:
  "All tid state a1 a2 timerAttr delayAttr timerState #i.
     St(tid, state, a1, a2, timerAttr, delayAttr, timerState)@i ==>
       ((timerState = ts_idle) |
        (timerState = ts_timed & timerAttr = tv_pos) |
        (timerState = ts_delayed & delayAttr = tv_pos))"
```

---
## CLUSTER-SPECIFIC EXAMPLES

**OnOff (0x0006)**: Features: LT, DF, OffOnly | States: OffIdle, OnIdle, TimedOn, DelayedOff | Attrs: OnOff, OnTime, OffWaitTime, GlobalSceneControl | Commands: Off, On, Toggle, OffWithEffect, OnWithRecallGlobalScene, OnWithTimedOff

**LevelControl (0x0008)**: Features: OO, LT, FQ | States: Idle, Moving, Transitioning | Attrs: CurrentLevel, OnLevel, RemainingTime | Commands: MoveToLevel, Move, Step, Stop

**DoorLock (0x0101)**: Features: PIN, RID, FGP, LOG, USR | States: Locked, Unlocked, PartiallyLocked | Attrs: LockState, LockType, ActuatorEnabled | Commands: LockDoor, UnlockDoor, UnlockWithTimeout, SetCredential

---
## EXAMPLE CONVERSION

**FSM Input (SimpleSwitch)**:
```json
{{
  "cluster_name": "SimpleSwitch",
  "states": [
    {{ "name": "Off", "attributes": {{ "power": {{ "value": false }} }} }},
    {{ "name": "On", "attributes": {{ "power": {{ "value": true }} }} }}
  ],
  "transitions": [
    {{ "source": "Off", "target": "On", "trigger": {{ "type": "command", "name": "TurnOn" }} }},
    {{ "source": "On", "target": "Off", "trigger": {{ "type": "command", "name": "TurnOff" }} }}
  ]
}}
```

**Tamarin Output**:
```tamarin
theory SimpleSwitch_Matter
begin

functions: b_true/0, b_false/0, st_Off/0, st_On/0

rule Init:
  [ Fr(~tid) ]
--[ ClusterInit(~tid) ]->
  [ St(~tid, st_Off) ]

rule Cmd_TurnOn:
  [ St(~tid, st_Off) ]
--[ Command(~tid, 'TurnOn'), StateTransition(~tid, st_Off, st_On) ]->
  [ St(~tid, st_On) ]

rule Cmd_TurnOff:
  [ St(~tid, st_On) ]
--[ Command(~tid, 'TurnOff'), StateTransition(~tid, st_On, st_Off) ]->
  [ St(~tid, st_Off) ]

restriction unique_init:
  "All tid #i #j. ClusterInit(tid)@i & ClusterInit(tid)@j ==> #i = #j"

lemma sources [sources]:
  "All tid s1 s2 #i. StateTransition(tid, s1, s2)@i ==>
     Ex #j. ClusterInit(tid)@j & #j < #i"

lemma exec_turnon: exists-trace "Ex tid #i. Command(tid, 'TurnOn')@i"
lemma exec_turnoff: exists-trace "Ex tid #i. Command(tid, 'TurnOff')@i"

end
```

---
## OUTPUT REQUIREMENTS

Return ONLY valid Tamarin theory code:
- No markdown code blocks
- No explanatory text
- Directly parseable by: `tamarin-prover --parse-only <file>.spthy`
"""

# FSM_TO_TAMARIN_PROMPT_TEMPLATE = """
# # MATTER FSM → TAMARIN CONVERTER (COMPACT)

# Expert converter. Focus: **termination, correctness, parsing validity**.

# **FSM INPUT**: {fsm_json}

# ---
# ## CORE PRINCIPLES & SYNTAX RULES

# 1. **Termination**: No loops without progress. Use `[sources]` lemmas.
# 2. **Correctness**: 1 Transition = 1 Rule. Guards must be exact.
# 3. **Efficiency**: Use persistent facts (`!Config`).

# ### ✅ CRITICAL SYNTAX (STRICT)
# - **Functions**: SINGLE block `functions: name/arity, ...`
# - **Rules**: Facts ONLY in premises. `[ St(...) ] --[ Action ]-> [ St(...) ]`
# - **Config**: `!Config(tid, features...)` is persistent.
# - **Fresh**: `Fr(~tid)` | **Public**: `In($x)`
# - **Inequality**: ONLY in restrictions `not(x=y)`. **NEVER in premises.**

# ### ❌ PARSING ERRORS (AVOID)
# - **NO `not()` in premises**: `[ St(..), not(X=val) ]` → WILL NOT PARSE.
# - **NO Disjunction**: `[ A | B ]` → Invalid.
# - **NO Underscores**: `St(_, x)` → Invalid. Use variables.
# - **Arity Mismatch**: All `St(...)` facts MUST have EQUAL arguments. Pad with `null`.

# ---
# ## MODELING STRATEGIES

# ### 1. Handling `!=` Guards (MANDATORY)
# Tamarin premises cannot handle negation. Split into rules for **allowed** values.
# *Bad*: `guard: X != 0xFFFF` → `rule [St(X), not(X=tv_ffff)]` (ERROR)
# *Good*:
#   - Rule 1: `[St(tv_zero)]`
#   - Rule 2: `[St(tv_pos)]`
#   (tv_ffff is implicitly excluded by omission)

# ### 2. Abstracting Attributes (No Arithmetic)
# Discretize large ranges into symbolic constants:
# - **Timers**: `tv_zero` (0), `tv_pos` (>0), `tv_ffff` (max)
# - **Levels**: `lv_min`, `lv_mid`, `lv_max`
# - **Bools**: `b_true`, `b_false`

# ### 3. State Fact Arity Consistency
# Calculate MAX attributes across all states. **Pad shorter states with `null`**.
# - State A (2 attrs): `St(~tid, st_A, a1, a2, null)`
# - State B (3 attrs): `St(~tid, st_B, b1, b2, b3)`

# ### 4. Feature Combinations
# Generate `2^N` init rules for feature sets (LT, OO, etc.).
# `rule Init_LT: [Fr(~tid)] --[Init]-> [St(...), !Config(~tid, f_LT)]`

# ---
# ## MAPPINGS

# | FSM Element | Tamarin Equivalent | Notes |
# |-------------|-------------------|-------|
# | `OnOff := true` | `St(..., b_true)` | Use constant |
# | `Timer := 100` | `St(..., tv_pos)` | Abstract value |
# | `Timer := 0` | `St(..., tv_zero)` | |
# | `Guard: X == Y` | Pattern match in premises | Same variable name |
# | `Guard: X != Y` | Split into rules for allowed values | |
# | `Action: generate(E)` | `--[ Event(tid, E) ]->` | Traceable action |

# ---
# ## TAMARIN TEMPLATE (Output ONLY this)

# ```tamarin
# theory {{ClusterName}}_FSM
# begin

# /* {{CLUSTER_NAME}} FSM Model */

# // 1. FUNCTIONS (Single Block)
# functions:
#   b_true/0, b_false/0, null/0,
#   st_Idle/0, st_Moving/0, ...,          // States
#   tv_zero/0, tv_pos/0, tv_ffff/0,       // Timers
#   lv_min/0, lv_mid/0, lv_max/0,         // Levels
#   f_LT/0, f_OO/0                        // Features

# // 2. INITIALIZATION
# rule Init_Features:
#   [ Fr(~tid) ]
# --[ ClusterInit(~tid) ]->
#   [ St(~tid, st_Initial, init_vals..., null...), !Config(~tid, f_LT...) ]

# // 3. TRANSITIONS
# rule Trans_Name:
#   [ St(~tid, st_Src, val_match...), !Config(~tid, f_LT...) ]
# --[ Command(~tid, 'Cmd'), Transition(st_Src, st_Dst) ]->
#   [ St(~tid, st_Dst, new_vals...) ]

# // 4. RESTRICTIONS
# restriction UniqueInit:
#   "All t #i #j. ClusterInit(t)@i & ClusterInit(t)@j ==> #i=#j"

# restriction SameArity:
#   "All t s a1 a2 a3 a4 #i. St(t,s,a1,a2,a3,a4)@i ==> T" // Adjust count

# // 5. LEMMAS
# lemma sources [sources]:
#   "All t s1 s2 #i. Transition(s1,s2)@i ==> Ex #j. ClusterInit(t)@j & j<i"

# lemma executable: exists-trace "Ex t #i. Command(t, 'Cmd')@i"

# end
# ```

# ---
# ## CHECKLIST (Pre-Generation)
# 1. Single `functions:` block?
# 2. No `not()` in rule premises?
# 3. All `St()` facts have SAME arity (padded with `null`)?
# 4. `!=` guards split into multiple rules?
# 5. `[sources]` lemma included?

# RETURN ONLY VALID TAMARIN CODE.
# """
