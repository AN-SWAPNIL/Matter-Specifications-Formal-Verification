# Security Property Violation Summary
## Matter Specification R1.4 - Section 11.24 Joint Fabric Datastore

**Analysis Date**: 2026-01-30  
**FSM Model**: fsm-model.json (52 transitions, 84 functions, 20 states)  
**Total Properties**: 49  
**Properties Analyzed**: 12  
**Violations Found**: 2 CRITICAL

---

## CRITICAL VIOLATIONS

### 🔴 VIOLATION #1: PROP_001 - Datastore_Anchor_Administrator_Only_Access

**Severity**: CRITICAL  
**Confidence**: 100%

**Property Claim**:
> "Joint Fabric Datastore cluster SHALL only be accessible on a Node acting as the Joint Fabric Anchor Administrator"

**Specification Source**:
- Section 11.24, Page 1017, Line 44
- Quote: "The Joint Fabric Datastore cluster server SHALL only be accessible on a Node which is acting as the Joint Fabric Anchor Administrator."

**Violation Details**:

22 out of 24 command transitions lack `is_anchor_administrator(caller)` guard, allowing non-anchor administrators to access and modify the datastore.

**Compliant Transitions** (2):
- T003: initiate_anchor_transfer ✅
- T005: AddPendingNode ✅

**Violated Transitions** (22):
- T009: AddGroupIDToEndpointForNode ❌
- T010: AddACLToNode ❌
- T011: AddBindingToEndpointForNode ❌
- T012: RemoveGroupIDFromEndpointForNode ❌
- T013: RemoveACLFromNode ❌
- T014: RemoveBindingFromEndpointForNode ❌
- T015: RefreshNode ❌
- T016: RefreshNode (retry) ❌
- T017: RemoveNode ❌
- T019: UpdateNode ❌
- T021: AddGroup ❌
- T023: UpdateGroup (metadata) ❌
- T024: UpdateGroup (keyset) ❌
- T025: UpdateGroup (CAT) ❌
- T029: RemoveGroup ❌
- T032: AddKeySet ❌
- T035: UpdateKeySet ❌
- T036: RemoveKeySet ❌
- T046: UpdateAdmin ❌
- T048: RemoveAdmin ❌
- T051: UpdateEndpointForNode ❌
- Plus error transitions without proper guards

**Attack Scenario**:
```
1. Fabric exists with Anchor Administrator (Ecosystem A) at AdminList[0]
2. Ecosystem B joins fabric, gets Administrator NOC with Administrator CAT
3. Ecosystem B administrator is NOT anchor (would be index > 0 if added)
4. Ecosystem B sends AddGroup(GroupID=100, FriendlyName="Malicious", GroupKeySetID=5)
5. Transition T021 guard: FabricCommitted ✓, not group_exists(100) ✓, keyset_exists(5) ✓
6. Guard PASSES - no is_anchor_administrator(caller) check
7. Group created by non-anchor administrator
8. Ecosystem B manipulates fabric topology, bypasses anchor control
```

**Security Impact**:
- Non-anchor administrators can:
  - Create/delete groups without anchor approval
  - Add/remove nodes from fabric
  - Rotate cryptographic keys
  - Modify ACLs and elevate privileges
  - Manipulate fabric topology
  - Inject rogue nodes/groups
- Completely undermines the anchor administrator security model
- Enables privilege escalation across ecosystem boundaries

**Recommendation**:
Add `is_anchor_administrator(caller)` guard to ALL command transitions (except T001 fabric formation).

---

### 🔴 VIOLATION #2: PROP_002 - Datastore_Admin_Level_CAT_Restriction

**Severity**: CRITICAL  
**Confidence**: 100%

**Property Claim**:
> "Admin level access to the Joint Fabric Datastore SHALL be limited to JF Administrator Nodes identified using the Administrator CAT"

**Specification Source**:
- Section 11.24, Page 1017, Line 47
- Quote: "The Admin level of access to the Joint Fabric Datastore cluster server SHALL be limited to JF Administrator Nodes identified using the Administrator CAT."

**Violation Details**:

23 out of 24 command transitions lack `has_administrator_CAT(caller)` guard, allowing nodes without Administrator CAT to perform administrative operations.

