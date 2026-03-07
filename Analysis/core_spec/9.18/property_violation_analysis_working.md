# Property Violation Analysis - Working Document

## Analysis Metadata
- Specification: Matter R1.4, Section 9.18, Ecosystem Information Cluster
- FSM Model: ecosystem_information_cluster_fsm.json
- Properties: ecosystem_information_cluster_properties.json
- Analysis Date: 2026-01-30
- Total Properties: 30
- Analysis Status: IN_PROGRESS

## Analysis Strategy
1. For each property, identify critical FSM transitions
2. Check if guards enforce property requirements
3. Check if actions violate property invariants
4. Trace attack paths for violations
5. Cite exact specification text

---

## PROPERTY ANALYSIS

### PROP_001: DeviceName_Timestamp_Binding
**Claim**: DeviceNameLastEdit SHALL be present when DeviceName is present.

**Critical Transitions**:
- T6: DeviceNameAbsent → DeviceNamePresent (set_device_name_command)
- T8: DeviceNamePresent → DeviceNamePresent (update_device_name_command)
- T9: DeviceNamePresent → DeviceNameAbsent (clear_device_name_command)

**FSM Trace**:
- T6 actions: `set_device_name(name)`, `set_device_name_last_edit(current_timestamp())`, `generate_event(device_name_updated)`
  - ✅ Sets timestamp when name is set
- T8 actions: `set_device_name(new_name)`, `set_device_name_last_edit(current_timestamp())`, `generate_event(device_name_updated)`
  - ✅ Updates timestamp when name is updated
- T9 actions: `clear_device_name()`, `set_device_name_last_edit(0)`
  - ✅ Clears timestamp when name is cleared

**Verdict**: HOLDS
**Confidence**: 100%

Guards enforce timestamp updates atomically with name changes. No path allows name without timestamp.

---

### PROP_002: BridgedEndpoint_Accessibility_Invariant
**Claim**: BridgedEndpoint present ⟺ device accessible

**Critical Transitions**:
- T1: DeviceUninitialized → DeviceRegisteredInaccessible
- T2: DeviceUninitialized → DeviceRegisteredAccessible
- T4: DeviceRegisteredInaccessible → DeviceRegisteredAccessible
- T5: DeviceRegisteredAccessible → DeviceRegisteredInaccessible

**FSM Trace**:
- T1: guard `device_accessible == false`, no `set_bridged_endpoint()` called ✅
- T2: guard `device_accessible == true && valid_endpoint(endpoint) == true`, action `set_bridged_endpoint(endpoint)` ✅
- T4: guard `device_accessible == true && valid_endpoint(endpoint) == true`, action `set_bridged_endpoint(endpoint)` ✅
- T5: guard `device_accessible == false`, action `clear_bridged_endpoint()` ✅

**Verdict**: HOLDS
**Confidence**: 100%

State transitions correctly enforce the bidirectional relationship.

---

### PROP_003: OriginalEndpoint_Matter_Device_Constraint
**Claim**: OriginalEndpoint SHALL be present for Matter devices

**Critical Transitions**:
- T3: DeviceUninitialized → DeviceRegisteredAccessible (register_matter_device_command)

**FSM Trace**:
- T3: guard `is_matter_device == true && valid_endpoint(original_ep) == true && valid_endpoint(bridged_ep) == true`
- T3: action `set_original_endpoint(original_ep)`
  - ✅ Sets OriginalEndpoint for Matter devices

**Issue**: What about T1 and T2? They don't check if device is Matter device and don't set OriginalEndpoint.

**Attack Path**:
1. Register Matter device via T2 (not T3) with `register_device_command` trigger
2. Guard only checks `device_accessible == true && valid_endpoint(endpoint)`
3. Action does NOT call `set_original_endpoint()`
4. Result: Matter device without OriginalEndpoint

**Verdict**: VIOLATED
**Confidence**: 95%

**Violation**: T2 allows Matter devices to be registered without OriginalEndpoint.

---

