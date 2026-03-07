# FSM Extraction Analysis: Joint Fabric Datastore (11.24)

## Section Overview
- **Section**: 11.24 Joint Fabric Datastore Cluster
- **Purpose**: Manages set of Nodes, Groups, and Group membership in Joint Fabric
- **Security Role**: Central authority for fabric topology, access control, and cryptographic key distribution

## State-Defining Attributes

### 1. DatastoreStateEnum (Primary State Type)
- **Pending**: Target device operation is pending
- **Committed**: Target device operation has been committed
- **DeletePending**: Target device delete operation is pending

### 2. Datastore-Level Attributes
- `AnchorRootCA`: Root CA certificate (null = fabric not formed)
- `AnchorNodeID`: Node ID of anchor administrator
- `AnchorVendorID`: Vendor ID of anchor administrator
- `FriendlyName`: Fabric friendly name
- `GroupKeySetList`: List of GroupKeySetStruct (must include IPK with ID=0)
- `GroupList`: List of Group Information Entries
- `NodeList`: List of Node Information Entries
- `AdminList`: List of Administrator Information Entries (empty = fabric not formed)
- `StatusEntry`: Overall datastore status (Pending/Committed/DeletePending)

### 3. Node Information Entry Attributes
- `NodeID`: Unique node identifier
- `FriendlyName`: Node friendly name
- `CommissioningStatusEntry`: Pending/Committed state
- `NodeKeySetList`: List of keysets with status (Pending/Committed/DeletePending)
- `ACLList`: List of ACL entries with status
- `EndpointList`: List of endpoints with status

### 4. Endpoint Entry Attributes
- `EndpointID`: Endpoint identifier
- `FriendlyName`: Endpoint name
- `StatusEntry`: Pending/Committed state
- `GroupIDList`: Groups this endpoint belongs to (each with status)
- `BindingList`: Binding targets (each with status)

### 5. Group Information Entry Attributes
- `GroupID`: Unique group identifier
- `FriendlyName`: Group friendly name
- `GroupKeySetID`: KeySet used by this group
- `GroupCAT`: CAT value for unicast access control
- `GroupCATVersion`: Current CAT version number
- `GroupPermission`: AccessControlEntryPrivilegeEnum (Administrator/Manage/etc)

### 6. KeySet Attributes
- `GroupKeySetID`: Unique identifier (0 = IPK)
- `EpochKeys`: List of epoch keys with timestamps
- Status tracked in NodeKeySetList when distributed to nodes

## State Space Definition

### Global Datastore States
1. **FabricNotFormed**: AdminList empty/null, AnchorRootCA null
2. **FabricPending**: AdminList non-empty, StatusEntry=Pending
3. **FabricCommitted**: AdminList non-empty, StatusEntry=Committed, operations allowed
4. **FabricTransferring**: StatusEntry=DeletePending (anchor transfer in progress)

### Node Entry States
1. **NodeAbsent**: No entry in NodeList
2. **NodePending**: Entry exists, CommissioningStatusEntry=Pending
3. **NodeCommitted**: Entry exists, CommissioningStatusEntry=Committed
4. **NodePartiallyConfigured**: Committed but has pending updates in ACL/KeySet/Endpoint lists

### Sub-Entry States (KeySet, ACL, GroupID, Binding on Node)
1. **EntryAbsent**: Not in list
2. **EntryPending**: In list with Status=Pending
3. **EntryCommitted**: In list with Status=Committed
4. **EntryDeletePending**: In list with Status=DeletePending

### Group States
1. **GroupAbsent**: Not in GroupList
2. **GroupActive**: In GroupList, no nodes have DeletePending membership
3. **GroupBeingRemoved**: Some nodes have DeletePending membership for this group

## Commands (Triggers)

### KeySet Management
1. **AddKeySet(GroupKeySet)**: Add new keyset to GroupKeySetList
2. **UpdateKeySet(GroupKeySet)**: Update existing keyset, propagate to all nodes using it
3. **RemoveKeySet(GroupKeySetID)**: Remove keyset if not in use