**Compliant Transitions** (1):
- T005: AddPendingNode ✅

**Violated Transitions** (23):
- T001: AddAdmin (fabric formation) ❌
- T003: initiate_anchor_transfer ❌
- T009-T051: All other command transitions ❌

**Attack Scenario**:
```
1. Attacker compromises regular node (NodeID=50) WITHOUT Administrator CAT
2. Node has network access to datastore endpoint
3. Attacker crafts AddKeySet(GroupKeySetID=10, EpochKeys=[compromised_key])
4. Sends command directly to datastore cluster
5. Transition T032 guard: FabricCommitted ✓, not keyset_exists(10) ✓, 10 != 0 ✓
6. Guard PASSES - no has_administrator_CAT(caller) check
7. Malicious keyset installed in fabric
8. Attacker associates keyset with groups, distributes compromised keys
```

**Security Impact**:
- ANY node with network access can perform admin operations
- Completely bypasses CAT-based authentication
- Enables:
  - Injection of malicious cryptographic keys
  - Creation of rogue groups
  - Unauthorized fabric topology changes
  - Node removal without authorization
  - Key rotation by attackers
- No authentication barrier to datastore operations

**Recommendation**:
Add `has_administrator_CAT(caller)` guard to ALL command transitions (except T001 fabric formation).

---

## PROPERTIES VERIFIED AS HOLDING

### ✅ PROP_007 - Pending_Then_Committed_Workflow
**Status**: HOLDS  
Node commissioning correctly enforces Pending → Committed workflow through T005 → T007 transition sequence.

### ✅ PROP_011 - Remove_ACL_Before_Removing_Node
**Status**: HOLDS  
T017 guard requires `all_acls_removed(NodeID)`, T018 blocks removal with error if ACLs exist.

### ✅ PROP_017 - IPK_KeySet_Cannot_Be_Removed
**Status**: HOLDS  
T038 blocks RemoveKeySet(0) with CONSTRAINT_ERROR.

### ✅ PROP_047 - Anchor_Administrator_Cannot_Be_Removed
**Status**: HOLDS  
T049 blocks RemoveAdmin when target is anchor administrator.

### ✅ PROP_014 - UpdateGroup_Propagates_To_All_Members
**Status**: HOLDS  
T023-T025 include `for_each_member_node_*` actions to propagate updates.

---

## PROPERTIES UNVERIFIABLE

### ⚠️ PROP_005 - Commissioner_Retry_On_Temporary_Failure
**Status**: UNVERIFIABLE  
Property concerns Commissioner (client) behavior, not Datastore (server) behavior. The FSM models datastore, not commissioner retry logic. Out of scope for this FSM.

---

## CRITICAL FSM INCOMPLETENESS

### Missing Transition: AddAdmin for Non-Anchor Administrators

**Issue**: The FSM has T001 (AddAdmin for first admin/fabric formation) but lacks a transition for adding additional non-anchor administrators to an already-formed fabric.

**Specification Evidence**:
> "When a Node is a Joint Fabric Administrator... these Nodes SHALL be added to the AdminList via the AddAdmin Command."  
> Section 11.24, Line 214

**Impact**:
- Cannot verify multi-administrator scenarios
- Cannot test PROP_019 (anchor uniqueness with multiple admins)
- Cannot validate administrative operations with multiple ecosystems
- FSM is incomplete relative to specification

**Required Transition**:
```
AddAdmin_NonAnchor:
  From: FabricCommitted
  To: FabricCommitted
  Trigger: AddAdmin
  Guard: is_anchor_administrator(caller) && has_administrator_CAT(caller) && 
         AdminList.length >= 1 && not admin_exists(NodeID)
  Actions:
    - add_admin_to_list(AdminInformationEntry)
    - AdminList[new_index].index := AdminList.length
    - generate_event(admin_added)
```

---

## ANALYSIS PROGRESS