### PROP_004: OriginalEndpoint_Bridge_Propagation
**Claim**: OriginalEndpoint SHALL be identical across bridge hops

**FSM Analysis**: 
The FSM does not model multi-hop bridging or data propagation between bridges. There are no transitions representing "receives_from(bridge2, bridge1, device)" or cross-bridge synchronization.

**Verdict**: UNVERIFIABLE from FSM
**Confidence**: N/A

The FSM models a single bridge instance. Property requires multi-instance behavior not captured in current FSM.

---

### PROP_005: DeviceTypes_Descriptor_Consistency
**Claim**: DeviceTypes SHALL match Descriptor cluster's DeviceTypeList

**Critical Transitions**:
- T1, T2, T3: All call `set_device_types(types)`
- T23, T23b: descriptor_change_event triggers, action `set_device_types(new_types)`

**FSM Trace**:
- Function `set_device_types()`: "Assigns DeviceTypes field to list of device type IDs from Descriptor cluster's DeviceTypeList"
- Function does NOT verify that types actually match Descriptor cluster
- No guard prevents mismatched types

**Attack Path**:
1. T23: State=DeviceRegisteredAccessible, trigger=descriptor_change_event
2. Guard: `device_types_changed(device) == true`
3. Action: `set_device_types(new_types)` - takes `new_types` from event
4. **Issue**: Who provides `new_types`? If attacker controls event, they can set arbitrary types
5. No verification that `new_types` actually matches Descriptor cluster

**Verdict**: VIOLATED (verification gap)
**Confidence**: 85%

**Violation**: FSM accepts new_types from event without verifying they match actual Descriptor cluster state.

---

### PROP_006: DeviceTypes_Validity
**Claim**: DeviceTypes SHALL contain valid device type IDs

**Critical Transitions**: T1, T2, T3, T23, T23b (all that set device types)

**FSM Trace**:
- No transition has guard checking `valid_device_type_id(type)` for each type
- Function `set_device_types()` has no validation logic
- Function description says "Assigns DeviceTypes field" but no validation mentioned

**Attack Path**:
1. T2: register_device_command with invalid device type IDs
2. No guard checks validity
3. Action `set_device_types(types)` accepts any types
4. Result: Invalid device type IDs in DeviceTypes field

**Verdict**: VIOLATED
**Confidence**: 90%

**Violation**: No validation of device type ID validity in any transition.

---

### PROP_007: UniqueLocationIDs_Reference_Integrity
**Claim**: UniqueLocationIDs SHALL reference existing LocationDirectory entries

**Critical Transitions**:
- T10: LocationUnassigned → LocationAssigned (assign_location_command)
- T11: LocationAssigned → LocationAssigned (assign_location_command)

**FSM Trace**:
- T10: guard includes `location_exists_in_directory(location_id) == true` ✅
- T11: guard includes `location_exists_in_directory(location_id) == true` ✅

**But wait - what about remote sync and conflict resolution?**
- T18: apply_remote_sync with action `set_unique_location_id(remote_location_id)`
- T22: resolve_conflict with action `apply_update_with_highest_timestamp()`

**Attack Path (T18)**:
1. Remote server sends sync data with location_id='malicious_id'
2. T18: guard only checks `remote_data_received == true && remote_unique_location_id_changed == true`
3. **No check for `location_exists_in_directory('malicious_id')`**
4. Action: `set_unique_location_id(remote_location_id)` - sets malicious_id
5. Result: Device references non-existent location

**Verdict**: VIOLATED
**Confidence**: 95%

**Violation**: T18 (remote sync) bypasses directory existence check.

---

### PROP_008: UniqueLocationIDs_Timestamp_Binding
**Claim**: UniqueLocationIDsLastEdit SHALL update when UniqueLocationIDs changes

**Critical Transitions**: T10, T11, T12, T12b, T14, T16, T18, T20, T22

**FSM Trace**:
- T10: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T11: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T12: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T12b: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T14: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T16: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T18: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T20: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅
- T22: actions include `set_unique_location_ids_last_edit(current_timestamp())` ✅

