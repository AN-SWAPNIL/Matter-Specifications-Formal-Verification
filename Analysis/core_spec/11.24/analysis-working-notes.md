# Property Violation Analysis - Working Notes

## PROP_001: Datastore_Anchor_Administrator_Only_Access

**Claim**: Joint Fabric Datastore cluster SHALL only be accessible on a Node acting as the Joint Fabric Anchor Administrator

**Formal**: ∀node. can_access(node, JF_Datastore) ⟹ is_anchor_administrator(node)

**Specification Source**:
- Quote: "The Joint Fabric Datastore cluster server SHALL only be accessible on a Node which is acting as the Joint Fabric Anchor Administrator."
- Source: Section 11.24, Page 1017, Line 44
- Context: Usage requirements for datastore access

### FSM Analysis - Checking ALL Command Transitions

Command transitions that trigger datastore operations:

1. **T001: AddAdmin** (FabricNotFormed → FabricPending)
   - Guard: `AdminList == null || AdminList == empty`
   - ❌ **NO is_anchor_administrator check**
   - Note: This is fabric formation, so no anchor exists yet - EXCEPTION?

2. **T003: initiate_anchor_transfer** (FabricCommitted → FabricTransferring)
   - Guard: `is_anchor_administrator(caller) && new_anchor_designated`
   - ✅ Has anchor check

3. **T005: AddPendingNode** (NodeAbsent → NodePending)
   - Guard: `FabricCommitted && is_anchor_administrator(caller) && has_administrator_CAT(caller) && not node_exists(NodeID)`
   - ✅ Has anchor check

4. **T009: AddGroupIDToEndpointForNode** (NodeCommitted → NodePartiallyConfigured)
   - Guard: `node_exists(NodeID) && endpoint_exists(NodeID, EndpointID) && group_exists(GroupID)`
   - ❌ **NO is_anchor_administrator check** - VIOLATION!

5. **T010: AddACLToNode** (NodeCommitted → NodePartiallyConfigured)
   - Guard: `node_exists(NodeID)`
   - ❌ **NO is_anchor_administrator check** - VIOLATION!

6. **T011: AddBindingToEndpointForNode** (NodeCommitted → NodePartiallyConfigured)
   - Guard: `node_exists(NodeID) && endpoint_exists(NodeID, EndpointID)`
   - ❌ **NO is_anchor_administrator check** - VIOLATION!

7. **T012: RemoveGroupIDFromEndpointForNode** (NodeCommitted → NodePartiallyConfigured)
   - Guard: `node_exists(NodeID) && endpoint_exists(NodeID, EndpointID) && groupid_exists_in_endpoint(NodeID, EndpointID, GroupID)`
   - ❌ **NO is_anchor_administrator check** - VIOLATION!

8. **T013: RemoveACLFromNode** (NodeCommitted → NodePartiallyConfigured)
   - Guard: `node_exists(NodeID) && acl_exists_in_node(NodeID, ListID)`
   - ❌ **NO is_anchor_administrator check** - VIOLATION!

9. **T014: RemoveBindingFromEndpointForNode** (NodeCommitted → NodePartiallyConfigured)
   - Guard: `node_exists(NodeID) && endpoint_exists(NodeID, EndpointID) && binding_exists_in_endpoint(NodeID, EndpointID, ListID)`
   - ❌ **NO is_anchor_administrator check** - VIOLATION!

