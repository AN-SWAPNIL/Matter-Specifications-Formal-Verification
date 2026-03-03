# Property Violation Analysis Prompt for Application Cluster Vulnerability Detection

## Objective

For each security property, systematically verify it against the extracted cluster FSM. Determine if the property holds or is violated. Then locate and cite exact specification text supporting the conclusion. Output evidence-based vulnerability assessment with physical safety impact analysis.

---

## Application Cluster vs Protocol Verification (Key Differences)

| Aspect                | Protocol Verification          | Cluster Verification                        |
| --------------------- | ------------------------------ | ------------------------------------------- |
| **Property Focus**    | Cryptographic guarantees       | Access control + safety                     |
| **FSM Tracing**       | Session states                 | Operational states + attribute combinations |
| **Evidence Source**   | Crypto algorithms, key flows   | "Effect on Receipt", access levels          |
| **Impact Assessment** | Data confidentiality/integrity | Physical safety, availability               |
| **Attack Model**      | Network adversary              | Malicious controller, compromised node      |
| **Severity Basis**    | Data breach scope              | Physical harm potential                     |

---

## Core Verification Methodology

### Phase 1: Property Formalization

For each property, establish verification criteria:

**Step 1: Decompose the Property**

```
Property: "Remote Unlock requires valid PIN when RequirePINForRemoteOperation is TRUE"

Components:
- Trigger: UnlockDoor command from remote source
- Precondition: RequirePINForRemoteOperation == TRUE
- Guard Required: HasValidPIN(command.PINCode)
- State Affected: LockState transition Locked→Unlocked
```

**Step 2: Map to FSM Elements**

- Which **transitions** could violate this property?
- Which **guards** enforce it?
- Which **states** are affected?
- Which **attributes** control the behavior?

**Step 3: Identify Verification Conditions**

```
Property HOLDS if:
  ∀ transitions T where T.trigger == UnlockDoor ∧ T.from_state.LockState == Locked:
    T.guard contains (RequirePINForRemoteOperation == false ∨ PIN_valid)

Property VIOLATED if:
  ∃ transition T where T.trigger == UnlockDoor ∧ T.from_state.LockState == Locked ∧
    T.guard does NOT check PIN validity when RequirePINForRemoteOperation == true
```

### Phase 2: FSM Tracing

**Step 1: Identify Relevant Transitions**
List all transitions that:

- Could trigger the property's subject action
- Affect the property's protected state
- Have guards related to the property's condition

**Step 2: Analyze Each Transition**
For each relevant transition, check:

| Check                  | Question                                     | If Missing                            |
| ---------------------- | -------------------------------------------- | ------------------------------------- |
| **Guard Presence**     | Is there a guard that enforces the property? | Property may be violated              |
| **Guard Completeness** | Does guard check ALL required conditions?    | Property partially violated           |
| **Guard Exclusivity**  | Are guard conditions mutually exclusive?     | Non-determinism = potential violation |
| **Action Correctness** | Do actions maintain property invariants?     | Property violated by side effect      |

**Step 3: Trace Attack Paths**
If property appears violated, construct attack path:

```
Attack Path for PROP_DRLK_007 (PIN bypass):
  State_1: Locked_Normal (RequirePINForRemoteOperation == true)
  ↓ Transition: UnlockDoor (no guard checking PIN)
  State_2: Unlocked_Normal

  VIOLATION: Reached Unlocked without PIN validation
```

**Step 4: Consider Feature Flags**

- Property may only apply when certain features enabled
- Check if FSM guards include feature flag checks
- Document if property is conditional on features

### Phase 3: Access Control Verification

For application clusters, verify privilege levels:

**Step 1: Command Access Matrix**
| Command | Required Privilege | Actual Guard | Matches Spec? |
|---------|-------------------|--------------|--------------|
| UnlockDoor | Operate (O) | access_level >= O | ✓ |
| SetCredential | Admin (A) | access_level >= A | ✓ |
| ClearAllPINCodes | Admin (A) | access_level >= M | ✗ VIOLATION |

**Step 2: Privilege Escalation Paths**
Check for transitions where:

- Lower privilege can achieve higher-privilege effect
- Intermediate commands bypass authorization
- State changes grant de facto elevation

### Phase 4: Evidence Collection

#### If Property HOLDS:

1. **Identify Supporting Transitions** (2-3 strongest)
   - Which transitions enforce this property?
   - Quote the guard condition
   - Reference the spec section

2. **Locate Specification Evidence**
   - Find "SHALL", "MUST" text supporting guarantee
   - Extract exact quote with section/page
   - Note conformance level (M, O, conditional)

3. **Document Enabling Assumptions**
   - What must be true externally for property to hold?
   - Are assumptions stated or implicit?
   - Where are assumptions enforced?

