# FSM Extraction Prompt for Application Cluster Specifications

## Objective

Extract a complete, sound Finite State Machine from Matter Application Cluster specifications. Capture ALL details including command behaviors, attribute transitions, events, access control requirements, and safety constraints. Output must be formally verifiable (ProVerif/Tamarin-compatible).

---

## Application Cluster vs Protocol FSMs (Key Differences)

| Aspect               | Core Protocol FSM              | Application Cluster FSM                        |
| -------------------- | ------------------------------ | ---------------------------------------------- |
| **State Definition** | Session/key states             | Operational modes + attribute combinations     |
| **Transitions**      | Cryptographic handshakes       | Commands with "Effect on Receipt"              |
| **Security Focus**   | Key derivation, authentication | Access control (V/O/M/A), authorization bypass |
| **Safety Impact**    | Data confidentiality           | Physical safety (locks, valves, alarms)        |
| **Timing**           | Session timeouts               | Auto-relock, timed commands, schedules         |
| **Events**           | Protocol completion            | StateChange, Alarm, Fault events               |

---

## Core Extraction Methodology

### Step 1: Cluster Structure Analysis

- Identify the cluster's **Feature Map** (feature flags that enable/disable capabilities)
- Extract the **PICS Code** (mandatory vs optional conformance)
- Identify **Dependencies** (clusters that must co-exist on the endpoint)
- Document the cluster's **Classification** (Base/Derived, Application/Utility, Endpoint scope)

### Step 2: State Identification

States in application clusters are defined by:

1. **Primary State Attributes**: Look for attributes named `*State`, `*Status`, `*Mode`
   - Examples: `LockState`, `OperationalState`, `AlarmState`, `Mode`, `CurrentState`
2. **Secondary State Modifiers**: Attributes that modify behavior within a primary state
   - Examples: `TargetState`, `Occupancy`, `FaultState`, `ConfigStatus`
3. **Feature-Conditional States**: States that only exist when a feature is enabled
   - Example: `UnboltState` only exists when `UBOLT` feature is supported

4. **Composite States**: Combinations of attributes that together define system behavior
   - Example: Door Lock state = (`LockState`, `DoorState`, `OperatingMode`)

**State Invariants**: For each state, document:

- Which attribute values define this state
- Which features must be enabled
- Physical/safety meaning of the state

### Step 3: Transition Extraction from Commands

For each command in the cluster:

1. **Parse "Effect on Receipt" Section**: This is the authoritative source for transition behavior
2. **Identify Preconditions**: Extract all `SHALL`/`MUST` requirements
3. **Identify Postconditions**: Document attribute modifications
4. **Extract Error Conditions**: Identify when command fails and what status is returned
5. **Note Timing Behaviors**: Look for timeouts, delays, ramp rates

**Command Access Levels** (Critical for security):
| Level | Symbol | Meaning | Risk Level |
|-------|--------|---------|------------|
| View | V | Read-only | Low |
| Operate | O | Basic actuation | Medium |
| Manage | M | Configuration changes | High |
| Administer | A | Full control | Critical |

### Step 4: Event-Driven Transitions

Events can trigger state changes or indicate state reached:

- **State Change Events**: Generated AFTER attribute changes (e.g., `AlarmNotification`, `DoorStateChange`)
- **Fault Events**: Generated on error conditions (e.g., `ValveFault`, `OperationalError`)
- **Periodic Events**: Generated on schedules (e.g., `AlarmsStateChanged`)

### Step 5: Conditional Logic → Separate Transitions

**CRITICAL**: All branching in "Effect on Receipt" must become separate transitions

Spec text: "If the door is locked, reject command; else if PIN is valid, unlock; else increment failure counter"

Becomes THREE transitions:

```
Transition 1: Guard="DoorState==Locked", Action=[return FAILURE]
Transition 2: Guard="DoorState!=Locked && PIN_valid", Action=[LockState:=Unlocked]
Transition 3: Guard="DoorState!=Locked && !PIN_valid", Action=[FailureCount:=FailureCount+1]
```

