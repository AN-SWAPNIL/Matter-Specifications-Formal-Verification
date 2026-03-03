# Security Property Detection for Protocol Verification

## Goal
Extract **all testable security properties** from specifications with sufficient precision to:
1. **Formally verify** using ProVerif or reasoning-based verification
2. **Detect vulnerabilities** when properties are violated
3. **Enable FSM analysis** by identifying state-enforcing properties
4. **Identify attack vectors** for each potential violation

---

## LLM Approach

### Step 1: Identify Requirements
Search specification for:
- **MANDATORY**: "SHALL", "MUST", "SHALL NOT", "MUST NOT"
- **RECOMMENDED**: "SHOULD", "SHOULD NOT" (apply 3-question impact filter)
- **SECURITY CLAIMS**: "confidential", "authentic", "prevent", "protect", "ensure"

### Step 2: Filter SHOULD Statements
Ask 3 questions to determine if SHOULD is security-critical:
1. Can attacker/non-member exploit if violated? → YES = Extract
2. Does violation break isolation, confidentiality, or authentication? → YES = Extract
3. Is it pure policy (admin enforcement, not cryptographic)? → YES = Skip, but note

### Step 3: Derive Implicit Properties
Combine statements to identify unstated constraints:
- **Access Control Derivation**: Rule A requires role R; Rule B restricts R → derive: "role R cannot simultaneously satisfy both"
- **Causality Chain**: Property P requires precondition Q; Q can fail → derive: "P is vulnerable unless Q is enforced"
- **Sequencing**: Multi-step procedures with implicit order → derive: "step X must complete before step Y"
- **State Invariants**: Multiple state constraints → derive: "state X and state Y are mutually exclusive"

### Step 4: Formalize by Category
Systematically extract properties from these 8 categories:

| Category | Keywords | Formalization | Example |
|----------|----------|---|---|
| **Correctness** | "SHALL", ordering, counts | `count(X) = N`, `order(A→B→C)` | "exactly 3 keys in rotation" |
| **Security** | "confidential", "prevent", "infeasible" | `attacker_lacks_X ⟹ cannot_achieve_Y` | "attacker without key → cannot decrypt" |
| **Cryptography** | "KDF", "DRBG", "derive", "encrypt" | `same_input ⟹ same_output` | "same epoch key → same operational key" |
| **Consistency** | "atomic", "all-or-nothing", "idempotent" | `(add ∧ delete) ∨ nothing` | "key update removes all old keys" |
| **Timing** | "before", "after", "start time", "deadline" | `happens_at(T ≥ t_start)`, `∀nodes: received_within(Δt)` | "key active only after start time" |
| **Atomicity** | "simultaneously", "race", "ordering" | `all_updated ∨ none_updated` | "all nodes updated or none" |
| **Access Control** | "privilege", "ACL", "credentials", "access" | `role_X_can(action) ∧ ¬role_Y_can(action)` | "only admin can write keys" |
| **Revocation** | "eject", "remove", "withdraw", "exclude" | `stop_distributing ⟹ node_loses_access` | "withholding key revokes membership" |

### Step 5: Identify Hard-to-Catch Patterns
⚠️ **WATCH FOR** (these are vulnerability hotspots):
1. **All-or-nothing atomicity**: "MAY deliver partial but SHALL remove all" → atomic replace, not incremental
2. **Implicit sequencing**: Order embedded in narrative, not explicit → formalize as FSM transitions
3. **Negative claims**: "no end time", "no expiration" → formalize as unbounded validity `¬expires`
4. **Probabilistic with fallback**: "collision 2^-16 but try all candidates" → safety via brute force, not prevention
5. **Temporal asymmetry**: "Senders use X, receivers use Y" → divergence risk if not synchronized
6. **Time-sync assumptions**: Clock drift, unsynchronized nodes → creates vulnerability windows

### Step 6: Extract Assumptions
Every property rests on assumptions. Identify:
- **Explicit**: "Barring software error", "Assume X", "Given Y"
- **Implicit**: Anything required for security claim to be true. **Test**: "Must assumption A be true for property P to guarantee security? If A not stated → implicit"

---

## Output Schema (JSON) - Minimal Accurate Format

**Each property MUST be formally verifiable with ProVerif. Include enough detail to identify attack vectors.**