**Verdict**: HOLDS
**Confidence**: 100%

All transitions that modify UniqueLocationIDs also update timestamp.

---

### PROP_009: UniqueLocationID_Uniqueness_Per_Instance
**Claim**: UniqueLocationID SHALL be unique per location within server instance

**FSM Analysis**:
This property concerns LocationDirectory entries, not device assignments.

**Critical Transitions**:
- T26, T27: Add location to directory
- Functions: `create_ecosystem_location_struct()`, `add_to_location_directory()`

**FSM Trace**:
- T26: guard `length(location_directory) == 0` - adding first location
- T27: guard `length(location_directory) > 0`
- **No guard checks if UniqueLocationID already exists in directory**

**Attack Path**:
1. T26: Add location with id='kitchen' to empty directory
2. T27: Add another location with id='kitchen' to directory
3. Guard checks `length(location_directory) > 0` ✅ passes
4. **No check for duplicate UniqueLocationID**
5. Action: `add_to_location_directory(new_location)` adds duplicate
6. Result: Two locations with same ID

**Verdict**: VIOLATED
**Confidence**: 95%

**Violation**: T27 does not verify UniqueLocationID uniqueness before adding.

---

### PROP_010: UniqueLocationID_Change_On_Relocation
**Claim**: UniqueLocationID SHALL change on relocation (different location)

**Critical Transitions**:
- T13: LocationStable → LocationRelocationPending
- T14: LocationRelocationPending → LocationStable

**FSM Trace**:
- T13: guard `represents_different_location(old_location, new_location) == true` ✅
- T14: action `generate_new_unique_location_id()` ✅
- T14: action `set_unique_location_id(new_id)` ✅

**Verdict**: HOLDS
**Confidence**: 100%

FSM explicitly generates new ID for relocation.

---

### PROP_011: UniqueLocationID_Stable_On_Rename
**Claim**: UniqueLocationID SHALL NOT change on rename (same location)

**Critical Transitions**:
- T15: LocationStable → LocationRenamePending
- T16: LocationRenamePending → LocationStable

**FSM Trace**:
- T15: guard `same_physical_location(old_name, new_name) == true` ✅
- T16: action `keep_unique_location_id_unchanged()` ✅

**Verdict**: HOLDS
**Confidence**: 100%

FSM explicitly preserves ID for rename.

---

## VIOLATIONS FOUND SO FAR

1. **PROP_003 VIOLATED**: Matter devices can be registered via T2 without OriginalEndpoint
2. **PROP_005 VIOLATED**: DeviceTypes from descriptor_change_event not verified against actual Descriptor cluster
3. **PROP_006 VIOLATED**: No validation of device type ID validity
4. **PROP_007 VIOLATED**: Remote sync (T18) bypasses LocationDirectory existence check
5. **PROP_009 VIOLATED**: No uniqueness check when adding locations to directory (T27)

## CONTINUING ANALYSIS...

### PROP_012: UniqueLocationID_Remote_Synchronization
**Claim**: When syncing from remote, local UniqueLocationID SHALL change iff remote UniqueLocationID changed

**Critical Transitions**:
- T17: LocationStable → RemoteSyncPending
- T18: RemoteSyncPending → LocationStable (remote ID changed)
- T19: LocationStable → RemoteSyncPending
- T20: RemoteSyncPending → LocationStable (remote ID unchanged)

**FSM Trace**:
- T17: guard checks `remote_unique_location_id_changed == true` ✅
- T18: action `set_unique_location_id(remote_location_id)` - changes local ID ✅
- T19: guard checks `remote_unique_location_id_changed == false` ✅
- T20: action `keep_unique_location_id_unchanged()` - preserves local ID ✅

**Verdict**: HOLDS
**Confidence**: 100%

Guards correctly distinguish between remote ID change vs unchanged.

---

### PROP_013: Fabric_Scoped_Access_Isolation
**Claim**: Fabric scoping ensures data isolation between fabrics