### Group Management
4. **AddGroup(GroupID, FriendlyName, GroupKeySetID, GroupCAT, GroupCATVersion, GroupPermission)**: Create new group
5. **UpdateGroup(GroupID, [optional fields])**: Update group, propagate changes to member nodes
6. **RemoveGroup(GroupID)**: Remove group if no active members

### Administrator Management
7. **AddAdmin(AdminInformationEntry)**: Add administrator to AdminList
8. **UpdateAdmin(NodeID, [optional fields])**: Update administrator info
9. **RemoveAdmin(NodeID)**: Remove administrator

### Node Management
10. **AddPendingNode(NodeID, FriendlyName)**: Create pending node entry
11. **RefreshNode(NodeID)**: Synchronize datastore with actual node state
12. **UpdateNode(NodeID, FriendlyName)**: Update node friendly name
13. **RemoveNode(NodeID)**: Delete node entry

### Endpoint/Group/Binding Management
14. **UpdateEndpointForNode(EndpointID, NodeID, FriendlyName)**: Update endpoint name
15. **AddGroupIDToEndpointForNode(NodeID, EndpointID, GroupID)**: Add group membership
16. **RemoveGroupIDFromEndpointForNode(NodeID, EndpointID, GroupID)**: Remove group membership
17. **AddBindingToEndpointForNode(NodeID, EndpointID, Binding)**: Add binding
18. **RemoveBindingFromEndpointForNode(ListID, EndpointID, NodeID)**: Remove binding

### ACL Management
19. **AddACLToNode(NodeID, ACLEntry)**: Add ACL entry to node
20. **RemoveACLFromNode(ListID, NodeID)**: Remove ACL entry from node

## Key Operations & Functions

### AddKeySet Logic
```
Guard: GroupKeySetID not in GroupKeySetList
Success: Add to GroupKeySetList
Failure: Return CONSTRAINT_ERROR if already exists
```

### UpdateKeySet Logic
```
Guard: GroupKeySetID exists in GroupKeySetList
Actions:
  1. Update KeySet entry in GroupKeySetList
  2. For each Node with this KeySet in NodeKeySetList:
     a. Set status to Pending
     b. Attempt to update node
     c. If success: Set status to Committed
     d. If fail: Remains Pending for future RefreshNode
```

### RemoveKeySet Logic
```
Guard: GroupKeySetID != 0 (cannot remove IPK)
Guard: GroupKeySetID exists
Guard: No nodes using this KeySet (or all are DeletePending)
Success: Remove from GroupKeySetList
Failure: Return CONSTRAINT_ERROR if in use
```

### AddGroup Logic
```
Guard: GroupID not in GroupList
Success: Add GroupInformationEntry to GroupList
Failure: Return CONSTRAINT_ERROR if exists
```

### UpdateGroup Logic
```
Guard: GroupID exists in GroupList
Actions (complex multi-branch):
  1. Update GroupInformationEntry fields
  2. If GroupKeySetID changed:
     For each node in group:
       - Add new KeySet entry (Pending)
       - Attempt to add to node
       - Mark old KeySet as DeletePending
       - Attempt to remove from node
  3. If GroupCAT/CATVersion/Permission changed:
     For each node in group:
       - Update ACL entries referencing this group (Pending)
       - Attempt to update node ACL
  4. If FriendlyName changed:
     For each endpoint in group:
       - Update GroupIDList entry (Pending)
       - Attempt to update node
```

### RemoveGroup Logic
```
Guard: GroupID exists
Guard: No nodes have this GroupID (or all are DeletePending)
Success: Remove from GroupList
Failure: Return CONSTRAINT_ERROR if in use
```

### AddPendingNode Logic
```
Guard: NodeID not in NodeList
Success: Create NodeInformationEntry with CommissioningStatusEntry=Pending
Failure: Return INVALID_CONSTRAINT if exists
```

