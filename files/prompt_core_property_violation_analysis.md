# Property Violation Analysis Prompt for Vulnerability Detection

## Objective
For each security property, systematically verify it against the extracted FSM. Determine if the property holds or is violated. Then locate and cite exact specification text supporting the conclusion. Output evidence-based vulnerability assessment.

---

## Core Verification Methodology

### Phase 1: FSM Property Verification

For each property, perform this analysis:

**Step 1: Formalize the Property**
- Take property claim: e.g., "Only nodes with epoch key E can derive operational key"
- Translate to FSM query: "In all transitions, is `derive_operational_key()` guarded by `has_epoch_key(E) == true`?"
- Identify critical transitions where property must hold

**Step 2: Trace FSM Execution Paths**
- List all transitions that could violate property
- For each transition:
  - What are the preconditions (guards)?
  - What are the actions?
  - Could an attacker reach this transition without satisfying property requirement?
  - Is there a state path to violation?

**Step 3: Check for Guard Violations**
- Guard missing? → Property violated
- Guard insufficient (doesn't check all preconditions)? → Property violated
- Guard correct but incomplete (doesn't cover all branches)? → Property violated

**Step 4: Check for Action Violations**
- Does action assume something not guaranteed? → Property violated
- Does action leak information or create side channel? → Property violated
- Does action have race condition or timing window? → Property violated

**Step 5: Determine Verdict**
- **HOLDS**: All paths enforce property, no exceptions
- **VIOLATED**: At least one path breaks property
- **PARTIALLY_HOLDS**: Property holds in most cases but fails in edge case
- **UNVERIFIABLE**: FSM abstraction too coarse to determine

---

### Phase 2: Evidence Collection

**If Property HOLDS**:

1. **Identify supporting transitions** (2-3 strongest)
   - Which transitions enforce this property?
   - Show guard conditions that prevent violation

2. **Locate specification text** supporting the guarantee
   - Search for: "SHALL", "MUST", explicit claims
   - Extract exact quote proving property requirement
   - Note section number and page

3. **Document assumptions** that enable property
   - What must be true for property to hold?
   - Are these assumptions explicitly stated or implicit?
   - Are assumptions enforced elsewhere in spec?

**Format**:
```
PROPERTY: [Name]
VERDICT: HOLDS

Supporting Transition:
  From: State_A
  To: State_B
  Guard: [guard condition]
  Why holds: [explanation]

Specification Evidence:
  Quote: "[exact text from spec]"
  Source: Section X.Y.Z, Page P, Paragraph N
  
Supporting Assumptions:
  1. [Assumption 1]
     - Source: Section / Enforcement: Where verified
  2. [Assumption 2]
     - Source: Section / Enforcement: Where verified
```

---

**If Property VIOLATED**:

1. **Identify attack path** (transition sequence leading to violation)
   - Start state
   - Sequence of transitions
   - Final state where property fails
   - Why property is violated in this path

2. **Locate specification text** that CLAIMS the property
   - Quote showing what spec INTENDED
   - Show where spec is wrong or incomplete
   - Identify the gap/flaw in specification

3. **Provide counterexample scenario**
   - Specific protocol execution
   - What attacker/system does
   - How property is broken
   - Impact on security

**Format**:
```
PROPERTY: [Name]
VERDICT: VIOLATED

Attack Path:
  State_A -(Trigger_1, Guard_X)-> State_B -(Trigger_2, Guard_Y)-> State_C
  Result: Property fails at State_C

Why Violated:
  [Detailed explanation of violation mechanism]

Specification Claim (What should hold):
  Quote: "[spec text claiming property]"
  Source: Section X.Y.Z, Page P
  
Specification Gap (Why it doesn't hold):
  Quote: "[spec text that's insufficient/missing]"
  Source: Section X.Y.Z, Page P
  Gap: [What's missing or wrong]

Counterexample Scenario:
  1. [Initial condition]
  2. [Attacker/system action]
  3. [Result violating property]
  4. [Impact: What security is broken]

Severity: CRITICAL | HIGH | MEDIUM
```

---

### Phase 3: Specification Citation

**Citation Requirements** (must be exact and verifiable):

1. **Direct Quote**: Copy exact text from specification
   - Include punctuation and capitalization as in spec
   - Use [...] for omitted text (show what's omitted)
   - Mark any interpretations as [interpretation]

2. **Source Reference**: Must be precise
   - Section number: X.Y.Z (use spec's numbering)
   - Page number: "Page P" (use page from document)
   - Paragraph: "Paragraph N" or "Bullet N" or "Table row N"
   - Subsection title: Include subsection name

3. **Context**: Show surrounding text for ambiguity resolution
   - What comes before/after quote?
   - Is there related guidance elsewhere?
   - Are there contradictions with other sections?

**Format**:
```
Quote: "Exact text from specification"
Source: Section X.Y.Z, "Subsection Title", Page P, [Paragraph/Bullet/Table specification]
Context: [What surrounds this statement - is there related guidance?]
Specification File: [Document name, version, date]
```

---

## Analysis Process (Per Property)

### Step A: Pre-Analysis
- [ ] Property clearly stated and formalized?
- [ ] FSM extracted and available?
- [ ] All transitions identified?
- [ ] All guards documented?

### Step B: FSM Tracing
- [ ] Identified all transitions that could violate property
- [ ] Traced attack paths (if violated)
- [ ] Checked guard sufficiency
- [ ] Checked action correctness

### Step C: Verdict
- [ ] Verdict decided (HOLDS/VIOLATED/PARTIAL/UNVERIFIABLE)?
- [ ] Decision justified with FSM evidence?

### Step D: Citation
- [ ] Located specification text (claim or gap)?
- [ ] Extracted exact quote?
- [ ] Verified source (section, page, paragraph)?
- [ ] Included context?

### Step E: Output
- [ ] Evidence presented clearly?
- [ ] All references verifiable?
- [ ] No speculation or inference (only facts)?

---

## Output Schema (JSON)

```json
{
  "vulnerability_analysis": {
    "analysis_metadata": {
      "specification": "name_and_version",
      "fsm_model": "extracted_fsm_reference",
      "analysis_date": "ISO_8601",
      "total_properties": 42,
      "properties_analyzed": 5,
      "analysis_complete": false,
      "status": "in_progress | completed | stopped_need_rerun"
    },
    "property_verdicts": [
      {
        "property_id": "PROP_001",
        "property_name": "Key_Derivation_Secrecy",
        "verdict": "HOLDS | VIOLATED | PARTIALLY_HOLDS | UNVERIFIABLE",
        "confidence": 0.95,
        "verdict_explanation": "Brief explanation of why property holds/violated"
      }
    ],
    "detailed_analyses": [
      {
        "property_id": "PROP_001",
        "property_name": "Key_Derivation_Secrecy",
        "verdict": "HOLDS",
        "fsm_analysis": {
          "critical_transitions": [
            {
              "from_state": "state_name",
              "to_state": "state_name",
              "trigger": "trigger_name",
              "guard_condition": "has_epoch_key(E) == true",
              "why_property_holds": "Guard ensures only nodes with epoch key can reach this transition"
            }
          ],
          "all_paths_checked": true,
          "violation_paths_found": 0
        },
        "specification_evidence": [
          {
            "quote": "Exact text: 'Only Nodes that possess the input epoch key can derive a given operational key.'",
            "source": "Section 4.17.2, 'Operational Group Key Derivation', Page 199, Paragraph 3",
            "context": "Discusses membership enforcement via key possession",
            "supports_verdict": "Confirms property requirement"
          },
          {
            "quote": "Exact text: 'Group membership is enforced by limiting access to the epoch keys.'",
            "source": "Section 4.17.2, 'Operational Group Key Derivation', Page 199, Paragraph 2",
            "context": "Core mechanism for enforcing membership",
            "supports_verdict": "Confirms access control is via epoch key possession"
          }
        ],
        "supporting_assumptions": [
          {
            "assumption": "KDF is cryptographically secure and unidirectional",
            "type": "cryptographic",
            "where_stated": "Section 3.8 'Key Derivation Function (KDF)'",
            "where_enforced": "FSM guard enforces that only epoch_key holders can call derive_operational_key()",
            "criticality": "CRITICAL"
          },
          {
            "assumption": "Epoch keys are not leaked from privileged nodes",
            "type": "operational",
            "where_stated": "Section 4.17, intro: 'Barring software error or compromise of a privileged Node'",
            "where_enforced": "ACL enforcement on Group Key Management Cluster",
            "criticality": "CRITICAL"
          }
        ],
        "gaps_identified": []
      },
      {
        "property_id": "PROP_005",
        "property_name": "Atomic_Key_Update",
        "verdict": "VIOLATED",
        "fsm_analysis": {
          "attack_path": [
            {
              "state": "KeyUpdateIdle",
              "trigger": "KeySetWrite with partial keys",
              "guard": "keys_ordered(new_keys) && EpochKey0_present(new_keys)",
              "action": "epoch_key_slots := append(existing_slots, new_keys)",
              "result_state": "KeyUpdateApplied",
              "violation": "Old keys NOT removed (append instead of replace)"
            }
          ],
          "violation_mechanism": "Action uses append/add instead of atomic replacement. Specification says 'SHALL remove ALL previous keys' but FSM action adds new keys without removing old ones.",
          "violation_paths_found": 1
        },
        "specification_evidence": [
          {
            "quote": "Exact text: 'Any update of the key set, including a partial update, SHALL remove all previous keys in the set, however many were defined.'",
            "source": "Section 4.17.3.2, 'Managing Epoch Keys', Page 201, Paragraph 3",
            "context": "Describes atomicity requirement for key updates",
            "supports_verdict": "Spec explicitly requires removal of ALL old keys"
          },
          {
            "quote": "Exact text: 'Key updates are idempotent operations to ensure the Administrator is always the source of truth.'",
            "source": "Section 4.17.3.2, 'Managing Epoch Keys', Page 201, Paragraph 2",
            "context": "States idempotency but doesn't explicitly define how old keys are removed",
            "gap": "No explicit algorithm for atomic replacement specified. Leaves implementation ambiguous."
          }
        ],
        "specification_gap": {
          "what_spec_claims": "All previous keys SHALL be removed with any update",
          "what_spec_fails_to_specify": "HOW keys are removed atomically. Spec doesn't say: 'Replace entire key set' vs 'Remove old, then add new' vs other methods",
          "consequence": "Implementation could use incremental add/remove, creating window where both old and new keys are valid simultaneously",
          "security_impact": "Nodes may diverge in key state during propagation interval, enabling attacks like replay with old key or sender/receiver mismatch"
        },
        "counterexample_scenario": {
          "steps": [
            "Admin generates new epoch keys (E_new)",
            "Admin sends KeySetWrite to Node_A: [E_new]",
            "Network partition: Node_B doesn't receive update yet",
            "Admin propagates to Node_B 100ms later",
            "During 100ms gap:",
            "  - Node_A has [E_new] (old removed)",
            "  - Node_B has [E_old] (update not received)",
            "  - Sender (Node_A) uses E_new",
            "  - Receiver (Node_B) only accepts E_old",
            "  - Messages from Node_A cannot be received by Node_B",
            "Result: DoS (denial of service) for 100ms"
          ],
          "severity": "HIGH",
          "note": "This is not an attacker exploit but a design vulnerability: spec allows partial propagation to cause communication failure"
        },
        "recommendations": [
          "Spec should state: 'KeySetWrite replaces entire epoch_key_slots atomically (all-or-nothing semantics)'",
          "Spec should define: 'If replacement fails on any node, transaction is rolled back (no partial updates)'",
          "Or: 'Nodes must maintain two key sets: active and staging. Only after all propagation is complete does staging become active'"
        ]
      }
    ],
    "summary": {
      "properties_analyzed": 5,
      "properties_holding": 3,
      "properties_violated": 1,
      "properties_partially_holding": 1,
      "properties_unverifiable": 0,
      "vulnerabilities_found": 1,
      "vulnerabilities_by_severity": {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 0
      },
      "next_action": "Continue with remaining 37 properties"
    }
  }
}
```

---

## Critical Requirements

### Accuracy Over Speed
- Do NOT speculate about specification intent
- If unsure, mark as UNVERIFIABLE
- Always cite exact text and location
- Show counterexample if claiming violation

### Citation Integrity
- Copy exact text from specification (verbatim)
- Note section, page, paragraph
- Include surrounding context to avoid misquoting
- If quoting paraphrase, clearly mark as [paraphrase]

### FSM Correctness
- Only trace transitions that exist in extracted FSM
- Don't invent attack paths not in FSM
- If FSM seems wrong, don't fix it—mark verdict as UNVERIFIABLE

### Stopping Condition
- If cannot analyze remaining properties (FSM incomplete, spec unclear, etc.)
- Output current results with status: `"analysis_complete": false`
- Stop and wait for rerun with updated FSM or clarification
- Document why analysis stopped

---

## Example Analysis (Complete)

**Property to Verify**: "Senders use CURRENT key only, Receivers accept ANY installed key"

**FSM Transitions**:
```
Transition: SendGroupMessage
  From: MemberWithCurrentKey
  To: MemberWithCurrentKey (stay)
  Guard: key_is_current(selected_key) == true
  Action: operational_key := derive_operational_key(selected_key)

Transition: ReceiveGroupMessage
  From: MemberWithInstalledKeys
  To: MemberWithInstalledKeys (stay)
  Guard: key_is_installed(any_key) == true
  Action: for_each_candidate try_decrypt_with_candidate_key()
```

**Analysis**:
```
VERDICT: HOLDS (with observation about asymmetry)

Why Holds:
- Send transition has Guard: key_is_current (only newest non-future key)
- Receive transition has Guard: key_is_installed (any key, regardless of time)
- Asymmetry is intentional per spec

Specification Evidence:

For Send Guard:
  Quote: "Nodes sending group messages SHALL use operational group keys that are derived from the current epoch key (specifically, the epoch key with the latest start time that is not in the future)."
  Source: Section 4.17.3.1, 'Using Epoch Keys', Page 201, Paragraph 1

For Receive Guard:
  Quote: "Nodes receiving group messages SHALL accept the use of any key derived from one of the currently installed epoch keys. This requirement holds regardless of whether the start time for the key is in the future or the past."
  Source: Section 4.17.3.1, 'Using Epoch Keys', Page 201, Paragraph 2

Asymmetry Justification:
  Quote: "This means Nodes continue to accept communication secured under an epoch key until that key is withdrawn by explicitly deleting the key from a Node's group state by the key distribution Administrator."
  Source: Section 4.17.3.1, 'Using Epoch Keys', Page 201, Paragraph 2

Assumptions Supporting Property:
1. Senders have synchronized time (or use second-newest for unsync)
2. Receivers don't forget keys until admin explicitly removes them
3. Current = latest_start_time AND start_time <= now
```

---

## How to Use This Prompt

1. **Input**: Extracted FSM + List of 48 properties
2. **For each property**:
   - Trace FSM to verify/violate property
   - Find specification text (claim or gap)
   - Document verdict with evidence
3. **Output**: JSON with all analyses
4. **If stuck**: Stop, document what failed, wait for rerun
5. **Next iteration**: Continue with remaining properties

---

## Important Notes

- **One property at a time**: Thoroughly analyze each property
- **No shortcuts**: Every claim must be evidence-based
- **Specification is oracle**: If spec says it, that's truth; if not in spec, it's not proven
- **FSM is executable**: Trace actual FSM paths, not hypothetical ones
- **Cite liberally**: More citations = higher confidence
- **Stop when needed**: If can't verify remaining properties, stop and report

