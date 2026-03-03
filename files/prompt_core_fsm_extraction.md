# FSM Extraction Prompt for Protocol Specifications

## Objective
Extract a complete, sound Finite State Machine from protocol specification sections. Capture ALL details including cryptographic functions, state transitions, guards, and behavioral constraints. Output must be formally verifiable (ProVerif/Tamarin-compatible).

---

## Core Extraction Methodology

### Step 1: Behavioral Analysis
- Identify state-defining attributes and their value combinations
- Extract all conditional logic from descriptions (if/then/else)
- Identify timers, counters, and automatic transitions
- Extract cryptographic operations and key material handling
- Document all function calls and their parameters
- Identify all constraints and invariants

### Step 2: State Identification
- States = meaningful system configurations (not internal processing steps)
- Use attribute values and state variables to define invariants
- Include timer states (active, expired, reset)
- Include error/fault states if reachable
- Model security-critical states (compromised, verified, authenticated)
- Example: "KeyRotationInProgress" (timer_active=true, old_key_valid=true, new_key_staging=true)

### Step 3: Transition Modeling
- **Parse behavioral descriptions** for exact state changes
- **Split conditionals**: Each if/else branch → separate transition with guard
- **Model timer expiry**: Automatic transitions when timer reaches zero
- **Include guard conditions**: All preconditions from spec
- **Define actions atomically**: No control flow (if/else/loops) in actions
- **Capture events**: Model event generation per spec
- **Include stay transitions**: When conditions don't cause state change
- **Add all function calls**: Every function used must be defined

### Step 4: Action Requirements (Atomic Operations)
Actions MUST be simple, non-branching:
- `attribute := value` (assignment)
- `generate_event(event_name)` (event generation)
- `call_function(params)` (function invocation - function must be defined)
- `timer := duration` (timer initialization)

**FORBIDDEN in actions**:
- ❌ if/else, loops, conditionals
- ❌ Complex logic (move logic to guard conditions)

### Step 5: Guard Conditions (Where Logic Lives)
ALL branching logic goes here:
- ❌ WRONG: Action = `"if rate != 0 then move()"`
- ✅ CORRECT: Transition 1: Guard = `"rate != 0"`, Action = `["move()"]`
- ✅ CORRECT: Transition 2: Guard = `"rate == 0"`, Action = `["no_op()"]`

Guard syntax: Use boolean expressions with `&&` (AND) and `||` (OR)

### Step 6: Function Definitions
**CRITICAL**: Every function referenced in actions MUST be defined.

For each function, provide:
- **Name**: Exact function name as used
- **Parameters**: Input parameters with types
- **Returns**: Output/return value
- **Behavior**: Plain English description (NO pseudocode, NO algorithms)
- **Usage**: Where/why called in transitions
- **Cryptographic detail**: If crypto function, include algorithm, key input, output format

**Examples**:
```
Function: derive_operational_key
Parameters: epoch_key (128-bit), fabric_id (64-bit)
Returns: operational_key (128-bit)
Behavior: Apply KDF with epoch_key as input and CompressedFabricIdentifier as salt, Info="GroupKey v1.0"
Usage: Called when transitioning to KeyValid state after key rotation
```

```
Function: verify_epoch_key_signature
Parameters: epoch_key (128-bit), signature (bitstring), admin_cert (X.509)
Returns: boolean (true if valid, false if invalid)
Behavior: ECDSA verification of epoch key using admin certificate public key
Usage: Called when receiving new epoch key from administrator
```

### Step 7: Cryptographic Detail Capture
For every cryptographic operation in spec:
- Algorithm name (KDF, DRBG, ECDSA, AES-CCM, etc.)
- Input parameters (keys, salts, IVs, data)
- Output format and length
- Any assumptions (KDF is secure, no key leakage, etc.)
- Where in FSM this operation occurs

Model as:
- **Transitions** with guards checking crypto preconditions
- **Actions** calling crypto functions
- **Functions** defining crypto operations in detail
- **Definitions** explaining cryptographic assumptions

### Step 8: All Conditional Logic → Separate Transitions
When spec says: "If X, then do A. Else if Y, then do B. Else do C"

Create THREE transitions:
```
Transition 1: Guard="X", Actions=[A]
Transition 2: Guard="Y && !X", Actions=[B]
Transition 3: Guard="!X && !Y", Actions=[C]
```

### Step 9: Timer Semantics
- Model timer start: `timer := duration_value`
- Model timer decrement: Stay transition when `timer > 0`
- Model timer expiry: Transition when `timer == 0` (automatic)
- Model timer reset: Action `timer := new_duration`
- Document resolution (milliseconds, seconds, etc.)