**Format**:

```
PROPERTY: [Name]
VERDICT: HOLDS

Supporting Transition:
  From: State_A
  To: State_B
  Guard: [guard condition from FSM]
  Why Holds: [explanation of how guard enforces property]

Specification Evidence:
  Quote: "[exact text with SHALL/MUST from spec]"
  Source: Section X.Y.Z.N, "Subsection Title", Page P
  Access Level: [V/O/M/A required]

Supporting Assumptions:
  1. [Assumption]
     - Type: Explicit | Implicit
     - Source: Section X.Y
     - Criticality: HIGH | MEDIUM | LOW
```

---

#### If Property VIOLATED:

1. **Identify Attack Path** (transition sequence)
   - Start state (initial conditions)
   - Sequence of transitions (commands/events)
   - Final state where property fails
   - Which guard is missing/insufficient

2. **Locate Specification Claim**
   - Quote showing what spec INTENDED
   - Show where spec text is insufficient
   - Identify normative weakness (MAY vs SHALL)

3. **Provide Concrete Attack Scenario**
   - Specific protocol execution
   - What attacker does (commands, timing)
   - Resulting state (property violated)
   - Physical/security impact

4. **Assess Impact Severity**

**Format**:

```
PROPERTY: [Name]
VERDICT: VIOLATED

Attack Path:
  Initial State: State_A [initial conditions]
  → Transition 1: Command_X (Guard: [guard], Access: O)
  → State_B
  → Transition 2: Command_Y (Guard: [guard], Access: O)
  → Final State: State_C [property violation]

Why Violated:
  [Specific explanation of missing/weak guard]

Specification Claim:
  Quote: "[spec text claiming property should hold]"
  Source: Section X.Y.Z, Page P
  Normative Strength: SHALL | SHOULD | MAY

Specification Gap:
  Quote: "[spec text that's insufficient/missing]"
  Source: Section X.Y.Z, Page P
  Gap Type: Missing guard | Weak normative | Undefined behavior | Silent on case

Counterexample Scenario:
  1. Attacker has: [initial capabilities]
  2. Attacker sends: [command sequence]
  3. System transitions: [state sequence]
  4. Result: [property violation + impact]

Severity Assessment:
  Confidentiality Impact: NONE | LOW | MEDIUM | HIGH
  Integrity Impact: NONE | LOW | MEDIUM | HIGH
  Availability Impact: NONE | LOW | MEDIUM | HIGH
  Physical Safety Impact: NONE | LOW | MEDIUM | HIGH | CRITICAL

  Overall Severity: CRITICAL | HIGH | MEDIUM

  Rationale: [Why this severity rating]
```

### Phase 5: Physical Safety Analysis

For safety-critical clusters (Door Lock, Valve, Smoke/CO Alarm, EVSE, etc.), assess:

**Step 1: Identify Safety-Relevant Properties**

- Properties affecting physical access (locks, closures)
- Properties affecting environmental hazards (valves, alarms)
- Properties affecting fire/electrical safety (appliances, EVSE)

**Step 2: Assess Physical Harm Potential**

| Violation Type          | Potential Harm              | Example                 |
| ----------------------- | --------------------------- | ----------------------- |
| Lock bypassed           | Unauthorized physical entry | Burglary                |
| Alarm suppressed        | Undetected hazard           | CO poisoning            |
| Valve open indefinitely | Flooding/gas leak           | Property damage, injury |
| EVSE overcurrent        | Electrical fire             | Property damage, injury |
| Thermostat extremes     | Hypothermia/heat stroke     | Injury                  |

**Step 3: Map Violation → Physical Consequence**

```
Property: Alarm cannot be remotely muted during emergency
Violation: Attacker mutes CO alarm via DeviceMuted attribute
Physical Consequence: Occupants unaware of carbon monoxide
Harm: Potential CO poisoning, death
Severity: CRITICAL
```

### Phase 6: Citation Requirements

**Citation Format** (must be exact and verifiable):

1. **Direct Quote**: Copy exact text from specification
   - Include punctuation, capitalization as in spec
   - Use [...] for brief omissions
   - Mark interpretations as [interpretation]

2. **Source Reference**: Must be precise
   - Chapter: Chapter N
   - Section: Section X.Y.Z
   - Subsection title: "Subsection Name"
   - Page: Page P
   - Paragraph/Table: Paragraph N / Table M / Bullet N

3. **Access Level**: Document required privilege
   - V (View), O (Operate), M (Manage), A (Administer)

4. **Conformance**: Document requirement strength
   - M (Mandatory), O (Optional), Conditional

---

## Analysis Process (Per Property)

### Pre-Analysis Checklist