### RefreshNode Logic (Complex Multi-Step)
```
Guard: NodeID exists in NodeList
Actions:
  1. Set CommissioningStatusEntry to Pending
  2. Synchronize Endpoint List:
     a. Read PartsList from node's Descriptor cluster
     b. Remove endpoints not in PartsList
     c. For each endpoint in PartsList:
        - For GroupIDList entries with Status=Pending: Add to node, mark Committed if success
        - For GroupIDList entries with Status=DeletePending: Remove from node, delete entry if success
        - For BindingList entries with Status=Pending: Add to node, mark Committed if success
        - For BindingList entries with Status=DeletePending: Remove from node, delete entry if success
  3. Synchronize GroupKeySetList:
     a. Read Group Keys from node
     b. For each KeySet with Status=Pending: Add to node, mark Committed if success
     c. Replace remaining keysets with node's actual keysets
  4. Synchronize ACLList:
     a. Read ACL attribute from node
     b. For each ACL with Status=Pending: Add to node, mark Committed if success
     c. Replace remaining ACLs with node's actual ACLs
  5. Set CommissioningStatusEntry to Committed
```

### AddGroupIDToEndpointForNode Logic
```
Guard: Endpoint exists for NodeID+EndpointID
Actions:
  1. Ensure Node has KeySet for this Group:
     If not present:
       - Add KeySet entry to NodeKeySetList (Status=Pending)
       - Add KeySet to node
       - If success: Mark Committed
  2. Add GroupID to Endpoint's GroupIDList:
     - Add entry (Status=Pending)
     - Add to node's group list
     - If success: Mark Committed
```

### RemoveGroupIDFromEndpointForNode Logic
```
Guard: Endpoint exists for NodeID+EndpointID
Actions:
  1. Remove GroupID from Endpoint's GroupIDList:
     - Set Status to DeletePending
     - Remove from node
     - If success: Delete entry
  2. If KeySet no longer used by any endpoint:
     - Set KeySet Status to DeletePending
     - Remove from node
     - If success: Delete from NodeKeySetList
```

### AddACLToNode Logic
```
Guard: Node exists
Actions:
  - Add ACLEntry to ACLList (Status=Pending)
  - Add to node's ACL attribute
  - If success: Mark Committed
```

### RemoveACLFromNode Logic
```
Guard: Node exists
Actions:
  - Set ACL Status to DeletePending
  - Remove from node's ACL attribute
  - If success: Delete from ACLList
```

## Guard Conditions Extracted

### Access Control Guards
- `is_anchor_administrator(caller)`: Caller is anchor admin node
- `has_administrator_CAT(caller)`: Caller has Administrator CAT
- `caller_has_fabric_admin_access()`: Caller has fabric admin privileges

### Existence Guards
- `keyset_exists(GroupKeySetID)`: KeySet in GroupKeySetList
- `group_exists(GroupID)`: Group in GroupList
- `node_exists(NodeID)`: Node in NodeList
- `endpoint_exists(NodeID, EndpointID)`: Endpoint in node's EndpointList
- `admin_exists(NodeID)`: Admin in AdminList

### State Guards
- `keyset_in_use(GroupKeySetID)`: Any group uses this keyset OR any node has it (not DeletePending)
- `group_in_use(GroupID)`: Any node has this group in GroupIDList (not DeletePending)
- `is_ipk(GroupKeySetID)`: GroupKeySetID == 0

### Status Guards
- `status_is_pending(entry)`: Entry Status = Pending
- `status_is_committed(entry)`: Entry Status = Committed
- `status_is_delete_pending(entry)`: Entry Status = DeletePending

## Timing Requirements

### Periodic Operations
- Datastore SHALL periodically review Pending and PendingDeletion entries
- Attempt to reach corresponding nodes to apply updates
- No specific timing value given (implementation-defined)