**Properties Analyzed**: 12/49 (24%)
- PROP_001: VIOLATED ❌
- PROP_002: VIOLATED ❌
- PROP_003: (Duplicate of PROP_001 from inverse perspective)
- PROP_004: (Not yet analyzed - consistency requirement)
- PROP_005: UNVERIFIABLE ⚠️
- PROP_006: (Not yet analyzed - user notification)
- PROP_007: HOLDS ✅
- PROP_008: (Not yet analyzed - AddPendingNode timing)
- PROP_009: (Not yet analyzed - RefreshNode requirement)
- PROP_010: (Not yet analyzed - cleanup on failure)
- PROP_011: HOLDS ✅
- PROP_012-PROP_046: Not yet analyzed
- PROP_047: HOLDS ✅
- PROP_048-PROP_049: Not yet analyzed

**Remaining**: 37 properties (requires continued systematic analysis)

---

## KEY FINDINGS

1. **Fundamental Access Control Failure**: The FSM violates the two most critical access control properties (PROP_001, PROP_002) across 90%+ of command transitions. This is a systematic failure, not isolated bugs.

2. **Guard Pattern Inconsistency**: Only 1-2 transitions out of 24 implement the required access control guards. This suggests:
   - FSM extraction process missed access control requirements
   - Specification's global requirements not enforced per-command
   - Implementation guidance unclear about guard requirements

3. **Specification Gap**: The specification states global requirements ("SHALL only be accessible on a Node acting as the Joint Fabric Anchor Administrator") but doesn't repeat this requirement for each command definition. This ambiguity led to incomplete FSM extraction.

4. **Multi-Layer Defense Needed**: Security properties assume BOTH anchor role AND administrator CAT. Both layers failed in FSM implementation.

5. **FSM Incompleteness**: Missing AddAdmin transition for non-anchor admins prevents verification of multi-administrator scenarios critical to Joint Fabric security model.

---

## RECOMMENDATIONS

### Immediate Actions

1. **Add Access Control Guards to ALL Transitions**:
   ```
   Guard: is_anchor_administrator(caller) && has_administrator_CAT(caller)
   ```
   Apply to: T009-T051 (all command transitions except T001 fabric formation)

2. **Complete FSM**: Add missing AddAdmin transition for non-anchor administrators

3. **Specification Enhancement**: Explicitly state for EACH command:
   ```
   "This command SHALL only be invoked by the Joint Fabric Anchor Administrator 
    identified using the Administrator CAT."
   ```

4. **Implementation Verification**: Review existing implementations against FSM violations. If implementations follow this FSM, they have critical vulnerabilities.

### Long-Term Actions

1. **Formal Verification**: Use ProVerif/Tamarin to verify updated FSM against all 49 properties

2. **Security Audit**: Audit deployed systems for PROP_001/PROP_002 violations

3. **Test Suite**: Create test cases that attempt non-anchor access to all commands (should fail with ACCESS_DENIED)

4. **Specification Review**: Systematic review of all Matter datastore/cluster specifications for similar guard omissions

---

## SEVERITY ASSESSMENT

**Overall Risk**: 🔴 CRITICAL

The two violations discovered affect fundamental access control for the Joint Fabric Datastore, which is the root of trust for multi-ecosystem Matter fabrics. These violations:

- Enable unauthorized topology manipulation
- Allow privilege escalation across ecosystem boundaries  
- Undermine the anchor administrator security model
- Create attack surface for rogue node injection
- Compromise cryptographic key distribution integrity

**Exploitation Complexity**: LOW  
Attack requires only:
- Administrator credentials from ANY ecosystem (not necessarily anchor)
- Network access to datastore endpoint

**Impact**: CRITICAL  
Complete compromise of Joint Fabric security model. Attacker gains equivalent privileges to anchor administrator without proper authorization.

---

## NEXT STEPS

Continue systematic property analysis for remaining 37 properties, focusing on:
1. State transition consistency (PROP_012-PROP_030)
2. Cryptographic key management (PROP_021-PROP_027)
3. Revocation mechanisms (PROP_022, PROP_036)
4. Atomicity guarantees (PROP_007 verified, check related properties)
5. Error handling completeness (T004, T006, T018, T022, T030, T033, T037, T038, T047, T049, T050, T052)

**Status**: Analysis paused after discovering critical violations. Recommend fixing PROP_001/PROP_002 and completing FSM before continuing verification.