- [ ] Property clearly stated and formalized?
- [ ] FSM extracted with all transitions, guards, actions?
- [ ] Access levels documented for all commands?
- [ ] Feature flags identified?

### FSM Tracing Checklist

- [ ] All relevant transitions identified?
- [ ] Guards checked for completeness?
- [ ] Attack paths traced if property appears violated?
- [ ] Feature flag interactions considered?

### Access Control Checklist

- [ ] Required privilege level identified from spec?
- [ ] FSM guards check privilege correctly?
- [ ] No privilege escalation paths found?

### Evidence Checklist

- [ ] Specification text located?
- [ ] Exact quote extracted?
- [ ] Source verified (section, page)?
- [ ] Normative strength noted (SHALL/SHOULD/MAY)?

### Impact Assessment Checklist

- [ ] Severity determined (C/H/M)?
- [ ] Physical safety impact assessed?
- [ ] Attack scenario documented?
- [ ] Concrete counterexample provided (if violated)?

---

## Output Schema (JSON)

```json
{
  "cluster_vulnerability_analysis": {
    "analysis_metadata": {
      "cluster_name": "Door Lock",
      "cluster_id": "0x0101",
      "specification": "Matter 1.5 Application Cluster Specification",
      "fsm_model": "doorlock_fsm_v1.json",
      "analysis_date": "ISO_8601",
      "total_properties": 25,
      "properties_analyzed": 25,
      "analysis_complete": true
    },

    "property_verdicts": [
      {
        "property_id": "PROP_DRLK_001",
        "property_name": "PIN_Brute_Force_Protection",
        "verdict": "VIOLATED",
        "confidence": 0.95,
        "severity": "HIGH",
        "physical_safety_impact": "Potential unauthorized entry"
      }
    ],

    "detailed_analyses": [
      {
        "property_id": "PROP_DRLK_001",
        "property_name": "PIN_Brute_Force_Protection",
        "property_claim": "Wrong PIN attempts SHALL be limited by WrongCodeEntryLimit",
        "verdict": "VIOLATED",

        "fsm_analysis": {
          "relevant_transitions": [
            {
              "transition_id": "T_Unlock_PIN_Fail",
              "from_state": "Locked",
              "to_state": "Locked",
              "trigger": "UnlockDoor",
              "guard": "PIN_invalid",
              "action": "FailureCount++, generate_event(CredentialFailure)"
            }
          ],
          "attack_path": [
            {
              "step": 1,
              "state": "Locked",
              "action": "Send UnlockDoor with guess PIN_1",
              "result": "FailureCount = 1"
            },
            {
              "step": 2,
              "state": "Locked, Wait 1 second",
              "action": "Send UnlockDoor with guess PIN_2",
              "result": "FailureCount = 2"
            },
            {
              "step": "N",
              "state": "Locked",
              "action": "After WrongCodeEntryLimit attempts",
              "result": "UserCodeTemporaryDisableTime lockout (1-255 seconds only)"
            }
          ],
          "violation_mechanism": "Spec allows WrongCodeEntryLimit up to 255 and UserCodeTemporaryDisableTime as low as 1 second. No exponential backoff. No permanent lockout. Attacker can try 255*86400/1 = 22M PINs per day."
        },

        "specification_evidence": [
          {
            "quote": "The number of consecutive authentication failures before generating a lockout condition. For now WrongCodeEntryLimit is between 1-255 wrong entry attempts.",
            "source": "Section 5.2.9.32, 'WrongCodeEntryLimit Attribute', Page 423",
            "normative": "Constraint (1-255)",
            "gap": "No minimum value specified. 255 attempts is very high."
          },
          {
            "quote": "The number of seconds that the lock shuts down following wrong code entry.",
            "source": "Section 5.2.9.33, 'UserCodeTemporaryDisableTime Attribute', Page 423",
            "normative": "Constraint (1-255 seconds)",
            "gap": "1 second lockout is trivially bypassable. No exponential backoff."
          }
        ],

        "specification_gap": {
          "what_spec_claims": "Lock may implement brute force protection via WrongCodeEntryLimit",
          "what_spec_fails_to_specify": "No minimum limit value, no exponential backoff, no permanent lockout, no account for rapid retry",
          "normative_weakness": "Uses MAY for counter reset: 'The lock MAY reset the counter used to track incorrect credential presentations as required by internal logic'",
          "consequence": "Implementation could reset counter freely, set high limit, set 1-second lockout"
        },

        "counterexample_scenario": {
          "attacker_capability": "Network access, Operate privilege (can send UnlockDoor commands)",
          "attack_steps": [
            "Configure: Assume lock has WrongCodeEntryLimit=100, UserCodeTemporaryDisableTime=5",
            "Loop: Send 100 UnlockDoor commands with different PINs (1 per second = 100 seconds)",
            "Wait: 5 second lockout",
            "Repeat: After lockout, counter resets (per MAY clause), continue enumeration",
            "Result: 6-digit PIN (1M combinations) cracked in ~14 hours"
          ],
          "physical_impact": "Unauthorized entry after PIN enumeration"
        },

        "severity_assessment": {
          "confidentiality_impact": "NONE",
          "integrity_impact": "HIGH",
          "availability_impact": "LOW",
          "physical_safety_impact": "HIGH",
          "overall_severity": "HIGH",
          "rationale": "Practical PIN brute force enables unauthorized physical entry"
        },

        "recommendations": [
          "Spec should mandate minimum WrongCodeEntryLimit (e.g., 3-5)",
          "Spec should mandate exponential backoff",
          "Spec should prohibit counter reset without admin action",
          "Spec should recommend permanent lockout after threshold"
        ]
      }
    ],

    "holds_summary": [
      {
        "property_id": "PROP_DRLK_010",
        "property_name": "Admin_Required_For_User_Management",
        "why_holds": "SetUser and ClearUser commands have Access: A (Admin), verified in FSM guards"
      }
    ],

    "vulnerability_summary": {
      "total_violations": 5,
      "by_severity": {
        "CRITICAL": 1,
        "HIGH": 3,
        "MEDIUM": 1
      },
      "by_category": {
        "AccessControl": 1,
        "Authentication": 2,
        "Timing": 1,
        "PhysicalSafety": 1
      },
      "safety_critical_violations": 2,
      "spec_gaps_exploited": 4
    },

    "overall_cluster_assessment": {
      "security_posture": "MODERATE_RISK",
      "major_concerns": [
        "PIN brute force protection is weak",
        "RequirePINForRemoteOperation is optional, not mandatory",
        "Auto-relock has no maximum timeout constraint"
      ],
      "recommended_spec_changes": [
        "Mandate RequirePINForRemoteOperation as default-true",
        "Add exponential backoff to WrongCodeEntryLimit behavior",
        "Add maximum value for UnlockWithTimeout duration"
      ]
    }
  }
}
```