### Retry Semantics
- Temporary failures (reachability, BUSY, RESOURCE_EXHAUSTED) → periodic retry
- No timeout specified, retry until success

### Resource Exhaustion
- RESOURCE_EXHAUSTED error → notify user
- User must purge unused node information

## Cryptographic Operations

### Group Key Distribution
- **KeySet Structure**: Contains epoch keys
- **Distribution**: Datastore pushes GroupKeySetStruct to nodes
- **Synchronization**: RefreshNode reads keys from node, replaces with datastore version
- **IPK Requirement**: GroupKeySetList SHALL contain at least IPK (ID=0)

### CAT-Based Access Control
- **CAT Assignment**: Groups have GroupCAT field
- **CAT Versioning**: GroupCATVersion incremented on member removal
- **Certificate Issuance**: Administrators issue NOCs with group CAT embedded
- **Revocation**: CAT version increment invalidates old NOCs

### Certificate Chain
- **Anchor Root CA**: AnchorRootCA attribute
- **Intermediate Certs**: Administrators have ICAC field
- **NOC Issuance**: Administrators sign NOCs using ICAC

## Error States & Responses

### Error Codes
- `CONSTRAINT_ERROR`: Operation violates constraint (duplicate ID, resource in use)
- `NOT_FOUND`: Referenced entity doesn't exist
- `INVALID_CONSTRAINT`: Operation invalid (e.g., add existing node)
- `RESOURCE_EXHAUSTED`: Storage capacity limit reached
- `BUSY`: Temporary unavailability

### Reachable Error States
1. **Node Unreachable During Update**: Entry remains in Pending state
2. **Storage Exhausted**: Cannot add new entries
3. **Duplicate ID**: Attempt to add existing ID
4. **Resource In Use**: Attempt to delete resource still referenced
5. **IPK Removal Attempt**: Special-case error for critical resource

## State Invariants

### Global Invariants
- AdminList non-empty ⟹ Fabric formed
- GroupKeySetList contains IPK (ID=0)
- Exactly one admin at index 0 (Anchor)
- AnchorRootCA != null when fabric formed

### Node Entry Invariants
- Node in NodeList ⟹ Unique NodeID
- Node Committed ⟹ RefreshNode completed at least once
- Node with GroupID ⟹ Node has corresponding KeySet

### Group Invariants
- Group exists ⟹ Referenced KeySet exists
- Group has unique GroupID
- Group has unique GroupCAT per fabric

### KeySet Invariants
- KeySet with ID=0 is IPK (cannot be removed)
- KeySet referenced by group cannot be deleted

### Consistency Invariants
- Entry Status=Committed ⟹ Datastore and node in sync
- Entry Status=Pending ⟹ Update attempted but not confirmed
- Entry Status=DeletePending ⟹ Removal attempted but not confirmed

## Functions to Define

### Datastore Operations
1. `add_keyset_to_list(GroupKeySet)`
2. `update_keyset_in_list(GroupKeySet)`
3. `remove_keyset_from_list(GroupKeySetID)`
4. `add_group_to_list(GroupInfo)`
5. `update_group_in_list(GroupID, fields)`
6. `remove_group_from_list(GroupID)`
7. `add_node_to_list(NodeInfo)`
8. `remove_node_from_list(NodeID)`
9. `add_admin_to_list(AdminInfo)`
10. `remove_admin_from_list(NodeID)`

### Node Communication Functions
11. `push_keyset_to_node(NodeID, GroupKeySet)` → success/failure
12. `push_acl_to_node(NodeID, ACLEntry)` → success/failure
13. `push_groupid_to_endpoint(NodeID, EndpointID, GroupID)` → success/failure
14. `push_binding_to_endpoint(NodeID, EndpointID, Binding)` → success/failure
15. `remove_keyset_from_node(NodeID, GroupKeySetID)` → success/failure
16. `remove_acl_from_node(NodeID, ListID)` → success/failure
17. `remove_groupid_from_endpoint(NodeID, EndpointID, GroupID)` → success/failure
18. `remove_binding_from_endpoint(NodeID, EndpointID, ListID)` → success/failure