### Step 10: Security & Access Control
- States for privilege levels (authenticated, admin, member, non_member)
- Transitions gated by access control checks
- Functions for ACL enforcement, signature verification, key checking
- Model revocation as state transitions
- Model unauthorized access attempts as blocked transitions or error states

---

## Analysis Procedure (13 Steps)

1. **Identify section type**: Is it key management, state machine, protocol flow, cryptographic operation, access control, timing, etc.?
2. **Extract key attributes**: Values that define system state
3. **Parse all descriptions**: Look for "SHALL", "MUST", "if/then", "state X", "transition to Y"
4. **Identify conditional branches**: Every if/else becomes separate transitions
5. **List all operations**: Commands, functions, timers, events
6. **Map state combinations**: Which attributes in combination = which state?
7. **Extract cryptographic operations**: Algorithm, inputs, outputs, assumptions
8. **Document all functions**: Every function used → must be defined completely
9. **Create transitions**: Source state + guard + action → target state
10. **Add timer modeling**: Timers as state attributes, automatic expiry transitions
11. **Include error paths**: Reachable failure states, security violations
12. **Model security properties**: Access control, authentication, revocation
13. **Validate completeness**: All commands/operations/conditions covered?

---

## Output Schema (JSON)

```json
{
  "fsm_model": {
    "section_name": "string (e.g., '4.17 Group Key Management')",
    "section_ref": "string (e.g., 'Matter 1.4 Core Specification, Section X.Y')",
    "states": [
      {
        "name": "state_name",
        "description": "what this state represents",
        "is_initial": true/false,
        "invariants": ["condition1", "condition2"],
        "state_variables": {"var_name": "type_and_range"}
      }
    ],
    "transitions": [
      {
        "from_state": "source",
        "to_state": "target",
        "trigger": "command_name or event_name or timer_expiry",
        "guard_condition": "boolean_expression (X > 0 && Y == Z)",
        "actions": ["action1", "action2"],
        "timing_requirement": "string_or_null"
      }
    ],
    "functions": [
      {
        "name": "function_name",
        "parameters": [{"name": "param1", "type": "type", "description": "what it is"}],
        "return_type": "type",
        "description": "plain_english_what_function_does",
        "algorithm_detail": "if_crypto: algorithm_name, inputs, outputs, assumptions",
        "usage_in_fsm": "which_transitions_call_this"
      }
    ],
    "definitions": [
      {
        "term": "technical_term",
        "definition": "explanation (no pseudocode)",
        "security_relevance": "why_this_matters_for_security_or_null"
      }
    ],
    "security_properties": [
      {
        "property_name": "property_identifier",
        "type": "access_control | revocation | confidentiality | authenticity | consistency | timing | etc",
        "description": "security_guarantee",
        "fsm_states_involved": ["state1", "state2"],
        "critical_transitions": ["transition_id1"]
      }
    ],
    "initial_state": "state_name",
    "all_states": ["state1", "state2", ...],
    "all_triggers": ["command1", "event1", "timer1", ...],
    "all_functions_used": ["func1", "func2", ...],
    "cryptographic_operations": [
      {
        "operation": "operation_name",
        "algorithm": "name",
        "inputs": ["input1", "input2"],
        "output": "output_format_and_length",
        "assumptions": ["assumption1", "assumption2"]
      }
    ],
    "security_assumptions": [
      {
        "assumption": "description",
        "type": "explicit_or_implicit",
        "if_violated": "consequence"
      }
    ],
    "validation_checklist": {
      "no_conditionals_in_actions": true,
      "no_loops_in_actions": true,
      "all_functions_defined": true,
      "all_guards_exclusive_or_exhaustive": true,
      "all_timers_modeled": true,
      "cryptographic_operations_detailed": true,
      "error_states_included": true
    }
  }
}
```

---

## Validation Requirements

- [ ] All functions used in actions are defined in functions[] section
- [ ] No if/else logic in actions (only in guard conditions)
- [ ] No loops in actions
- [ ] Guard conditions are mutually exclusive or properly ordered
- [ ] All timer operations have corresponding expiry transitions
- [ ] Every cryptographic operation documented with algorithm and inputs
- [ ] Error/failure states included
- [ ] Security-critical transitions identified
- [ ] All assumptions (especially implicit ones) listed
- [ ] JSON valid and parseable
- [ ] NO comments in JSON

---

## LLM Instructions