**FSM Analysis**:
The FSM does not model fabric isolation or access control checks. No transitions have guards checking fabric membership. No actions enforce fabric-scoped access.

**Verdict**: UNVERIFIABLE from FSM
**Confidence**: N/A

Fabric isolation is enforced at access layer (below FSM abstraction level).

---

### PROP_014: User_Consent_Required
**Claim**: DeviceName and LocationDescriptor from external sources SHALL require user consent

**Critical Transitions**:
- T6: set_device_name_command
- T7: set_device_name_command (consent denied)
- T8: update_device_name_command
- T10, T11: assign_location_command
- T29: update_location_descriptor_command

**FSM Trace - Device Name**:
- T6: guard `user_consent_given == true && length(name) <= 64` ✅
- T7: guard `user_consent_given == false`, action `generate_event(consent_required_error)` ✅
- T8: guard `user_consent_given == true` ✅

**FSM Trace - Location Assignment**:
- T10: guard `user_consent_given == true` ✅
- T11: guard `user_consent_given == true` ✅

**FSM Trace - Location Descriptor Update**:
- T29: guard `user_consent_given == true` ✅

**BUT - What about remote sync?**
- T18: apply_remote_sync with `set_location_descriptor(remote_descriptor)`
- T20: apply_remote_sync with `set_location_descriptor(remote_descriptor)`
- **No guard checks `user_consent_given == true`**

**Attack Path**:
1. Remote server sends sync data with new location descriptor
2. T18: guard only checks `remote_data_received == true && remote_unique_location_id_changed == true`
3. **No consent check**
4. Action: `set_location_descriptor(remote_descriptor)` - sets external data without consent
5. Result: External location descriptor applied without user consent

**Verdict**: VIOLATED
**Confidence**: 90%

**Violation**: T18, T20 (remote sync) bypass user consent requirement for location descriptors.

---

### PROP_015: Read_Access_Privilege_Required
**Claim**: Read access to sensitive data requires sufficient privileges

**FSM Analysis**:
The FSM does not model read operations or access control enforcement for reads. No transitions represent "read" or "query" operations. Access control is enforced at the protocol layer below FSM.

**Verdict**: UNVERIFIABLE from FSM
**Confidence**: N/A

Read access control is not modeled in this FSM (only write operations).

---

### PROP_016: Timestamp_Monotonicity
**Claim**: Timestamps SHALL be monotonically increasing

**Critical Function**: `current_timestamp()`

**FSM Trace**:
- Function `current_timestamp()`: "Returns current time in microseconds since epoch. MUST be monotonically increasing."
- Function definition includes monotonicity requirement
- BUT: No guard enforces `new_timestamp > old_timestamp`

**Attack Path**:
1. System clock goes backwards (NTP adjustment, clock skew, attacker manipulation)
2. T8: update_device_name_command triggered
3. Guard: `current_timestamp() > device_name_last_edit` - **This guard exists!** ✅
4. If clock goes backwards, guard fails, transition blocked ✅

**Wait, let me check other transitions**:
- T8: guard includes `current_timestamp() > device_name_last_edit` ✅
- But T6, T10, T11 don't check old timestamp (because they're setting first time)

**Actually, let me reconsider**:
- T6: First name set, device_name_last_edit == 0, so any timestamp > 0 ✅
- T10: First location set, unique_location_ids_last_edit == 0, so any timestamp > 0 ✅

**But what about these?**:
- T1, T2, T3: call `initialize_timestamps_to_zero()` - sets to 0, not current time
- Initial timestamps are 0, then first update sets to current time
- Subsequent updates must have timestamp > previous

**Issue**: What if `current_timestamp()` returns same value twice?
- T8: guard `current_timestamp() > device_name_last_edit` would fail if equal
- T11: no guard checking timestamp > previous

**Attack Path for T11**:
1. Device assigned to location A at timestamp T
2. Immediately assign to location B (within same microsecond)
3. T11: guard does NOT check `current_timestamp() > unique_location_ids_last_edit`
4. Action: `set_unique_location_ids_last_edit(current_timestamp())` could set same timestamp T
5. Result: Two different states with same timestamp (breaks conflict resolution)