### Node Reading Functions
19. `read_partslist_from_node(NodeID)` → list of EndpointIDs
20. `read_keysets_from_node(NodeID)` → list of GroupKeySets
21. `read_acls_from_node(NodeID)` → list of ACLEntries
22. `read_grouplist_from_node(NodeID, EndpointID)` → list of GroupIDs
23. `read_bindinglist_from_node(NodeID, EndpointID)` → list of Bindings

### Utility Functions
24. `generate_constraint_error()` → error response
25. `generate_not_found_error()` → error response
26. `generate_invalid_constraint_error()` → error response
27. `generate_resource_exhausted_error()` → error response
28. `notify_user_storage_exhausted()`
29. `schedule_periodic_refresh()`

### Access Control Functions
30. `verify_anchor_administrator(caller)` → boolean
31. `verify_administrator_cat(caller)` → boolean
32. `verify_fabric_admin_access(caller)` → boolean

## Security Properties Enforced by FSM

1. **Anchor Exclusivity**: Only anchor admin can access datastore (PROP_001, PROP_003)
2. **Administrator Authentication**: Admin operations require Administrator CAT (PROP_002)
3. **Two-Phase Commit**: Pending → Committed workflow ensures atomicity (PROP_007)
4. **IPK Protection**: IPK cannot be removed (PROP_017, PROP_018)
5. **CAT Version Monotonicity**: CAT version increments on membership removal (PROP_022, PROP_036)
6. **Revocation Consistency**: DeletePending entries removed during RefreshNode (PROP_026, PROP_028)
7. **KeySet Integrity**: KeySets in use cannot be deleted (PROP_016)
8. **Group Integrity**: Groups in use cannot be deleted (PROP_015)
9. **Commissioning Atomicity**: Node must reach Committed via RefreshNode (PROP_009, PROP_029)
10. **Update Propagation**: All member nodes receive group updates (PROP_014, PROP_021)

## Complex State Transitions

### Node Commissioning Workflow
```
NodeAbsent --[AddPendingNode]--> NodePending --[RefreshNode + success]--> NodeCommitted
NodePending --[commissioning fails]--> NodeAbsent (via RemoveNode)
```

### Group Update with Member Propagation
```
GroupActive --[UpdateGroup with KeySetID change]--> 
  For each member node:
    NodeCommitted --[add new keyset]--> NodePartiallyConfigured (new keyset pending)
    NodePartiallyConfigured --[RefreshNode]--> NodeCommitted (new keyset committed, old deleted)
```

### Group Removal Workflow
```
GroupActive --[remove all members]--> 
  For each member:
    Node has group (committed) --[RemoveGroupIDFromEndpointForNode]--> Node has group (delete pending)
GroupActive (some delete pending) --[RefreshNode on all members]--> GroupActive (no members)
GroupActive (no members) --[RemoveGroup]--> GroupAbsent
```

### ACL Revocation Workflow
```
Node has ACL (committed) --[RemoveACLFromNode]--> Node has ACL (delete pending)
Node has ACL (delete pending) --[RefreshNode]--> Node has ACL (absent)
```

## Key Observations for FSM Modeling

1. **Three-State Pattern**: Most sub-entries follow Pending → Committed → DeletePending → Absent
2. **Asymmetric Synchronization**: Datastore is authoritative; node updates are best-effort with retry
3. **Eventual Consistency**: Failed updates remain Pending until future RefreshNode succeeds
4. **Security-Critical Transitions**: RefreshNode is THE synchronization point for all security updates
5. **Anchor Role**: Single point of authority enforced by access control
6. **No Explicit Timers**: Periodic refresh is implementation-defined, no hard deadlines
7. **Error Handling**: Most errors are constraint violations, not state transitions