1. **Extract COMPLETE FSM** from provided specification section
2. **Include EVERY detail**: Cryptographic functions, guards, timers, events, security checks
3. **Define ALL functions**: Every function in actions must be defined with algorithm details
4. **Capture security properties**: Identify what security guarantees this section provides
5. **Model error paths**: Don't skip failure states or reachable error conditions
6. **Use guard conditions**: ALL branching logic (if/else) must be in guards, not actions
7. **Atomic actions only**: Actions must be simple assignments, function calls, or event generation
8. **Document assumptions**: List all assumptions, especially implicit cryptographic ones
9. **Be precise**: Match specification text exactly; don't invent behavior
10. **Validate before output**: Check all functions are defined, all triggers modeled, completeness verified

---

## Example: Simple Protocol Operation

**Spec Input**:
```
"If node has current epoch key and timer is active, 
derive operational group key via KDF(epoch_key, fabric_id). 
If derivation succeeds, transition to KeyValid state. 
If derivation fails, remain in KeyDerivationFailed state and generate error_event."
```

**FSM Output**:
```json
{
  "fsm_model": {
    "states": [
      {
        "name": "KeyDerivationInProgress",
        "description": "Attempting to derive operational key from current epoch key",
        "is_initial": false,
        "invariants": ["has_current_epoch_key == true", "timer_active == true"],
        "state_variables": {"current_epoch_key": "128-bit", "timer": "positive_integer"}
      },
      {
        "name": "KeyValid",
        "description": "Operational key successfully derived and ready for use",
        "is_initial": false,
        "invariants": ["operational_key_valid == true", "timer_active == false"],
        "state_variables": {"operational_key": "128-bit"}
      },
      {
        "name": "KeyDerivationFailed",
        "description": "Key derivation failed due to missing preconditions",
        "is_initial": false,
        "invariants": ["derivation_error == true"],
        "state_variables": {"error_reason": "string"}
      }
    ],
    "transitions": [
      {
        "from_state": "KeyDerivationInProgress",
        "to_state": "KeyValid",
        "trigger": "derive_key_command",
        "guard_condition": "has_current_epoch_key == true && timer_active == true",
        "actions": [
          "operational_key := derive_operational_key(current_epoch_key, fabric_id)",
          "timer := 0",
          "generate_event(key_derivation_success)"
        ],
        "timing_requirement": null
      },
      {
        "from_state": "KeyDerivationInProgress",
        "to_state": "KeyDerivationFailed",
        "trigger": "derive_key_command",
        "guard_condition": "has_current_epoch_key == false || timer_active == false",
        "actions": [
          "derivation_error := true",
          "error_reason := derive_error_reason()",
          "generate_event(key_derivation_failure)"
        ],
        "timing_requirement": null
      }
    ],
    "functions": [
      {
        "name": "derive_operational_key",
        "parameters": [
          {"name": "epoch_key", "type": "128-bit_key", "description": "input epoch key from administrator"},
          {"name": "fabric_id", "type": "64-bit_identifier", "description": "compressed fabric identifier"}
        ],
        "return_type": "128-bit_key",
        "description": "Derives operational group key using KDF",
        "algorithm_detail": "HKDF-SHA256: InputKey=epoch_key, Salt=CompressedFabricIdentifier, Info='GroupKey v1.0', OutputLength=128bits. Returns derived key suitable for AES-CCM encryption.",
        "usage_in_fsm": "Called in KeyDerivationInProgress->KeyValid transition to produce encryption key from epoch material"
      },
      {
        "name": "derive_error_reason",
        "parameters": [],
        "return_type": "string",
        "description": "Determines reason for failed key derivation",
        "algorithm_detail": "Check preconditions: if has_current_epoch_key==false return 'missing_epoch_key', else if timer_active==false return 'timer_inactive', else return 'unknown_error'",
        "usage_in_fsm": "Called in error transition to populate error_reason field"
      }
    ],
    "security_properties": [
      {
        "property_name": "KEY_DERIVATION_GUARD",
        "type": "cryptography",
        "description": "Operational key derivation only succeeds with valid preconditions",
        "fsm_states_involved": ["KeyDerivationInProgress", "KeyValid", "KeyDerivationFailed"],
        "critical_transitions": ["KeyDerivationInProgress->KeyValid", "KeyDerivationInProgress->KeyDerivationFailed"]
      }
    ],
    "all_functions_used": ["derive_operational_key", "derive_error_reason"]
  }
}
```

---

## Notes

- **Precision**: This FSM will be used for formal verification. Every detail matters.
- **Completeness**: Don't skip edge cases, error conditions, or security checks.
- **Soundness**: The FSM must accurately represent the actual protocol behavior, including what can go wrong.
- **Formal Compatibility**: This FSM will be translated to ProVerif or Tamarin. Keep it strict and unambiguous.