**Verdict**: PARTIALLY VIOLATED
**Confidence**: 75%

**Violation**: T11 (and other location transitions) don't enforce strict monotonicity like T8 does.

---

### PROP_017: Cluster_Revision_Support
**Claim**: ClusterRevision SHALL be highest supported revision

**FSM Analysis**:
The FSM does not model ClusterRevision attribute or revision negotiation. No transitions handle revision updates or validation.

**Verdict**: UNVERIFIABLE from FSM
**Confidence**: N/A

ClusterRevision is static metadata not modeled in FSM.

---

### PROP_018: Conflict_Resolution_Last_Write_Wins
**Claim**: Conflict resolution SHALL use highest timestamp (last-write-wins)

**Critical Transitions**:
- T21: NoConflict → ConcurrentUpdateDetected
- T22: ConcurrentUpdateDetected → NoConflict

**FSM Trace**:
- T21: guard `multiple_instances_updating_simultaneously(updates) == true`
- T21: action `store_competing_updates(updates)`
- T22: action `apply_update_with_highest_timestamp()` ✅
- T22: action `drop_other_updates()`

**Function `apply_update_with_highest_timestamp()`**:
- "Selects update with highest UniqueLocationIDsLastEdit timestamp and applies it to device state"
- ✅ Implements last-write-wins correctly

**Verdict**: HOLDS
**Confidence**: 100%

FSM implements last-write-wins via highest timestamp selection.

---

### PROP_019: DeviceName_Length_Constraint
**Claim**: DeviceName SHALL be ≤ 64 characters

**Critical Transitions**: T6, T8

**FSM Trace**:
- T6: guard `user_consent_given == true && length(name) <= 64` ✅
- T8: guard `user_consent_given == true && length(new_name) <= 64 && current_timestamp() > device_name_last_edit` ✅

**Verdict**: HOLDS
**Confidence**: 100%

Guards enforce 64-character limit.

---

### PROP_020: UniqueLocationID_Length_Constraint
**Claim**: UniqueLocationID SHALL be ≤ 64 characters

**Critical Transitions**: T26, T27 (add location to directory), T14 (generate new ID)

**FSM Trace**:
- T26: No guard checking `length(UniqueLocationID) <= 64`
- T27: No guard checking `length(UniqueLocationID) <= 64`
- T14: action `generate_new_unique_location_id()` - function doesn't specify length constraint

**Function `generate_new_unique_location_id()`**:
- "Generates fresh UniqueLocationID that differs from previous ID. Typically includes timestamp and random component."
- **No mention of length constraint**

**Attack Path**:
1. T14: Process relocation, action `generate_new_unique_location_id()`
2. Function generates ID longer than 64 characters (e.g., very long timestamp + long random string)
3. No validation prevents this
4. Result: UniqueLocationID exceeds 64 characters

**Verdict**: VIOLATED
**Confidence**: 85%

**Violation**: No length validation when generating or accepting UniqueLocationIDs.

---

### PROP_021: UniqueLocationIDs_List_Length_Constraint
**Claim**: UniqueLocationIDs list SHALL have ≤ 64 entries, each ≤ 64 characters

**Critical Transitions**: T10, T11

**FSM Trace**:
- T10: guard `user_consent_given == true && location_exists_in_directory(location_id) == true && length(unique_location_ids) < 64` ✅
- T11: guard `user_consent_given == true && location_exists_in_directory(location_id) == true && length(unique_location_ids) < 64 && contains(unique_location_ids, location_id) == false` ✅

**List count constraint**: ✅ Enforced (< 64)

**Individual ID length**: No guard checks `length(location_id) <= 64` in T10 or T11

**Attack Path**:
1. Create location in directory with ID = 65-character string
2. T10: assign_location_command with that ID
3. Guard checks `length(unique_location_ids) < 64` ✅ passes (list size, not ID size)
4. No check for `length(location_id) <= 64`
5. Action: `add_to_unique_location_ids(location_id)` adds oversized ID
6. Result: List contains ID > 64 characters