### Step 6: Action Requirements (Atomic Operations)

Actions MUST be simple, non-branching:

- `attribute := value` (assignment)
- `generate_event(event_name, fields)` (event generation)
- `call_function(params)` (function invocation)
- `timer := duration` (timer initialization)
- `return status_code` (command response)

**FORBIDDEN in actions**:

- ❌ if/else, loops, conditionals
- ❌ Complex logic (move to guard conditions)

### Step 7: Feature Flag Handling

Feature flags affect:

- Which attributes exist
- Which commands are available
- Which transitions are valid

Model as **guards on transitions**:

```
Guard: "Feature_UBOLT == true && LockState == Locked"
```

### Step 8: Timer and Schedule Semantics

Application clusters heavily use timing:

- **Auto-relock timers**: `AutoRelockTime`
- **Timed commands**: `OnWithTimedOff`, `UnlockWithTimeout`
- **Schedules**: `WeekDaySchedule`, `YearDaySchedule`, `HolidaySchedule`

Model timers as:

- Timer start: `timer := duration_value`
- Timer check: Guard `timer > 0`
- Timer expiry: Automatic transition when `timer == 0`

### Step 9: Safety and Access Control

For each transition, document:

- **Required Privilege Level**: V, O, M, or A
- **Timed Interaction Requirement**: Does command require Timed Invoke?
- **Fabric Scoping**: Is data isolated per fabric?
- **Physical Safety Implications**: What real-world impact does this have?

---

## Analysis Procedure (15 Steps)

