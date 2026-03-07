# VIOLATION ANALYSIS - PROP_001: Node_ID_Uniqueness_Enforcement

## Property Under Analysis
**ID**: PROP_001  
**Name**: Node_ID_Uniqueness_Enforcement  
**Claim**: "Any newly-allocated Node ID SHALL be checked to ensure its uniqueness in the NodeList attribute of the Joint Fabric Datastore before assignment."

## Verdict: **VIOLATED**

---

## FSM Analysis

### Critical Transitions:
**JCM FSM - Transition: JCM_FabricUpdate_InProgress → JCM_Complete_JointFabric_Active**

**Function Called**: `add_noc_with_anchor_fabric_id(cross_signed_icac, anchor_fabric_id)`

**Algorithm Detail** (from FSM line 879):
```
"Generates new NOC for node: Subject DN includes matter-fabric-id=anchor_fabric_id.  
Issuer=cross_signed_icac. Signs NOC using cross-signed ICAC private key.  
Invokes AddNOC command with NOC, ICAC, IP address, port, CaseAdminSubject=Administrator CAT.  
Node validates NOC chains to trusted Anchor RCAC, activates new fabric.  
Returns NOCResponse with StatusCode and assigned Fabric Index."
```

### Attack Path:

```
State 1: JCM_FabricUpdate_InProgress
  - Ecosystem B iterates over all nodes in Fabric B
  - For each node, calls: add_noc_with_anchor_fabric_id()
  
State 2: add_noc_with_anchor_fabric_id() execution
  - Generates new NOC with Subject DN (includes Node ID)
  - ❌ NO uniqueness check against NodeList
  - ❌ NO query to Joint Fabric Datastore
  - Invokes AddNOC command directly
  
State 3: JCM_Complete_JointFabric_Active
  - All nodes transitioned to Joint Fabric
  - Node IDs assigned without validation
  - VIOLATION: Duplicate Node IDs possible
```

### Why Violated:

1. **Missing Guard**: No guard condition checks `exists_in_nodelist(node_id) == false`
2. **Missing Function**: No function `check_node_id_uniqueness(node_id, datastore)` defined
3. **Missing Action**: No action `query_datastore_nodelist(node_id)` before AddNOC
4. **Direct Assignment**: NOC generation and issuance happens atomically without intermediate validation

---

## Specification Evidence

### What Spec REQUIRES (Section 12.2.2, Page 1057):

**Quote**:
```
"Any newly-allocated Node ID SHALL:
  • be greater than 0x0000_0000_0000_0000, but less than 0xFFFF_FFEF_FFFF_FFFF, representing a value within the Operational NodeID range (see Table 4, "Node Identifier Allocations");
  • be checked to ensure its uniqueness in the NodeList attribute of the Joint Fabric Datastore

The Node ID SHALL be regenerated if these constraints are not met."
```

**Source**: Section 12.2.2, "Node ID Generation", Page 1057, Bullet points 1-2  
**Context**: Defines SHALL requirements for Node ID allocation in Joint Fabric

### What FSM FAILS TO IMPLEMENT:

**Gap 1**: No function checks NodeList  
- Expected: `check_node_id_uniqueness(node_id, datastore) → boolean`
- Actual: Function does not exist in FSM

**Gap 2**: No guard enforces uniqueness before AddNOC  
- Expected: Guard `uniqueness_verified(node_id) == true`
- Actual: No such guard in any transition leading to AddNOC

**Gap 3**: No regeneration loop  
- Expected: `while exists_in_nodelist(node_id): node_id = generate_new_node_id()`
- Actual: One-shot generation without retry logic

---

## Counterexample Scenario

### Attack Vector: Node ID Collision Attack

**Initial Conditions**:
- Joint Fabric Datastore contains Node A with Node ID = 0x1234_5678_9ABC_DEF0
- Ecosystem B commissioning Node B with random Node ID generation

**Execution Steps**:

1. **T=0**: Ecosystem B generates Node ID for Node B
   - Random generation produces: 0x1234_5678_9ABC_DEF0 (collision!)
   
2. **T=1**: Ecosystem B calls `add_noc_with_anchor_fabric_id()`
   - FSM generates NOC with duplicate Node ID
   - ❌ No uniqueness check performed
   - AddNOC command invoked
   
3. **T=2**: Node B accepts NOC and joins Joint Fabric
   - Node B now has identical Node ID as Node A
   - Both nodes respond to same address
   
4. **T=3**: Communication Failure
   - Message to 0x1234_5678_9ABC_DEF0 → ambiguous routing
   - ACL entry for 0x1234_5678_9ABC_DEF0 → which node?
   - CASE session establishment → identity confusion

### Security Impact:

**Identity Spoofing**:
- Node B can impersonate Node A by presenting valid NOC with matching Node ID
- Attacker intercepts messages intended for Node A
- Attacker uses Node A's ACL permissions without authorization

**ACL Bypass**:
- ACL entry: "Grant MANAGE to Node ID 0x1234_5678_9ABC_DEF0" 
- Both Node A (authorized) and Node B (unauthorized) match ACL
- Node B gains privileges intended only for Node A

**Routing Confusion**:
- CASE session to "0x1234_5678_9ABC_DEF0" → connects to wrong node
- Messages encrypted for Node A → decrypted by Node B
- Man-in-the-middle without cryptographic compromise

**Probability Analysis**:
- Node ID space: ~2^56 valid IDs (0x1 to 0xFFFF_FFEF_FFFF_FFFE)
- Birthday paradox: P(collision) ≈ n²/2N where n=nodes, N=2^56
- For 10,000 nodes: P(collision) ≈ 0.0000009 (low but non-zero)
- For 100,000 nodes: P(collision) ≈ 0.00009 (0.009%)
- Attack scenario: Adversary generates many Node IDs until collision found

---

## Severity Assessment

**Severity**: **CRITICAL**

**Justification**:
1. **Specification Violation**: Direct violation of SHALL requirement
2. **Authentication Bypass**: Enables identity spoofing without key compromise
3. **Authorization Bypass**: Allows ACL circumvention through ID collision
4. **No Mitigation**: No compensating controls in protocol
5. **Difficult Detection**: Collision may not be immediately observable

**Exploitability**: MEDIUM
- Requires adversary to commission nodes to Joint Fabric
- Requires random collision (low probability) OR
- Requires adversary with knowledge of existing Node IDs (targeted attack)

**Impact**: HIGH
- Complete identity theft of targeted node
- Unauthorized privilege escalation via ACL confusion
- Denial of service (routing ambiguity)

---

## Recommendations

### Fix 1: Add Uniqueness Check Function

**New Function**:
```json
{
  "name": "check_node_id_uniqueness_in_datastore",
  "parameters": [
    {
      "name": "candidate_node_id",
      "type": "64-bit",
      "description": "Proposed Node ID to validate"
    },
    {
      "name": "datastore_connection",
      "type": "CASE_session",
      "description": "Connection to Joint Fabric Datastore"
    }
  ],
  "return_type": "boolean (true=unique, false=collision)",
  "description": "Queries NodeList attribute of Joint Fabric Datastore to verify candidate Node ID does not exist.",
  "algorithm_detail": "Establishes CASE session to Datastore (if not already connected). Queries NodeList attribute via attribute read command. Searches returned list for candidate_node_id. Returns false if found (collision), true if not found (unique). Handles errors (datastore unreachable) by returning false (fail-closed)."
}
```

### Fix 2: Add Guard to AddNOC Transition

**Updated Transition**:
```json
{
  "from_state": "JCM_FabricUpdate_InProgress",
  "to_state": "JCM_Complete_JointFabric_Active",
  "trigger": "all_nodes_updated",
  "guard": "all_nodes_updated_successfully() && all_node_ids_unique_in_datastore()",
  "actions": [
    "log_jcm_complete()"
  ]
}
```

### Fix 3: Add Regeneration Loop

**Updated Algorithm** (add_noc_with_anchor_fabric_id):
```
1. Generate random Node ID in range (0x1, 0xFFFF_FFEF_FFFF_FFFE)
2. Check uniqueness: is_unique = check_node_id_uniqueness_in_datastore(node_id, datastore)
3. If not unique: goto step 1 (regenerate)
4. If unique: proceed with NOC generation
5. Generate NOC with validated unique Node ID
6. Invoke AddNOC command
```

### Fix 4: Specification Amendment

**Add to Section 12.2.2**:
```
"The uniqueness check SHALL be performed by querying the NodeList attribute  
of the Joint Fabric Datastore before invoking the AddNOC command.  
If the Node ID already exists in NodeList, a new Node ID SHALL be generated  
and the check repeated until a unique Node ID is found."
```

---

## Related Vulnerabilities

**PROP_025**: Device Re-commissioning Prevention
- If Node ID collision occurs, device may be re-commissioned with different identity
- Violates prohibition against commissioning same device to multiple fabrics

**PROP_001 Assumption Violations**:
- Assumes datastore is available and queryable during commissioning
- If datastore unreachable, uniqueness check cannot be performed
- Spec should define fail-safe behavior (abort commissioning vs. proceed with risk)

---

## Status
- **Property**: VIOLATED
- **Confidence**: 100%
- **Evidence Quality**: HIGH (direct spec quote, clear FSM gap)
- **Exploitability**: MEDIUM
- **Severity**: CRITICAL