**Verdict**: PARTIALLY VIOLATED
**Confidence**: 80%

**Violation**: List count is enforced, but individual ID length is not validated.

---

### PROP_022: Concurrent_Update_Acceptable_Data_Loss
**Claim**: System MAY lose one update during concurrent conflict (acceptable per spec)

**FSM Trace**:
- T22: action `apply_update_with_highest_timestamp()` - applies one update ✅
- T22: action `drop_other_updates()` - drops the rest ✅

**Specification Note**: "Per specification NOTE, when multiple server instances update UniqueLocationIDs simultaneously, it is possible one of the updates will be missed. This is considered an acceptable limitation."

**Verdict**: HOLDS (by design)
**Confidence**: 100%

FSM implements acceptable data loss as specified.

---

### PROP_023: Endpoint_BridgedNode_DeviceType_Required
**Claim**: Endpoints hosting this cluster SHALL have BridgedNode in DeviceTypes

**FSM Analysis**:
This property is about cluster hosting requirements, not operational behavior. No transitions model endpoint device type validation.

**Verdict**: UNVERIFIABLE from FSM
**Confidence**: N/A

Cluster hosting requirements are enforced at deployment, not runtime.

---

### PROP_024: Unmodified_Field_Timestamp_Zero
**Claim**: If field never modified, timestamp SHALL be 0

**Critical Transitions**:
- T1, T2, T3: call `initialize_timestamps_to_zero()`

**FSM Trace**:
- Initial states have timestamps == 0 ✅
- State invariants:
  - DeviceNameAbsent: `device_name_last_edit == 0` ✅
  - LocationUnassigned: `unique_location_ids_last_edit == 0` ✅

**Verdict**: HOLDS
**Confidence**: 100%

Initial state correctly sets timestamps to 0.

---

### PROP_025: Single_Instance_History_Only
**Claim**: Clients SHALL use single-instance history for change detection

**FSM Analysis**:
This property is about client behavior and data interpretation, not server FSM behavior. FSM models server state machine, not client logic.

**Verdict**: UNVERIFIABLE from FSM
**Confidence**: N/A

Client-side behavior not modeled in server FSM.

---

### PROP_026: LocationDescriptor_Timestamp_Binding
**Claim**: LocationDescriptorLastEdit SHALL update when LocationDescriptor changes

**Critical Transitions**: T30 (apply location descriptor update)

**FSM Trace**:
- T30: action `update_location_descriptor_in_directory(new_descriptor)` 
- T30: action `set_location_descriptor_last_edit_in_directory(current_timestamp())` ✅

**But what about T29?**
- T29: Initiates update, transitions to LocationDescriptorUpdatePending
- T29: action `set_location_change_pending(true)`
- **Does NOT update descriptor or timestamp yet** ✅ Correct (pending state)

**What about remote sync (T18, T20)?**
- T18: action `set_location_descriptor(remote_descriptor)`
- T18: action `set_location_descriptor_last_edit(remote_timestamp)`
- **Uses remote timestamp, not local current_timestamp()**

**Is this correct?** Actually yes, because remote sync should preserve remote timestamp for conflict resolution.

**But wait - T14, T16 also modify location descriptors**:
- T14: action `set_location_descriptor(new_descriptor)` (relocation)
- T14: action `set_location_descriptor_last_edit(current_timestamp())` ✅
- T16: action `set_location_descriptor(new_name)` (rename)
- T16: action `set_location_descriptor_last_edit(current_timestamp())` ✅

**Verdict**: HOLDS
**Confidence**: 95%

All transitions that modify LocationDescriptor also update timestamp.

---

### PROP_027: LocationDirectory_Reference_Integrity
**Claim**: UniqueLocationIDs in directory SHALL be unique per server instance

**Already analyzed as PROP_009** - VIOLATED

---

### PROP_028: LocationDirectory_Remove_Safety
**Claim**: Cannot remove location from directory while devices reference it