---

## Severity Rating Guidelines

### CRITICAL (Physical Safety + No Mitigation)

- Remote disable of smoke/CO alarms
- Unauthorized door unlock with physical entry consequence
- Valve control enabling flooding/gas leak with no auto-shutoff
- EVSE override causing electrical fire risk

### HIGH (Security Bypass with Significant Impact)

- PIN brute force feasible in practical timeframe
- Credential management without proper authorization
- Privilege escalation (Operate → Admin effect)
- Timer manipulation enabling extended security window

### MEDIUM (Security Weakness with Limited Impact)

- Rate limiting inadequate but not trivially bypassed
- Event suppression possible but detectible
- Timing windows exist but narrow
- Feature bypass possible only with specific configuration

---

## Application Cluster-Specific Verification Focus

### Door Lock (DRLK)

- PIN/credential authentication enforcement
- Operating mode restrictions
- Auto-relock timing
- Remote operation authorization
- User type restrictions

### Smoke/CO Alarm (SMOKECO)

- Alarm suppression controls
- Sensitivity manipulation detection
- Interconnect alarm authentication
- Self-test abuse prevention

### Valve Control (VALCC)

- Fail-safe behavior on fault
- Open duration limits
- Command authorization

### Window Covering (WNCV)

- Position manipulation authorization
- Safety mode enforcement

### Camera/AV (CAMERA)

- Privacy mode enforcement
- Stream access authorization
- SFrame E2E encryption use

### EVSE (EVSE)

- Charging authorization
- Current limit enforcement
- Grid safety properties

---

## LLM Instructions

1. **Verify EACH property systematically** against FSM
2. **Trace attack paths** for violated properties
3. **Quote spec precisely** — exact text, section, page
4. **Assess physical impact** for safety-critical clusters
5. **Document spec gaps** that enable vulnerabilities
6. **Rate severity** based on practical exploitability and impact
7. **Provide concrete scenarios** — not abstract descriptions
8. **Check access levels** — privilege violations are common issues
9. **Consider feature flags** — properties may be conditional
10. **Stop if blocked** — document what prevents further analysis

---

## Stopping Conditions

Output current results and stop when:

- FSM is incomplete for remaining properties
- Spec text is ambiguous and requires human interpretation
- Multiple equally valid interpretations exist
- Analysis resource limit reached

Document why analysis stopped and what remains.

---

## Key Success Criteria

✅ Every property has clear HOLDS/VIOLATED verdict with evidence
✅ Violated properties have concrete attack paths
✅ Spec citations are verifiable (exact quote + location)
✅ Physical safety impacts are assessed for relevant clusters
✅ Recommendations are actionable spec changes
✅ JSON output is valid and parseable