10. **T015: RefreshNode** (NodePartiallyConfigured → NodeCommitted)
    - Guard: `node_exists(NodeID) && has_pending_or_delete_pending_entries(NodeID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

11. **T016: RefreshNode** (NodePartiallyConfigured → NodePartiallyConfigured - retry)
    - Guard: `node_exists(NodeID) && node_unreachable(NodeID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

12. **T017: RemoveNode** (NodeCommitted → NodeAbsent)
    - Guard: `node_exists(NodeID) && all_acls_removed(NodeID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

13. **T019: UpdateNode** (NodeCommitted → NodeCommitted)
    - Guard: `node_exists(NodeID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

14. **T021: AddGroup** (GroupAbsent → GroupActive)
    - Guard: `FabricCommitted && not group_exists(GroupID) && keyset_exists(GroupKeySetID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

15. **T023: UpdateGroup** (GroupActive → GroupActive - metadata update)
    - Guard: `group_exists(GroupID) && GroupKeySetID_not_changed`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

16. **T024: UpdateGroup** (GroupActive → GroupActive - keyset rotation)
    - Guard: `group_exists(GroupID) && GroupKeySetID_changed && new_keyset_exists(new_GroupKeySetID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

17. **T025: UpdateGroup** (GroupActive → GroupActive - CAT update)
    - Guard: `group_exists(GroupID) && (GroupCAT_changed || GroupCATVersion_changed || GroupPermission_changed)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

18. **T029: RemoveGroup** (GroupActive → GroupAbsent)
    - Guard: `group_exists(GroupID) && not group_in_use(GroupID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

19. **T032: AddKeySet** (KeySetAbsent → KeySetActive)
    - Guard: `FabricCommitted && not keyset_exists(GroupKeySetID) && GroupKeySetID != 0`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

20. **T035: UpdateKeySet** (KeySetActive → KeySetActive)
    - Guard: `keyset_exists(GroupKeySetID) && GroupKeySetID != 0`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

21. **T036: RemoveKeySet** (KeySetActive → KeySetAbsent)
    - Guard: `keyset_exists(GroupKeySetID) && GroupKeySetID != 0 && not keyset_in_use(GroupKeySetID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

22. **T046: UpdateAdmin** (FabricCommitted → FabricCommitted)
    - Guard: `admin_exists(NodeID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

23. **T048: RemoveAdmin** (FabricCommitted → FabricCommitted)
    - Guard: `admin_exists(NodeID) && not is_anchor_administrator_by_nodeid(NodeID) && AdminList.length > 1`
    - ❌ **NO is_anchor_administrator check for CALLER** - VIOLATION!
    - Note: It checks the target is not anchor, but not if caller is anchor

24. **T051: UpdateEndpointForNode** (NodeCommitted → NodeCommitted)
    - Guard: `node_exists(NodeID) && endpoint_exists(NodeID, EndpointID)`
    - ❌ **NO is_anchor_administrator check** - VIOLATION!

### Summary

**VIOLATION FOUND**: PROP_001 is VIOLATED

**Violations Count**: 22 out of 24 command transitions lack `is_anchor_administrator(caller)` guard

**Only 2 transitions have the guard**:
- T003: initiate_anchor_transfer 
- T005: AddPendingNode

**Attack Path Example**:
1. Non-anchor administrator node (or compromised regular admin)
2. Sends AddGroup command to datastore
3. Transition T021 activates with guard: `FabricCommitted && not group_exists(GroupID) && keyset_exists(GroupKeySetID)`
4. No check that caller is anchor administrator
5. Group is created by non-anchor admin
6. Property violated: non-anchor node accessed and modified datastore

**Severity**: CRITICAL

This is a fundamental access control violation affecting almost all datastore operations.

---

## PROP_002: Datastore_Admin_Level_CAT_Restriction

**Claim**: Admin level access to the Joint Fabric Datastore SHALL be limited to JF Administrator Nodes identified using the Administrator CAT

**Formal**: ∀node. has_admin_access(node, JF_Datastore) ⟹ has_administrator_CAT(node)

**Specification Source**:
- Quote: "The Admin level of access to the Joint Fabric Datastore cluster server SHALL be limited to JF Administrator Nodes identified using the Administrator CAT."
- Source: Section 11.24, Page 1017, Line 47

### FSM Analysis

Same systematic check as PROP_001:

**has_administrator_CAT guard present**: ONLY in T005 (AddPendingNode)

**ALL OTHER 23 COMMAND TRANSITIONS LACK THIS GUARD**

### Verdict

**VIOLATION FOUND**: PROP_002 is VIOLATED

**Violations Count**: 23 out of 24 command transitions lack `has_administrator_CAT(caller)` guard

**Attack Path**:
1. Attacker compromises a node with some admin privileges but WITHOUT Administrator CAT
2. Node sends AddKeySet command to datastore
3. Transition T032 activates with guard: `FabricCommitted && not keyset_exists(GroupKeySetID) && GroupKeySetID != 0`
4. No check for Administrator CAT
5. Keyset created by node without proper CAT credentials
6. Property violated

**Severity**: CRITICAL

The Administrator CAT is the authentication mechanism for admin operations. Without this check, any node with network access to datastore can perform admin operations.

---

## PROP_005: Commissioner_Retry_On_Temporary_Failure

**Claim**: If attempts to update the Datastore fail due to temporary conditions, the Commissioner SHALL periodically retry the attempted commands until successful

**Formal**: ∀cmd, t. failed(cmd, temporary_condition, t) ⟹ ∃t'>t. retry(cmd, t')

**Specification Source**:
- Quote: "If attempts to update the Datastore fail due to temporary conditions (reachability issues, BUSY response error, RESOURCE_EXHAUSTED error, etc.), the Commissioner SHALL periodically retry the attempted commands until successful."
- Source: Section 11.24.4, Page 1018, Line 125

### FSM Analysis

**CLARIFICATION**: This property is about Commissioner (administrator client) behavior, not Datastore (server) behavior.

The FSM models the DATASTORE's state machine, not the Commissioner's retry logic. The Commissioner's retry mechanism is external to the datastore.

However, the FSM DOES model what happens when the datastore's attempts to synchronize with nodes fail:

**T016, T041, T043, T044** implement retry for datastore→node synchronization.

But for Commissioner→Datastore communication failures, the retry is the Commissioner's responsibility (not modeled in this FSM).

### Verdict

**UNVERIFIABLE** from this FSM alone

This property cannot be verified from the datastore FSM because it concerns Commissioner behavior, not Datastore behavior. The FSM scope is the Joint Fabric Datastore cluster server, not the Commissioner client.

To verify this property, we would need the Commissioner's FSM, which would show:
- Command submission
- Receipt of BUSY/RESOURCE_EXHAUSTED/timeout
- Scheduling retry
- Resubmitting command

**Note**: The datastore FSM correctly implements retry for its own operations (datastore→node synchronization), which is within its scope.

---

## CRITICAL FSM GAP DISCOVERED: Missing AddAdmin Transition for Non-Anchor Admins

### Issue

The FSM has:
- **T001**: AddAdmin when AdminList is empty (fabric formation, first admin becomes anchor)

But there's NO transition for:
- **AddAdmin when AdminList is NOT empty** (adding additional non-anchor administrators)

### Specification Evidence

Quote: "When a Node is a Joint Fabric Administrator, its Group membership does not need to be managed by the Datastore since it has the ability to monitor the Datastore and issue operational certs for its own Administrator Nodes at any time. As a result, rather than adding Joint Fabric Administrator Nodes to the regular NodeList attribute via the AddPendingNode Command, these Nodes SHALL be added to the AdminList via the AddAdmin Command."
Source: Section 11.24, Line 214

The specification clearly states AddAdmin is used for adding JF Administrators (plural), not just the anchor.

### Impact on Property Verification

This gap affects:
- **PROP_019**: Cannot verify anchor uniqueness because there's no way to add second admin in FSM
- **PROP_002**: Cannot verify CAT restriction for additional admins
- **Multiple properties**: Any property involving multiple administrators cannot be fully verified

### The Missing Transition

Should exist:
```
Transition: AddAdmin_NonAnchor
  From: FabricCommitted
  To: FabricCommitted
  Trigger: AddAdmin
  Guard: is_anchor_administrator(caller) && has_administrator_CAT(caller) && AdminList.length >= 1 && not admin_exists(NodeID)
  Actions:
    - add_admin_to_list(AdminInformationEntry)
    - AdminList[new_admin].index := AdminList.length
    - generate_event(admin_added)
```

This is a MAJOR FSM incompleteness issue. The FSM extracted is incomplete relative to the specification.