**Critical Transitions**: T28, T28b (remove location from directory)

**FSM Trace**:
- T28: guard `location_exists_in_directory(location_id) == true && location_in_use_by_devices(location_id) == false && length(location_directory) == 1`
  - ✅ Checks `location_in_use_by_devices() == false`
- T28b: guard `location_exists_in_directory(location_id) == true && location_in_use_by_devices(location_id) == false && length(location_directory) > 1`
  - ✅ Checks `location_in_use_by_devices() == false`

**Verdict**: HOLDS
**Confidence**: 100%

Guards prevent removing in-use locations.

---

### PROP_029: LocationDescriptor_User_Consent
**Claim**: External LocationDescriptor SHALL require user consent

**Already analyzed as part of PROP_014** - VIOLATED
Remote sync (T18, T20) bypasses consent check for location descriptors.

---

### PROP_030: LocationDescriptor_Length_Constraint
**Claim**: LocationDescriptor SHALL conform to type constraints

**Critical Transitions**: T29, T30 (update location descriptor)

**FSM Trace**:
- T29: guard `user_consent_given == true` - no length check
- T30: action `update_location_descriptor_in_directory(new_descriptor)` - no length validation

**Function `update_location_descriptor_in_directory()`**:
- "Updates LocationDescriptor field of specified location in LocationDirectory"
- **No mention of length constraint or validation**

**Attack Path**:
1. T29: update_location_descriptor_command with very long descriptor (>64 chars)
2. Guard only checks consent, not length
3. T30: action updates descriptor without validation
4. Result: LocationDescriptor exceeds length constraint

**Verdict**: VIOLATED
**Confidence**: 85%

**Violation**: No length validation for LocationDescriptor updates.

---

## COMPLETE VIOLATIONS SUMMARY

### Critical Violations (3)
1. **PROP_007**: Remote sync bypasses LocationDirectory existence check (T18)
2. **PROP_014**: Remote sync bypasses user consent for location descriptors (T18, T20)
3. **PROP_003**: Matter devices can be registered without OriginalEndpoint (T2)

### High Violations (5)
4. **PROP_005**: DeviceTypes from events not verified against Descriptor cluster (T23)
5. **PROP_006**: No validation of device type ID validity (T1, T2, T3, T23)
6. **PROP_009**: No uniqueness check for UniqueLocationIDs in directory (T27)
7. **PROP_020**: No length validation for UniqueLocationID generation (T14, T26, T27)
8. **PROP_030**: No length validation for LocationDescriptor (T29, T30)

### Medium Violations (2)
9. **PROP_016**: Timestamp monotonicity not enforced for location assignments (T11, T12, T14, etc.)
10. **PROP_021**: Individual location ID length not validated (T10, T11)

## Properties Holding (15)
- PROP_001: DeviceName_Timestamp_Binding ✅
- PROP_002: BridgedEndpoint_Accessibility_Invariant ✅
- PROP_008: UniqueLocationIDs_Timestamp_Binding ✅
- PROP_010: UniqueLocationID_Change_On_Relocation ✅
- PROP_011: UniqueLocationID_Stable_On_Rename ✅
- PROP_012: UniqueLocationID_Remote_Synchronization ✅
- PROP_018: Conflict_Resolution_Last_Write_Wins ✅
- PROP_019: DeviceName_Length_Constraint ✅
- PROP_022: Concurrent_Update_Acceptable_Data_Loss ✅
- PROP_024: Unmodified_Field_Timestamp_Zero ✅
- PROP_026: LocationDescriptor_Timestamp_Binding ✅
- PROP_028: LocationDirectory_Remove_Safety ✅

## Properties Unverifiable from FSM (5)
- PROP_004: Multi-bridge propagation not modeled
- PROP_013: Fabric isolation enforced below FSM layer
- PROP_015: Read access control not modeled
- PROP_017: ClusterRevision not modeled
- PROP_023: Cluster hosting requirements not modeled
- PROP_025: Client behavior not modeled

## NEXT: Generate detailed JSON output with specification citations
