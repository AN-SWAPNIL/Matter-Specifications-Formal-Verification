# Research Analysis: LLM vs Parser Strategy for FSM-to-Tamarin Generation

**Author:** Research Analysis  
**Date:** December 24, 2025  
**Project:** Matter Protocol FSM Generator for Tamarin Security Verification

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Pipeline Overview](#pipeline-overview)
3. [Strategy 1: LLM Way - Deep Analysis](#strategy-1-llm-way---deep-analysis)
4. [Strategy 2: Parser Way - Deep Analysis](#strategy-2-parser-way---deep-analysis)
5. [Comparative Analysis](#comparative-analysis)
6. [FSM Content Comparison](#fsm-content-comparison)
7. [Tamarin Output Quality Analysis](#tamarin-output-quality-analysis)
8. [Recommendations](#recommendations)

---

## Executive Summary

This research analyzes two distinct strategies for generating Tamarin protocol verification models from Matter IoT cluster specifications:

| Aspect                    | Strategy 1 (LLM)                  | Strategy 2 (Parser)         |
| ------------------------- | --------------------------------- | --------------------------- |
| **FSM Generation**        | LLM with judge loop               | LLM with structured judge   |
| **Tamarin Conversion**    | LLM with judge loop               | Deterministic parser        |
| **FSM Transitions**       | 57 (complete with Startup)        | 29 (missing Startup)        |
| **Tamarin Syntax**        | Error-prone (5-10 retries)        | Zero errors (deterministic) |
| **Action Representation** | Complex (if-else, function calls) | Simple (attribute=value)    |

### Critical Finding

**Strategy 2's FSM is MISSING actual content, not just documentation sections:**

- Missing **6 Startup transitions** (power-cycle behavior)
- Missing **feature combination variants** (e.g., `LT && OnTime==0 && OffWaitTime>0`)
- Has only 29 transitions vs Strategy 1's 57 transitions

**The removal of "definitions" was intentional** because if-else logic and function calls like `store_global_scene()` cannot be converted to Tamarin. Strategy 2 correctly simplifies actions to parseable `state_updates`.

### Primary Recommendation

**Use Strategy 2's parser approach** (more reliable) **BUT fix the FSM completeness** by ensuring all transitions (including Startup) are generated.

---

## Pipeline Overview

### Common Starting Point

Both strategies share the same initial stages:

```
matter_toc_extractor.py → cluster_detail_extractor.py
         ↓                          ↓
   TOC JSON file              Cluster Detail JSON
```

### Divergence Point

```
Strategy 1 (LLM Way):
cluster_detail_extractor.py
    → cluster_fsm_generator_for_llm.py
    → cluster_tamarin_generator.py

Output: fsm_models/ & tamarin_models_from_fsm/

Strategy 2 (Parser Way):
cluster_detail_extractor.py
    → cluster_fsm_generator_for_parser.py
    → cluster_tamarin_parser.py

Output: fsm_models_v2/
```

---

## FSM Content Comparison (CRITICAL)

### Transition Count by Command

| Command                 | Strategy 1 | Strategy 2 | Missing |
| ----------------------- | ---------- | ---------- | ------- |
| Off                     | 4          | 2          | 2       |
| On                      | 7          | 5          | 2       |
| Toggle                  | 7          | 5          | 2       |
| OffWithEffect           | 8          | 5          | 3       |
| OnWithRecallGlobalScene | 12         | 3          | **9**   |
| OnWithTimedOff          | 9          | 5          | 4       |
| Timer/TimerTick         | 4          | 4          | 0       |
| **Startup**             | **6**      | **0**      | **6**   |
| **TOTAL**               | **57**     | **29**     | **28**  |

### What Strategy 2 FSM is MISSING

#### 1. **ALL Startup Transitions (6 missing) - CRITICAL**

Strategy 1 has:

```json
{"trigger": "Startup", "guard_condition": "feature_LT == TRUE && StartUpOnOff_is_null == TRUE && PreviousOnOff == TRUE", "actions": ["OnOff := TRUE"]}
{"trigger": "Startup", "guard_condition": "feature_LT == TRUE && StartUpOnOff_value == StartUpOnOffEnum_On", "actions": ["OnOff := TRUE"]}
{"trigger": "Startup", "guard_condition": "feature_LT == TRUE && StartUpOnOff_value == StartUpOnOffEnum_Toggle && PreviousOnOff == FALSE", ...}
// ... 3 more
```

**Strategy 2 has NONE.** This means power-cycle attacks cannot be analyzed.

#### 2. **Feature Combination Variants (many missing)**

Strategy 1 has separate transitions for:

```json
{"guard_condition": "feature_OFFONLY == FALSE && feature_LT == FALSE", ...}
{"guard_condition": "feature_OFFONLY == FALSE && feature_LT == TRUE && !(OnTime == 0 && OffWaitTime > 0)", ...}
{"guard_condition": "feature_OFFONLY == FALSE && feature_LT == TRUE && OnTime == 0 && OffWaitTime > 0", ...}
```

Strategy 2 simplifies to:

```json
{
  "guard_condition": "feature_OFFONLY == FALSE",
  "guard_features": [{ "name": "OFFONLY", "value": "FALSE" }]
}
```

**Impact:** Loss of timer-dependent behavior modeling.

#### 3. **OnWithRecallGlobalScene Variants (9 missing)**

Strategy 1: 12 transitions covering all state × GSC × OnTime combinations
Strategy 2: Only 3 transitions

---

## Tamarin Output Comparison

### Strategy 1 Tamarin (LLM-generated)

**File:** `tamarin_models_from_fsm/OnOff_Cluster_tamarin.spthy` (522 lines)

```tamarin
// State fact with 8 parameters - tracks ALL attributes
St(tid, State, OnOff, OnTime, OffWaitTime, GlobalSceneControl, StartUpOnOff, PreviousOnOff)

// Timer value abstraction
functions: tv_zero/0, tv_pos/0, tv_ffff/0

// Has Startup rules
rule Startup_From_OffIdle_SU_Null_PrevOn:
  [ St(~tid, st_OffIdle, On, OT, OW, GSC, su_null, prev_on) ]
--[ Command(~tid, 'Startup'), StateTransition(~tid, st_OffIdle, st_OnIdle) ]->
  [ St(~tid, st_OnIdle, b_true, OT, OW, GSC, su_null, prev_on) ]

// Simple action labels
--[ Command(~tid, 'Off'), StateTransition(~tid, st_OnIdle, st_OffIdle) ]->
```

**Pros:**

- ✅ Models Startup behavior (6 rules)
- ✅ Tracks all 8 state attributes
- ✅ Timer abstraction (tv_zero, tv_pos, tv_ffff)
- ✅ Feature flag combinations

**Cons:**

- ❌ Prone to syntax errors (LLM hallucinations)
- ❌ Simple action labels (only `Command` and `StateTransition`)
- ❌ Requires 5-10 retry loops

### Strategy 2 Tamarin (Parser-generated)

**File:** `fsm_models_v2/1.5_OnOff_Cluster_fsm.spthy` (798 lines)

```tamarin
// Simple state fact
ServerState(endpoint, 'BaseOff')

// Message passing modeled
In(<'Off_Request', endpoint>)
Out(<'Off_Response', SUCCESS>)

// Rich action labels (23 different facts)
--[
    Off(endpoint),
    StateTransition(endpoint, 'BaseOn', 'BaseOff'),
    OffReceived(endpoint),
    OffAccepted(endpoint)
]->

// NO Startup rules - missing!
```

**Pros:**

- ✅ Zero syntax errors (deterministic)
- ✅ Rich action facts (23 types) - better for security lemmas
- ✅ Message passing modeled (In/Out)
- ✅ Reachability lemmas auto-generated

**Cons:**

- ❌ NO Startup rules - cannot analyze power-cycle attacks
- ❌ Simpler state representation (loses timer abstraction)
- ❌ Missing feature combination handling

---

## Why Definitions Were Removed (Intentional Design)

The user correctly points out that definitions were removed because **if-else logic cannot be converted to Tamarin**.

### Strategy 1 Actions (Cannot Parse):

```json
"actions": [
    "store_global_scene()",           // Function call - cannot parse
    "OnTime := max(current, field)",   // Complex expression - cannot parse
    "if (OnTime == 0) OffWaitTime := 0" // Conditional - cannot parse
]
```

### Strategy 2 Actions (Parseable):

```json
"state_updates": [
    {"attribute": "OnOff", "value": "FALSE"},
    {"attribute": "OnTime", "value": "0"},
    {"attribute": "OffWaitTime", "value": "0"}
]
```

**This simplification is CORRECT** for Tamarin compatibility. The issue is that Strategy 2's FSM prompt doesn't require Startup transitions.

---

## Strategy 1: LLM Way - Deep Analysis

### File: `cluster_fsm_generator_for_llm.py`

#### Architecture

```python
class FSMGenerator:
    def __init__(self):
        self.fsm_generator = init_chat_model(...)  # For FSM generation
        self.judge = init_chat_model(...)          # For validation

    def generate_fsm(self, cluster_info, max_retries=10):
        # Iterative refinement with judge feedback
        for attempt in range(max_retries):
            response = self.fsm_generator.invoke(prompt)
            judge_response = self.judge_fsm(response, cluster_info)
            if '"correct": true' in judge_response:
                return fsm_data
            feedback = judge_response  # Use for next iteration
```

#### Prompt Used: `FSM_GENERATION_PROMPT_TEMPLATE_LLM`

**Key Characteristics:**

- Focus on behavioral FSM modeling
- Emphasizes Tamarin compatibility at action level
- No structured action facts requirement
- Simple transition format without `guard_features` decomposition

**Prompt Structure Analysis:**

```
1. UNIVERSAL FSM GENERATION APPROACH (Steps 1-9)
2. ANALYSIS METHODOLOGY (15-step procedure)
3. OUTPUT STRUCTURE (basic FSM schema)
4. VALIDATION CHECKLIST
```

#### Judge Implementation

```python
def judge_fsm(self, fsm: str, user_input: str) -> str:
    prompt = f"""
    You are a judge that evaluates the correctness of a finite state machine...
    Your output format should be json parsable:
    {{
        "correct": true/false,
        "explanation": "Your explanation"
    }}
    """
```

**Weakness:** The judge prompt is generic and doesn't validate v2.0 schema requirements.

### File: `cluster_tamarin_generator.py`

#### Architecture

```python
class FSMToTamarinConverter:
    def __init__(self):
        self.converter = init_chat_model(...)  # For Tamarin generation
        self.judge = init_chat_model(...)      # For validation

    def convert_fsm_to_tamarin(self, fsm_data, max_retries=10):
        for attempt in range(max_retries):
            response = self.converter.invoke(prompt)

            # Run tamarin-prover --parse for syntax validation
            parse_result = self.run_tamarin_parse(tamarin_code)

            # LLM judge evaluates semantic correctness
            judge_response = self.judge_tamarin(tamarin_code, fsm_json, parse_result)

            if '"correct": true' in judge_response:
                return result
```

#### Critical Issue: LLM Tamarin Generation

The `FSM_TO_TAMARIN_PROMPT_TEMPLATE` attempts to teach LLM Tamarin syntax:

```
## CRITICAL SYNTAX RULES

### 1. FACT ARGUMENT SYNTAX (MOST COMMON ERROR)
**Every argument MUST be separated by comma** - no exceptions!

❌ St(~tid, state, OnTime OffWaitTime, GSC)     // Missing comma
✅ St(~tid, state, OnTime, OffWaitTime, GSC)    // Correct
```

**Problem:** Despite extensive documentation, LLM still produces:

- Missing commas between fact arguments
- Malformed comments (colons cause parse errors)
- Inconsistent fact arity
- Undefined action fact references

### Output Analysis: `tamarin_models_from_fsm/OnOff_Cluster_tamarin.spthy`

```tamarin
theory OnOff_Cluster_0x0006_Matter_FSM
begin

functions:
  b_true/0, b_false/0,
  st_OffIdle/0, st_OnIdle/0, st_TimedOn/0, st_DelayedOff/0,
  tv_zero/0, tv_pos/0, tv_ffff/0,
  ...

// Unified state fact:
//   St(tid, State, OnOff, OnTime, OffWaitTime, GlobalSceneControl, StartUpOnOff, PreviousOnOff)

rule Init_OffIdle_GenericConfig:
  [ Fr(~tid) ]
--[ ClusterInit(~tid) ]->
  [ St(~tid, st_OffIdle, b_false, tv_zero, tv_zero, b_true, su_null, prev_off),
    !Config(~tid, f_LT_true, f_DF_false, f_OFFONLY_false) ]
```

**Observations:**

- Complex state fact with 8 parameters
- Feature flags encoded as function symbols
- Timer values abstracted as `tv_zero/tv_pos/tv_ffff`
- No structured action labels beyond `Command()` and `StateTransition()`

---

## Strategy 2: Parser Way - Deep Analysis

### File: `cluster_fsm_generator_for_parser.py`

#### Architecture

```python
class FSMGenerator:
    def __init__(self):
        self.prompt_template = FSM_GENERATION_PROMPT_TEMPLATE_PARSER  # v2.0 schema
        self.judge_prompt_template = FSM_JUDGE_PROMPT_TEMPLATE        # Structured validation
```

#### Prompt Used: `FSM_GENERATION_PROMPT_TEMPLATE_PARSER`

**Key Differences from LLM Prompt:**

1. **Action Facts Requirement:**

```json
"action_facts": [
  {
    "name": "GetSetupPINReceived",
    "params": ["endpoint", "temp_id"],
    "description": "Server received GetSetupPIN request"
  }
]
```

2. **Structured Guard Decomposition:**

```json
"transitions": [{
  "guard_condition": "feature_OFFONLY == TRUE",
  "guard_features": [{"name": "OFFONLY", "value": "TRUE"}],
  "guard_attributes": [],
  "action_facts_emitted": [
    {"name": "OnReceived", "args": ["endpoint"]},
    {"name": "OnNotSupportedOffOnly", "args": ["endpoint"]}
  ]
}]
```

3. **Security Properties with Formula Structure:**

```json
"security_properties": [{
  "property_id": "SP1",
  "property_name": "rate_limit_enforced",
  "formula_type": "requires_previous",
  "formula": {
    "quantifier": "All",
    "variables": ["endpoint", "temp_id"],
    "trigger": {"fact": "GetSetupPINAccepted", "args": ["endpoint", "temp_id"]},
    "requirement": {"fact": "RateLimitWindowActive", "args": ["endpoint"]},
    "temporal": "before"
  },
  "referenced_action_facts": ["GetSetupPINAccepted", "RateLimitWindowActive"]
}]
```

#### Judge Implementation: `FSM_JUDGE_PROMPT_TEMPLATE`

**Validates v2.0 Schema:**

```
### VALIDATION CHECKLIST:

**1. FEATURES SECTION:**
- [ ] IF cluster has features, `features` array MUST exist
- [ ] Feature names match those referenced in guard_features

**2. ACTION FACTS:**
- [ ] `action_facts` array exists and is non-empty
- [ ] Each action fact has: name (CamelCase), params (lowercase), description

**3. TRANSITIONS WITH STRUCTURED GUARDS:**
- [ ] Each transition has `guard_features` array
- [ ] Each transition has `guard_attributes` array
- [ ] IF guard_condition contains "feature_X == VALUE", guard_features MUST contain matching entry

**4. SECURITY PROPERTIES CONSISTENCY:**
- [ ] `referenced_action_facts` ONLY contains names from `action_facts`
```

### File: `cluster_tamarin_parser.py`

#### Architecture: Rule-Based Deterministic Parser

```python
class TamarinGeneratorV2:
    """Generates Tamarin protocol code from enhanced FSM JSON."""

    def __init__(self, fsm_data):
        self.fsm = fsm_data.get('fsm_model', {})
        self.action_facts = self._parse_action_facts()
        self.fresh_values = self._extract_fresh_values()
        self.features = self._extract_features()

    def generate(self) -> str:
        sections = [
            self._generate_header(),
            self._generate_builtins(),
            self._generate_functions(),
            self._generate_restrictions(),
            self._generate_init_rule(),
            self._generate_fresh_value_rules(),
            self._generate_transition_rules(),
            self._generate_lemmas(),
            "end"
        ]
        return '\n\n'.join(filter(None, sections))
```

#### Key Parser Methods

**1. Transition Rule Generation:**

```python
def _generate_single_rule(self, trans):
    # Extract guard information
    guard_features = trans.get('guard_features', [])
    guard_attributes = trans.get('guard_attributes', [])

    # Build premise facts
    premise_facts = [f"ServerState(endpoint, '{from_state}')"]

    # Add feature config facts
    for guard_feat in guard_features:
        premise_facts.append(
            f"!FeatureConfig(endpoint, '{feat_name}', '{feat_value}')"
        )

    # Build action labels from action_facts_emitted
    action_labels = [f"{trigger}(endpoint)"]
    for af in trans.get('action_facts_emitted', []):
        action_labels.append(f"{af['name']}({', '.join(af['args'])})")

    # Build conclusion facts
    conclusion_facts = [f"ServerState(endpoint, '{to_state}')"]
```

**2. Security Lemma Generation:**

```python
def _generate_security_lemma(self, prop):
    formula_type = prop.get('formula_type', '')
    formula = prop.get('formula', {})

    if formula_type == 'requires_previous':
        # All vars #i. Trigger@i ==> Ex #j. Requirement@j & #j < #i
        return f"All {var_decl} #i. {trigger_fact}@i ==> Ex #j. {req_fact}@j & #j < #i"

    elif formula_type == 'requires_simultaneous':
        # All vars #i. Trigger@i ==> Requirement@i
        return f"All {var_decl} #i. {trigger_fact}@i ==> {req_fact}@i"
```

### Output Analysis: `fsm_models_v2/1.5_OnOff_Cluster_fsm.spthy`

```tamarin
theory On_Off_Cluster
begin

/*
 * Model Statistics:
 * - States: 4
 * - Transitions: 29
 * - Action Facts: 23
 * - Security Properties: 0
 */

builtins: hashing, symmetric-encryption

functions: true/0, false/0, null/0, empty/0, SUCCESS/0, FAILURE/0

restriction Equality:
    "All x y #i. Eq(x, y)@i ==> x = y"

rule Server_Init:
    [ Fr(~endpoint_id) ]
    --[ ServerInit(~endpoint_id), Once(<'server_init', ~endpoint_id>) ]->
    [
        !Server(~endpoint_id),
        ServerState(~endpoint_id, 'BaseOff'),
        !FeatureConfig(~endpoint_id, 'LT', feature_lt),
        !FeatureConfig(~endpoint_id, 'OFFONLY', feature_offonly)
    ]

rule On_BaseOff_to_BaseOff_T3:
    [
        ServerState(endpoint, 'BaseOff'),
        !FeatureConfig(endpoint, 'OFFONLY', 'true'),
        In(<'On_Request', endpoint>),
        !Server(endpoint)
    ]
    --[
        On(endpoint),
        StateTransition(endpoint, 'BaseOff', 'BaseOff'),
        OnReceived(endpoint),
        OnNotSupportedOffOnly(endpoint)
    ]->
    [
        ServerState(endpoint, 'BaseOff'),
        Out(<'On_Response', 'UNSUPPORTED_COMMAND'>),
        !Server(endpoint)
    ]
```

**Observations:**

- Clean, consistent structure
- Action facts directly from FSM `action_facts_emitted`
- Feature configuration as persistent facts
- Automatic state transition tracking
- No syntax errors

---

## Comparative Analysis

### FSM Schema Comparison

| Field                  | Strategy 1 (v1.0) | Strategy 2 (v2.0)                   |
| ---------------------- | ----------------- | ----------------------------------- |
| `features`             | ❌ Not required   | ✅ Required if cluster has features |
| `action_facts`         | ❌ Not present    | ✅ Required array                   |
| `guard_features`       | ❌ Not present    | ✅ Required in transitions          |
| `guard_attributes`     | ❌ Not present    | ✅ Required in transitions          |
| `action_facts_emitted` | ❌ Not present    | ✅ Required in transitions          |
| `security_properties`  | ❌ Basic or none  | ✅ Structured with formulas         |
| `variables`            | ❌ Not structured | ✅ fresh/input/state categorization |
| `protocol_messages`    | ❌ Not present    | ✅ Request/response definitions     |

### Strategy 1 FSM Example (v1.0)

```json
{
  "fsm_model": {
    "cluster_name": "On/Off Cluster",
    "states": [
      {
        "name": "Off_Idle",
        "invariants": ["OnOff == FALSE"],
        "attributes_monitored": ["OnOff", "OnTime"]
      }
    ],
    "transitions": [
      {
        "from_state": "Off_Idle",
        "to_state": "On_Idle",
        "trigger": "On",
        "guard_condition": "feature_OFFONLY == FALSE && feature_LT == TRUE",
        "actions": ["OnOff := TRUE", "OffWaitTime := 0"],
        "response_command": null
      }
    ]
  }
}
```

### Strategy 2 FSM Example (v2.0)

```json
{
  "fsm_model": {
    "cluster_name": "On/Off Cluster",
    "features": [
      {"name": "LT", "full_name": "Lighting", "description": "..."},
      {"name": "OFFONLY", "full_name": "OffOnly", "description": "..."}
    ],
    "action_facts": [
      {"name": "OnReceived", "params": ["endpoint"], "description": "..."},
      {"name": "OnAccepted", "params": ["endpoint"], "description": "..."},
      {"name": "OnNotSupportedOffOnly", "params": ["endpoint"], "description": "..."}
    ],
    "states": [...],
    "transitions": [
      {
        "transition_id": "T3",
        "from_state": "BaseOff",
        "to_state": "BaseOff",
        "trigger": "On",
        "guard_condition": "feature_OFFONLY == TRUE",
        "guard_features": [{"name": "OFFONLY", "value": "TRUE"}],
        "guard_attributes": [],
        "action_facts_emitted": [
          {"name": "OnReceived", "args": ["endpoint"]},
          {"name": "OnNotSupportedOffOnly", "args": ["endpoint"]}
        ],
        "state_updates": []
      }
    ],
    "security_properties": []
  }
}
```

### Tamarin Output Comparison

| Aspect                   | Strategy 1 (LLM)                     | Strategy 2 (Parser)                       |
| ------------------------ | ------------------------------------ | ----------------------------------------- |
| **Syntax Errors**        | Common (5-10 retries)                | None (deterministic)                      |
| **Action Labels**        | Basic (`Command`, `StateTransition`) | Rich (all `action_facts_emitted`)         |
| **Feature Handling**     | Function symbols                     | Persistent facts                          |
| **State Representation** | Complex 8-param fact                 | Simple 2-param fact                       |
| **Security Lemmas**      | Manual/inconsistent                  | Auto-generated from `security_properties` |
| **Consistency**          | Variable                             | 100% deterministic                        |

---

## Tamarin Output Quality Analysis

### Strategy 1 Common Errors

**1. Missing Commas in Facts (Most Common)**

```tamarin
❌ St(~tid, state, OnTime OffWaitTime, GSC)
✅ St(~tid, state, OnTime, OffWaitTime, GSC)
```

**2. Malformed Comments**

```tamarin
❌ // Section: Description  // Colon in comment
❌ /*: Title */            // Leading colon
✅ // Section - Description
```

**3. Inconsistent Fact Arity**

```tamarin
Rule 1: St(~tid, state, a, b, c, d, e, f)  // 8 params
Rule 2: St(~tid, state, a, b, c, d)        // 6 params - ERROR
```

**4. Undefined Action Facts in Lemmas**

```tamarin
lemma security_prop:
    "All x #i. UndefinedFact(x)@i ==> ..."  // UndefinedFact never emitted
```

### Strategy 2 Guarantees

- ✅ Consistent fact arity (programmatic generation)
- ✅ All action facts defined before use
- ✅ No comment syntax issues (templated)
- ✅ Proper comma separation (string formatting)
- ✅ Lemmas only reference emitted facts

---

## Prompt Engineering Analysis

### `FSM_GENERATION_PROMPT_TEMPLATE_LLM` (3873 lines total, ~500 for this prompt)

**Strengths:**

- Comprehensive 15-step methodology
- Good behavioral modeling guidance
- Timer semantics well explained
- Feature validation emphasized

**Weaknesses:**

- No `action_facts` requirement
- No structured guard decomposition
- Judge relies on generic evaluation
- Security properties format not enforced

### `FSM_GENERATION_PROMPT_TEMPLATE_PARSER` (~800 lines)

**Strengths:**

- v2.0 schema with all required fields
- `action_facts` mandatory with params
- `guard_features` + `guard_attributes` decomposition
- Structured `security_properties` with formula types
- Explicit consistency rules

**Weaknesses:**

- Longer, more complex prompt
- More tokens required for generation
- Stricter validation may cause more rejections

### `FSM_JUDGE_PROMPT_TEMPLATE` (~300 lines)

**Validation Checklist Enforces:**

1. Features section presence
2. Action facts structure
3. Guard decomposition consistency
4. Security property references
5. Variable categorization
6. No fabricated security properties

---

## Strengths and Weaknesses

### Strategy 1: LLM Way

| Strengths                            | Weaknesses                          |
| ------------------------------------ | ----------------------------------- |
| Flexible handling of ambiguous specs | Inconsistent Tamarin output         |
| Can infer missing information        | 5-10 retry loops common             |
| Adapts to unusual cluster structures | High API cost                       |
| Good for exploratory analysis        | Syntax errors require manual fixing |
|                                      | No structured security properties   |
|                                      | Judge doesn't validate schema       |

### Strategy 2: Parser Way

| Strengths                      | Weaknesses                              |
| ------------------------------ | --------------------------------------- |
| Deterministic Tamarin output   | Requires strict FSM schema              |
| Zero syntax errors             | Less flexible with ambiguous input      |
| Rich action label tracing      | Parser needs maintenance for edge cases |
| Auto-generated security lemmas | More complex prompt                     |
| Single-pass conversion         | Schema violations cause rejection       |
| Lower API cost                 |                                         |

---

## OUTPUT ANALYSIS: What Each Strategy Captures vs Misses

### FSM Output Comparison (OnOff Cluster)

| Aspect           | Strategy 1 (LLM)                             | Strategy 2 (Parser)                      | Analysis                                           |
| ---------------- | -------------------------------------------- | ---------------------------------------- | -------------------------------------------------- |
| **File Size**    | 903 lines                                    | 1994 lines                               | Strategy 2 is 2.2x larger                          |
| **States**       | 4 (Off_Idle, On_Idle, Timed_On, Delayed_Off) | 4 (BaseOff, BaseOn, TimedOn, DelayedOff) | ✅ Equal - both capture all states                 |
| **Transitions**  | ~60 transitions                              | 29 transitions                           | ⚠️ Strategy 1 has more due to feature combinations |
| **State Naming** | Semantic names with `_Idle` suffix           | Simpler `Base*` prefix                   | Strategy 1 more descriptive                        |

### What Strategy 1 Captures That Strategy 2 MISSES ❌

#### 1. **Missing: Definitions Section (15 terms)**

Strategy 1 includes rich domain definitions:

```json
"definitions": [
  {"term": "feature_LT", "definition": "A boolean derived from FeatureMap..."},
  {"term": "OnOffControl_AcceptOnlyWhenOn", "definition": "..."},
  {"term": "store_global_scene()", "definition": "An abstract operation..."},
  {"term": "recall_global_scene()", "definition": "..."},
  {"term": "0xFFFF timer sentinel", "definition": "..."}
  // ... 10 more terms
]
```

**Impact**: Loss of domain semantics for understanding FSM behavior.

#### 2. **Missing: References Section (6 references)**

```json
"references": [
  {"id": "0xFFFD", "name": "FeatureMap"},
  {"id": "Scenes Management Cluster", "name": "..."},
  {"id": "0x0008", "name": "Level Control Cluster"}
]
```

**Impact**: Loss of cross-cluster dependency information.

#### 3. **Missing: Scene Behaviors (3 behaviors)**

```json
"scene_behaviors": [
  "When GlobalSceneControl is TRUE and OffWithEffect is received...",
  "When GlobalSceneControl is FALSE and OnWithRecallGlobalScene...",
  "The OnOff attribute is scene-capable..."
]
```

**Impact**: Loss of scene interaction semantics.

#### 4. **Missing: Data Types Used**

```json
"data_types_used": ["OnOffControlBitmap", "StartUpOnOffEnum", "EffectIdentifierEnum"]
```

**Impact**: Loss of type information for formal verification.

#### 5. **⚠️ CRITICAL Missing: Startup Transitions**

Strategy 1 FSM includes these Startup-related transitions:

```json
{"trigger": "Startup", "guard_condition": "feature_LT == TRUE && StartUpOnOff_is_null == TRUE && PreviousOnOff == TRUE"},
{"trigger": "Startup", "guard_condition": "feature_LT == TRUE && StartUpOnOff_value == StartUpOnOffEnum_On"},
{"trigger": "Startup", "guard_condition": "feature_LT == TRUE && StartUpOnOff_value == StartUpOnOffEnum_Toggle"}
```

**Impact**: Startup behavior not modeled in Strategy 2's FSM - **significant for power-cycle security analysis**.

#### 6. **Missing: Rich State Invariants**

Strategy 1 state invariants are more comprehensive:

```json
"invariants": [
  "OnOff == FALSE",
  "feature_LT == FALSE || OnTime == 0 || OnTime == 0xFFFF",
  "feature_LT == FALSE || OffWaitTime == 0 || OffWaitTime == 0xFFFF"
]
```

Strategy 2 has simplified invariants: `"invariants": ["OnOff == FALSE"]`

#### 7. **Missing: Timing Requirements**

Strategy 1 includes per-transition timing info:

```json
"timing_requirements": "Stops any active OnWithTimedOff timers"
```

### What Strategy 2 Captures That Strategy 1 MISSES ✅

#### 1. **Has: Protocol Messages Definition**

```json
"protocol_messages": [
  {"name": "Off_Request", "direction": "client_to_server", "command_id": "0x00"},
  {"name": "Off_Response", "direction": "server_to_client", "fields": [{"name": "status"}]}
]
```

**Benefit**: Complete message specification for Tamarin In/Out facts.

#### 2. **Has: Action Facts Definition (23 facts)**

```json
"action_facts": [
  {"name": "OffReceived", "params": ["endpoint"]},
  {"name": "OnNotSupportedOffOnly", "params": ["endpoint"]}
]
```

**Benefit**: Enables precise security lemma formulation.

#### 3. **Has: Per-Transition Action Facts Emitted**

```json
"action_facts_emitted": [
  {"name": "OffReceived", "args": ["endpoint"]},
  {"name": "OffAccepted", "args": ["endpoint"]}
]
```

**Benefit**: Direct mapping to Tamarin rule action labels.

#### 4. **Has: Guard Decomposition**

```json
"guard_features": [{"name": "OFFONLY", "value": "TRUE"}],
"guard_attributes": [{"name": "OnOff", "operator": "==", "value": "TRUE"}]
```

**Benefit**: Machine-parseable guards for deterministic rule generation.

### Tamarin Output Comparison

| Aspect                   | Strategy 1 (LLM-Generated)                            | Strategy 2 (Parser-Generated)                       |
| ------------------------ | ----------------------------------------------------- | --------------------------------------------------- |
| **File Size**            | 522 lines                                             | 798 lines                                           |
| **State Representation** | Positional tuple `St(tid, state, OnOff, OnTime, ...)` | Individual facts `ServerState(endpoint, 'BaseOff')` |
| **Startup Rules**        | ✅ Yes - 6 startup rules                              | ❌ No startup rules                                 |
| **Timer Abstraction**    | `tv_zero`, `tv_pos`, `tv_ffff`                        | String states                                       |
| **Action Labels**        | `Command(tid, 'Off')`                                 | `Off(endpoint)`, `OffReceived(endpoint)`            |
| **Lemmas**               | 1 sources lemma                                       | 5 reachability lemmas                               |
| **Syntax Errors**        | Possible (LLM-generated)                              | Zero (deterministic)                                |

### Critical Finding: Information Loss in Strategy 2

| Category                | Items Lost           | Severity     |
| ----------------------- | -------------------- | ------------ |
| Definitions             | 15 domain terms      | Medium       |
| References              | 6 cross-cluster refs | Low          |
| Scene Behaviors         | 3 behaviors          | High         |
| Data Types              | 5 enum types         | Medium       |
| **Startup Transitions** | **~6 transitions**   | **Critical** |
| Rich Invariants         | Complex conditions   | High         |
| Timing Requirements     | Per-transition info  | Medium       |

---

## Recommendations for Improvement

### IMPORTANT: Answer to Your Question

**Should you just follow Strategy 2?**

**No, not directly.** Strategy 2's FSM is **missing critical information** that Strategy 1 captures:

1. **Startup transitions** - Critical for power-cycle security analysis
2. **Definitions & References** - Important for documentation
3. **Scene behaviors** - Important for scene-based attacks
4. **Rich invariants** - Important for verification precision

**BUT**, Strategy 2's **Tamarin parser** is excellent - zero syntax errors, deterministic output.

### Recommended Hybrid Approach

**The Best Solution: Merge Both Strategies**

```
┌─────────────────────────────────────────────────────────────┐
│  NEW v2.1 FSM Schema = v2.0 + v1.0 Missing Elements         │
├─────────────────────────────────────────────────────────────┤
│ From v2.0 (Strategy 2):                                     │
│   ✅ action_facts, guard_features, guard_attributes         │
│   ✅ protocol_messages, action_facts_emitted                │
│   ✅ security_properties with formula structure             │
├─────────────────────────────────────────────────────────────┤
│ Add from v1.0 (Strategy 1):                                 │
│   ✅ definitions (15 domain terms)                          │
│   ✅ references (6 cross-cluster refs)                      │
│   ✅ scene_behaviors (3 behaviors)                          │
│   ✅ data_types_used                                        │
│   ✅ timing_requirements per transition                     │
│   ✅ Startup transitions with StartUpOnOff handling         │
│   ✅ Rich invariants with feature conditions                │
└─────────────────────────────────────────────────────────────┘
```

**Pipeline:**

```
Cluster Detail JSON
       ↓
┌──────────────────────────────────────┐
│ cluster_fsm_generator_for_parser.py  │
│ (using MERGED v2.1 Prompt)           │
│ (using FSM_JUDGE_PROMPT_TEMPLATE)    │
└──────────────────────────────────────┘
       ↓
   FSM v2.1 JSON (complete!)
       ↓
┌──────────────────────────────────────┐
│ cluster_tamarin_parser.py (updated)  │
│ + Startup rule generation            │
│ (deterministic conversion)           │
└──────────────────────────────────────┘
       ↓
   Complete Tamarin .spthy
```

### Recommendation 1: Adopt v2.0 Schema for Strategy 1

**Change `cluster_fsm_generator_for_llm.py`:**

```python
# Current
from config import FSM_GENERATION_PROMPT_TEMPLATE_LLM

# Recommended
from config import FSM_GENERATION_PROMPT_TEMPLATE_PARSER
```

**Impact:** FSM output will include `action_facts`, `guard_features`, `action_facts_emitted`

### Recommendation 2: Use Structured Judge

**Change `cluster_fsm_generator_for_llm.py`:**

```python
# Current: Generic judge
def judge_fsm(self, fsm, user_input):
    prompt = "You are a judge that evaluates correctness..."

# Recommended: Structured judge
from config import FSM_JUDGE_PROMPT_TEMPLATE

def judge_fsm(self, fsm, user_input):
    prompt = FSM_JUDGE_PROMPT_TEMPLATE.format(fsm=fsm, cluster_info=user_input)
```

**Impact:** Judge validates v2.0 schema compliance before approval

### Recommendation 3: Replace LLM Tamarin Generator with Parser

**Change `cluster_tamarin_generator.py`:**

```python
# Current: LLM-based conversion
def convert_fsm_to_tamarin(self, fsm_data):
    prompt = FSM_TO_TAMARIN_PROMPT_TEMPLATE.format(...)
    response = self.converter.invoke(prompt)
    # ... 10 retry loop with judge

# Recommended: Deterministic parser
from cluster_tamarin_parser import GeneralizedFSMParserV2

def convert_fsm_to_tamarin(self, fsm_data):
    parser = GeneralizedFSMParserV2(fsm_data)
    return parser.parse()  # Single pass, no retries
```

**Impact:**

- Zero syntax errors
- Consistent output
- ~10x faster (no retries)
- ~10x cheaper (fewer API calls)

### Recommendation 4: Unified Pipeline

```
Cluster Detail JSON
       ↓
┌──────────────────────────────────────┐
│ cluster_fsm_generator_for_llm.py     │
│ (using FSM_GENERATION_PROMPT_PARSER) │
│ (using FSM_JUDGE_PROMPT_TEMPLATE)    │
└──────────────────────────────────────┘
       ↓
   FSM v2.0 JSON
       ↓
┌──────────────────────────────────────┐
│ cluster_tamarin_parser.py            │
│ (deterministic conversion)           │
└──────────────────────────────────────┘
       ↓
   Tamarin .spthy
```

---

## Implementation Roadmap

### Phase 1: Create v2.1 FSM Schema (High Priority)

**Update `FSM_GENERATION_PROMPT_TEMPLATE_PARSER` in config.py:**

Add these required sections to the schema:

```json
{
  "fsm_model": {
    // ... existing v2.0 fields ...

    // ADD FROM v1.0:
    "definitions": [
      { "term": "...", "definition": "...", "usage_context": "..." }
    ],
    "references": [{ "id": "...", "name": "...", "description": "..." }],
    "scene_behaviors": ["..."],
    "data_types_used": ["..."],

    // ADD Startup transitions requirement
    "transitions": [
      // ... existing transitions ...
      {
        "trigger": "Startup",
        "guard_condition": "StartUpOnOff handling..."
        // ...
      }
    ]
  }
}
```

### Phase 2: Update Tamarin Parser (Medium Priority)

**Update `cluster_tamarin_parser.py`:**

Add Startup rule generation:

```python
def _generate_startup_rules(self):
    """Generate Tamarin rules for Startup transitions."""
    startup_transitions = [t for t in self.transitions if t.get('trigger') == 'Startup']
    rules = []
    for trans in startup_transitions:
        rules.append(self._generate_startup_rule(trans))
    return '\n\n'.join(rules)
```

### Phase 3: Schema Migration (Low Risk)

1. Update `cluster_fsm_generator_for_llm.py` to use merged prompt
2. Update judge to validate all sections
3. Test with OnOff Cluster
4. Compare output completeness

### Phase 4: Validation & Testing

1. Test with complex clusters (Door Lock, Thermostat)
2. Verify Startup transitions are modeled correctly
3. Add regression tests
4. Document edge cases

### Timeline Estimate

| Phase   | Effort  | Duration | Priority |
| ------- | ------- | -------- | -------- |
| Phase 1 | Medium  | 2-3 days | High     |
| Phase 2 | Medium  | 2-3 days | High     |
| Phase 3 | Low     | 1-2 days | Medium   |
| Phase 4 | Ongoing | 1 week+  | Low      |

---

## FINAL CONCLUSION AND RECOMMENDATION

### The Core Problem

After deep analysis of actual outputs:

| Metric                 | Strategy 1 (LLM)  | Strategy 2 (Parser)    |
| ---------------------- | ----------------- | ---------------------- |
| FSM Transitions        | **57**            | 29                     |
| Startup Transitions    | **6**             | 0                      |
| Tamarin Syntax Errors  | Frequent          | **0**                  |
| Tamarin Retries Needed | 5-10              | **1**                  |
| Action Representation  | Complex (if-else) | **Simple (parseable)** |

### Why Strategy 2's Simplification is CORRECT

Strategy 2 intentionally removed complex actions because:

```
Strategy 1 Actions (CANNOT PARSE):
- store_global_scene()           ← Function call
- OnTime := max(current, field)  ← Complex expression
- if (x) then y := z             ← Conditional logic

Strategy 2 Actions (CAN PARSE):
- {"attribute": "OnOff", "value": "FALSE"}
- {"attribute": "OnTime", "value": "0"}
```

**This simplification is correct for Tamarin.** The problem is Strategy 2's FSM prompt doesn't require Startup transitions.

### Which is More Reliable?

| Component              | Winner         | Reason                                            |
| ---------------------- | -------------- | ------------------------------------------------- |
| **FSM Generation**     | Strategy 1     | More complete (57 vs 29 transitions)              |
| **Tamarin Generation** | **Strategy 2** | Deterministic, zero errors                        |
| **Action Facts**       | **Strategy 2** | 23 defined facts vs basic Command/StateTransition |
| **Security Analysis**  | Strategy 2     | Richer action labels enable better lemmas         |

### FINAL RECOMMENDATION

**Use Strategy 2's architecture BUT fix FSM completeness:**

1. **Keep Strategy 2's Tamarin Parser** - It's more reliable (zero syntax errors)
2. **Keep Strategy 2's simplified actions** - They're parseable
3. **FIX Strategy 2's FSM Prompt** - Add requirement for Startup transitions
4. **FIX Strategy 2's Parser** - Add Startup rule generation

### Specific Changes Needed

**In `FSM_GENERATION_PROMPT_TEMPLATE_PARSER` (config.py):**

```
Add to REQUIRED TRANSITIONS:
- Startup transitions (if cluster has StartUpOnOff attribute)
- All feature combination variants
```

**In `cluster_tamarin_parser.py`:**

```python
def _generate_startup_rules(self):
    """Generate Startup rules if FSM has Startup transitions."""
    startup_trans = [t for t in self.transitions if t.get('trigger') == 'Startup']
    # Generate rules like Strategy 1's LLM-generated Startup rules
```

### Summary Table

| What To Use       | Source                  | Reason                   |
| ----------------- | ----------------------- | ------------------------ |
| FSM Schema        | Strategy 2 (v2.0)       | Parseable structure      |
| FSM Completeness  | Strategy 1              | Has Startup transitions  |
| Tamarin Generator | **Strategy 2 (Parser)** | Deterministic, reliable  |
| Action Facts      | Strategy 2              | Rich labeling for lemmas |

**Parser is more reliable than LLM for Tamarin generation.**  
**But the FSM itself needs to be complete first (add Startup).**

---

## Appendix: File Reference

| File                                  | Purpose                       | Lines |
| ------------------------------------- | ----------------------------- | ----- |
| `config.py`                           | All prompts and configuration | 3873  |
| `matter_toc_extractor.py`             | TOC extraction from PDF       | 363   |
| `cluster_detail_extractor.py`         | Cluster detail extraction     | 798   |
| `cluster_fsm_generator_for_llm.py`    | Strategy 1 FSM generation     | 273   |
| `cluster_tamarin_generator.py`        | Strategy 1 Tamarin conversion | 624   |
| `cluster_fsm_generator_for_parser.py` | Strategy 2 FSM generation     | 312   |
| `cluster_tamarin_parser.py`           | Strategy 2 Tamarin parsing    | 1016  |

---

_End of Research Analysis - December 24, 2025_