1. **Identify Cluster Type**: Measurement, Actuation, Control, Safety, Media, Energy, etc.
2. **Extract Feature Map**: Document all feature flags and their implications
3. **Identify Primary State Attribute(s)**: Find the main *State/*Status/\*Mode attribute
4. **Map Attribute Combinations**: Which combinations form valid states?
5. **Parse Each Command's "Effect on Receipt"**: Extract transitions systematically
6. **Document Access Levels**: For each command, note V/O/M/A requirement
7. **Identify Error Paths**: When does command fail? What status code returns?
8. **Extract Events**: What generates events? What do they contain?
9. **Model Timers**: Auto-relock, timed commands, schedules
10. **Identify Feature-Conditional Behavior**: Which transitions need feature flags?
11. **Document Constraints**: Numeric limits, enums, valid ranges
12. **Map Dependencies**: Other clusters on same endpoint that interact
13. **Identify Safety-Critical Transitions**: Which could cause physical harm?
14. **Check for Spec Gaps**: MAY vs SHALL, missing constraints, ambiguous behavior
15. **Validate Completeness**: All commands, attributes, events covered?

---

## Output Schema (JSON)

```json
{
  "cluster_fsm": {
    "cluster_name": "string (e.g., 'Door Lock')",
    "cluster_id": "hex (e.g., '0x0101')",
    "pics_code": "string (e.g., 'DRLK')",
    "spec_reference": "Matter 1.5 Application Cluster Specification, Section X.Y, Pages P1-P2",
    "revision": "integer (current cluster revision)",

    "features": [
      {
        "bit": 0,
        "code": "PIN",
        "name": "PINCredential",
        "conformance": "O",
        "description": "Lock supports PIN credentials",
        "affects_states": ["state1", "state2"],
        "affects_transitions": ["transition_id1"]
      }
    ],

    "dependencies": [
      {
        "cluster": "On/Off",
        "relationship": "SHALL_COEXIST",
        "description": "Required on same endpoint for Dead Front behavior"
      }
    ],

    "states": [
      {
        "name": "state_name",
        "description": "physical/operational meaning",
        "is_initial": true/false,
        "invariants": ["attribute1 == value1", "attribute2 == value2"],
        "state_attributes": {
          "PrimaryState": "value",
          "SecondaryModifier": "value"
        },
        "feature_requirements": ["Feature_X == true"],
        "safety_implications": "string_or_null (what physical risk does this state pose?)"
      }
    ],

    "transitions": [
      {
        "id": "T001",
        "from_state": "source",
        "to_state": "target",
        "trigger": {
          "type": "command|event|timer|attribute_change",
          "name": "trigger_name",
          "command_id": "hex_or_null"
        },
        "guard_condition": "boolean_expression (Feature_X == true && attr > 0)",
        "actions": ["action1", "action2"],
        "access_required": "V|O|M|A",
        "timed_required": true/false,
        "timing_constraint": "string_or_null",
        "error_responses": [
          {
            "condition": "when this occurs",
            "status_code": "INVALID_COMMAND|FAILURE|CONSTRAINT_ERROR|etc",
            "description": "why this error"
          }
        ],
        "spec_reference": "Section X.Y.Z.N.M 'Effect on Receipt'"
      }
    ],

    "events": [
      {
        "id": "hex",
        "name": "EventName",
        "priority": "DEBUG|INFO|CRITICAL",
        "generated_by": ["transition_id1", "transition_id2"],
        "fields": [
          {"name": "field1", "type": "type", "description": "desc"}
        ],
        "description": "when and why this event is generated"
      }
    ],

    "timers": [
      {
        "name": "timer_name",
        "source_attribute": "AutoRelockTime",
        "trigger": "what starts this timer",
        "expiry_transition": "transition_id on expiry",
        "resolution": "seconds|milliseconds"
      }
    ],

    "functions": [
      {
        "name": "function_name",
        "parameters": [{"name": "param1", "type": "type", "description": "desc"}],
        "return_type": "type",
        "description": "plain_english_behavior (NO pseudocode)",
        "usage_in_fsm": "which transitions call this"
      }
    ],

    "access_control_summary": {
      "view_commands": ["cmd1"],
      "operate_commands": ["cmd2", "cmd3"],
      "manage_commands": ["cmd4"],
      "administer_commands": ["cmd5"],
      "timed_commands": ["cmd6"]
    },

    "safety_critical_elements": [
      {
        "element_type": "state|transition|attribute",
        "element_id": "identifier",
        "safety_concern": "description of physical safety risk",
        "mitigation_in_spec": "what spec says to prevent harm (or 'NONE' if unspecified)"
      }
    ],

    "spec_gaps": [
      {
        "location": "Section X.Y.Z",
        "gap_type": "ambiguous|missing_constraint|weak_normative|undefined_behavior",
        "description": "what is missing or unclear",
        "security_impact": "how this gap could be exploited"
      }
    ],

    "initial_state": "state_name",
    "all_states": ["state1", "state2"],
    "all_triggers": ["cmd1", "event1", "timer1"],

    "validation_checklist": {
      "no_conditionals_in_actions": true,
      "all_commands_mapped": true,
      "all_events_mapped": true,
      "all_features_handled": true,
      "access_control_documented": true,
      "timers_modeled": true,
      "error_paths_included": true,
      "safety_implications_noted": true
    }
  }
}
```

---

## Validation Requirements

- [ ] All commands from specification are mapped to transitions
- [ ] All attributes with `*State/*Status/*Mode` are included in state definitions
- [ ] No if/else logic in actions (only in guard conditions)
- [ ] Every command has access level documented (V/O/M/A)
- [ ] Timed commands are marked
- [ ] All events have their generation conditions documented
- [ ] All timers have expiry transitions
- [ ] Feature-conditional behavior uses guards
- [ ] Error responses included for each command
- [ ] Safety-critical elements identified
- [ ] Spec gaps documented with security impact
- [ ] JSON is valid and parseable

---

## LLM Instructions

1. **Extract COMPLETE Cluster FSM** from provided specification section
2. **Parse "Effect on Receipt" CAREFULLY**: This is the primary source of transition logic
3. **Document ALL access levels**: Security depends on knowing who can do what
4. **Identify Safety Implications**: Locks, valves, alarms have real-world impact
5. **Use Feature Guards**: Don't create transitions for disabled features
6. **Include Error Paths**: Commands can fail — model when and why
7. **Model Timers**: Application clusters use timing extensively
8. **Document Spec Gaps**: MAY vs SHALL, missing constraints, ambiguous text
9. **Be Precise**: Match specification text exactly; don't invent behavior
10. **Validate Before Output**: Check all commands, attributes, events are covered

---

## Example: Door Lock Cluster (Partial)

**Spec Input**:

```
5.2.10.1 Lock Door Command
Upon receipt of this command, the device SHALL lock the door. This command is valid
only in specific OperatingModes: Normal, Vacation, No Remote Lock Unlock. If received
in other modes, SHALL return FAILURE status.

If RequirePINForRemoteOperation is TRUE and the PINCredential feature is supported,
the command SHALL include a valid PINCode field. If missing or invalid, return FAILURE.

Upon successful lock, the DoorLockOperationEvent SHALL be generated.
Access: OPERATE privilege required.
```

**FSM Output (Partial)**:

```json
{
  "cluster_fsm": {
    "cluster_name": "Door Lock",
    "cluster_id": "0x0101",
    "pics_code": "DRLK",

    "states": [
      {
        "name": "Unlocked_Normal",
        "description": "Door is unlocked and lock is in Normal operating mode",
        "is_initial": false,
        "invariants": ["LockState == Unlocked", "OperatingMode == Normal"],
        "state_attributes": {
          "LockState": "Unlocked",
          "OperatingMode": "Normal"
        },
        "feature_requirements": [],
        "safety_implications": "Physical entry permitted - security risk if unauthorized"
      },
      {
        "name": "Locked_Normal",
        "description": "Door is locked and lock is in Normal operating mode",
        "is_initial": true,
        "invariants": ["LockState == Locked", "OperatingMode == Normal"],
        "state_attributes": {
          "LockState": "Locked",
          "OperatingMode": "Normal"
        },
        "feature_requirements": [],
        "safety_implications": "Physical entry denied"
      }
    ],

    "transitions": [
      {
        "id": "T001",
        "from_state": "Unlocked_Normal",
        "to_state": "Locked_Normal",
        "trigger": {
          "type": "command",
          "name": "LockDoor",
          "command_id": "0x00"
        },
        "guard_condition": "OperatingMode IN [Normal, Vacation, NoRemoteLockUnlock] && (!RequirePINForRemoteOperation || PIN_valid)",
        "actions": [
          "LockState := Locked",
          "generate_event(DoorLockOperationEvent, {LockOperationType: Lock, OperationSource: Remote})"
        ],
        "access_required": "O",
        "timed_required": false,
        "error_responses": [
          {
            "condition": "OperatingMode NOT IN [Normal, Vacation, NoRemoteLockUnlock]",
            "status_code": "FAILURE",
            "description": "Lock command not allowed in current operating mode"
          },
          {
            "condition": "RequirePINForRemoteOperation == true && PIN missing/invalid",
            "status_code": "FAILURE",
            "description": "PIN required but not provided or incorrect"
          }
        ],
        "spec_reference": "Section 5.2.10.1 'Lock Door Command' Effect on Receipt"
      }
    ],

    "safety_critical_elements": [
      {
        "element_type": "transition",
        "element_id": "T_UnlockDoor",
        "safety_concern": "Remote unlock without PIN allows unauthorized physical entry",
        "mitigation_in_spec": "RequirePINForRemoteOperation attribute (but OPTIONAL)"
      }
    ],

    "spec_gaps": [
      {
        "location": "Section 5.2.9.32-33",
        "gap_type": "missing_constraint",
        "description": "No minimum value for WrongCodeEntryLimit — could be 255 attempts",
        "security_impact": "Brute force attack on PIN codes feasible"
      }
    ]
  }
}
```

---

## Notes

- **Physical Safety Focus**: Unlike protocol FSMs, cluster FSMs affect the physical world
- **Access Control is Critical**: V/O/M/A levels determine who can execute what
- **Feature Flags Complicate State Space**: Document which features enable which states
- **"Effect on Receipt" is Truth**: Always defer to this section for command behavior
- **MAY vs SHALL**: Weak normative language creates implementation variation = vulnerabilities
- **This FSM enables formal verification**: Must be precise enough for ProVerif/Tamarin