```json
{
  "properties": [
    {
      "id": "PROP_001",
      "name": "Property_Name",
      "category": "Security | Correctness | Cryptography | Consistency | Timing | Atomicity | AccessControl | Revocation",
      "importance": "CRITICAL | HIGH | MEDIUM",
      "claim": "Natural language: what must be true (1 sentence)",
      "formal": "Formal logic OR FSM notation: ∀x. P(x) → Q(x) OR state_A --[cond]--> state_B",
      "violation": "What breaks if property fails (2-3 sentences, include state corruption or data leakage)",
      "proverifQuery": "event_name(x:principal, y:key) ==> precondition(x,y)"
    }
  ],
  "assumptions": [
    {
      "id": "ASSUM_001",
      "statement": "Assumption (e.g., 'KDF is secure', 'no privileged node is compromised')",
      "type": "Explicit | Implicit",
      "impact_if_violated": "Consequence (which properties fail if this assumption breaks)"
    }
  ],
  "vulnerabilities_if_violated": [
    {
      "property_id": "PROP_001",
      "vulnerability": "Specific exploit (e.g., 'attacker derives operational key without epoch key')",
      "severity": "CRITICAL | HIGH | MEDIUM",
      "attack_vector": "How attacker triggers this (e.g., 'send message with unverified epoch key')"
    }
  ],
  "fsmReferenceProperties": [
    {
      "state_name": "key_rotation",
      "properties_enforcing_transitions": ["PROP_005", "PROP_012"],
      "critical_property": "Which property is violated if state machine reaches wrong state"
    }
  ],
  "additionalInsights": "Any emergent patterns, edge cases, or vulnerabilities identified outside the specification guidelines. Include if model identifies unstated risks or design flaws.",
  "summary": {
    "total_properties": 42,
    "by_importance": { "CRITICAL": 8, "HIGH": 16, "MEDIUM": 18 },
    "by_category": { "Security": 12, "Consistency": 8, "Cryptography": 10, "Timing": 6, "Atomicity": 4, "Correctness": 1, "AccessControl": 0, "Revocation": 1 },
    "total_assumptions": 5,
    "vulnerabilities_identified": 3
  }
}
```

---

## Formalization Rules for ProVerif

Keep formal statements **short and verifiable**:

```proverif
(* Property: Only nodes with epoch key can derive operational key *)
query x:principal, e:key, o:key ⊢ 
  event derive_operational_key(x, e, o) ==> has_epoch_key(x, e)

(* Property: Keys removed are no longer usable *)
query x:principal, k:key, msg:bitstring ⊢ 
  event receive_encrypted(msg, k) ==> ¬event key_removed(k)

(* Property: State transition ordering *)
query ⊢ 
  event after(state_activate, state_admin_update) ==> 
  event before(state_admin_update, state_activate)
```

---

**Exception**: Include any property affecting security, even if obvious. When in doubt, include it.

---

## LLM Instructions

1. **Extract all properties** (CRITICAL, HIGH, MEDIUM) across all 8 categories
2. **Formalize for ProVerif**: Every property must translate to a verifiable query
3. **Identify vulnerabilities**: For each property, explain the attack if it's violated
4. **Link to FSM**: Note which FSM states/transitions depend on this property
5. **Combine statements**: Don't just quote—derive emergent constraints
6. **Think adversarially**: "What can attacker do if this property fails?"
7. **Check assumptions**: Test implicit assumptions (use criteria in Step 6)
8. **Add insights beyond guidelines**: If you identify risks not covered by spec, add to additionalInsights
9. **Consolidate redundancy**: Don't duplicate overlapping properties
10. **Sort by importance**: CRITICAL first, then HIGH, then MEDIUM

---

## Execution Checklist

- [ ] All "SHALL", "MUST" extracted and formalized
- [ ] All "SHOULD" filtered via 3-question decision tree
- [ ] Security claims (confidentiality, authenticity, integrity) identified
- [ ] Derived properties from combined statements added
- [ ] State transitions mapped to properties
- [ ] Cryptographic operations and assumptions extracted
- [ ] Timing constraints formalized with temporal notation
- [ ] Atomicity/consistency properties identified
- [ ] Access control rules specified
- [ ] Revocation mechanisms analyzed
- [ ] Hard-to-catch patterns explicitly checked
- [ ] Implicit assumptions identified and tested
- [ ] Vulnerability scenarios documented for each property
- [ ] ProVerif queries sketched for all critical properties
- [ ] FSM properties cross-referenced
- [ ] Any insights beyond guidelines added to additionalInsights

---

## Example Property (Complete)

```json
{
  "id": "PROP_015",
  "name": "Key_Derivation_Secrecy",
  "category": "Security",
  "importance": "CRITICAL",
  "claim": "Only nodes possessing epoch key E can derive the operational group key derived from E.",
  "formal": "∀node, E, OG. event derive(node, E, OG) ==> has_key(node, E)",
  "violation": "A non-member node derives the operational group key without possessing the epoch key. The node gains unauthorized access to group communications, breaking confidentiality and authentication.",
  "proverifQuery": "query x:principal, e:key, og:key ⊢ event derive_key(x, e, og) ==> has_epoch_key(x, e)"
}
```

```json
{
  "property_id": "PROP_015",
  "vulnerability": "Attacker without epoch key derives operational group key via KDF attack or weak randomness",
  "severity": "CRITICAL",
  "attack_vector": "Attacker sends message claiming to use operational key, node verifies with wrong epoch key assumption"
}
```

---

## Key Improvements for Accuracy

✅ **Minimal property format** - removes unnecessary nesting, keeps fields essential for ProVerif  
✅ **Explicit vulnerability section** - links each property to concrete attack vectors  
✅ **FSM cross-reference** - maps properties to state machine for holistic verification  
✅ **AdditionalInsights field** - captures model reasoning outside guidelines (may reveal design flaws)  
✅ **Assumption discipline** - implicit assumptions explicitly tested and documented  
✅ **ProVerif-native** - formal statements directly translatable to queries  
✅ **Violation scenarios** - precise description enabling targeted test case generation  
✅ **Generic & precise** - works for any protocol; optimized for vulnerability detection