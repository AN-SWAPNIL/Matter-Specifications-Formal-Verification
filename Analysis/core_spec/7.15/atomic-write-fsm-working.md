# Atomic Write FSM Extraction - Working Document

## Section Analysis: 7.15 Atomic Write Protocol

### Protocol Overview
Three-stage protocol:
1. BeginWrite - Client requests atomic write, server validates and creates state
2. Write Requests - Client sends writes, server buffers them
3. CommitWrite/RollbackWrite - Client commits or cancels, server applies all or none

---

## State Identification

### Client-Side States (from client perspective)
1. **IDLE** - No active atomic write transaction
2. **AWAITING_BEGIN_RESPONSE** - Sent BeginWrite, waiting for server response
3. **TRANSACTION_ACTIVE** - BeginWrite succeeded, can send write requests
4. **AWAITING_COMMIT_RESPONSE** - Sent CommitWrite, waiting for server response
5. **AWAITING_ROLLBACK_RESPONSE** - Sent RollbackWrite, waiting for server response
6. **TRANSACTION_COMPLETED** - Transaction finished (success or failure)

### Server-Side States (per client, per cluster/endpoint)
1. **NO_STATE** - No Atomic Write State associated with client for this cluster/endpoint
2. **STATE_CREATED** - Atomic Write State exists, accepting write requests
3. **COMMIT_VALIDATION** - Validating pending writes before application
4. **COMMIT_APPLICATION** - Applying validated writes
5. **ROLLBACK_IN_PROGRESS** - Discarding pending writes
6. **TIMEOUT_EXPIRED** - Timeout elapsed, automatic rollback triggered

---

## Key Attributes Defining States

### Server-Side Attributes
- `atomic_write_state_exists`: boolean
- `endpoint_no`: integer
- `cluster_id`: integer
- `atomic_writer_id`: Operational Node ID
- `accessing_fabric`: fabric identifier
- `attrib_ids_set`: set of attribute IDs
- `pending_writes`: map of attribute_id -> pending_value
- `timeout_value`: uint16 (milliseconds)
- `timeout_timer`: countdown timer
- `validation_status`: SUCCESS | FAILURE | CONSTRAINT_ERROR | DATA_VERSION_MISMATCH | etc.

### Client-Side Attributes
- `has_active_transaction`: boolean
- `requested_attributes`: list of attribute IDs
- `accepted_attributes`: list of attribute IDs (from server response)
- `requested_timeout`: uint16
- `effective_timeout`: uint16 (from server)
- `transaction_status`: SUCCESS | FAILURE | etc.

---

## Transitions Extraction

### BeginWrite Flow

#### Client Sends BeginWrite
- **From**: IDLE
- **To**: AWAITING_BEGIN_RESPONSE
- **Trigger**: begin_atomic_write command
- **Guard**: has_active_transaction == false
- **Actions**: 
  - send_atomic_request(BeginWrite, attribute_list, timeout)
  - requested_attributes := attribute_list
  - requested_timeout := timeout

#### Server Receives BeginWrite - Validation Phase

**Validation 1: Check Accessing Fabric**
- **From**: NO_STATE
- **To**: NO_STATE (stay)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: accessing_fabric == NULL
- **Actions**: 
  - send_atomic_response(INVALID_COMMAND, [], 0)

**Validation 2: Check Atomic Writer ID**
- **From**: NO_STATE
- **To**: NO_STATE (stay)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: accessing_fabric != NULL && (atomic_writer_id_unavailable() || !is_valid_operational_node_id(atomic_writer_id))
- **Actions**: 
  - send_atomic_response(INVALID_COMMAND, [], 0)

**Validation 3: Check Empty AttributeRequests**
- **From**: NO_STATE
- **To**: NO_STATE (stay)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: accessing_fabric != NULL && is_valid_operational_node_id(atomic_writer_id) && |AttributeRequests| == 0
- **Actions**: 
  - send_atomic_response(INVALID_COMMAND, [], 0)

**Validation 4: Check Duplicate AttributeRequests**
- **From**: NO_STATE
- **To**: NO_STATE (stay)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: accessing_fabric != NULL && is_valid_operational_node_id(atomic_writer_id) && |AttributeRequests| > 0 && has_duplicates(AttributeRequests)
- **Actions**: 
  - send_atomic_response(INVALID_COMMAND, [], 0)

**Validation 5: Check Unsupported Attributes**
- **From**: NO_STATE
- **To**: NO_STATE (stay)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: accessing_fabric != NULL && is_valid_operational_node_id(atomic_writer_id) && |AttributeRequests| > 0 && !has_duplicates(AttributeRequests) && contains_unsupported_attributes(AttributeRequests)
- **Actions**: 
  - send_atomic_response(INVALID_COMMAND, [], 0)

**Validation 6: Check Existing State Conflict**
- **From**: NO_STATE (but checking global state)
- **To**: NO_STATE (stay)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: all_basic_validations_passed() && client_has_existing_state_on_same_cluster_endpoint(client, cluster, endpoint)
- **Actions**: 
  - send_atomic_response(INVALID_IN_STATE, [], 0)

**Validation 7: Check Missing Timeout**
- **From**: NO_STATE
- **To**: NO_STATE (stay)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: all_basic_validations_passed() && !client_has_existing_state_on_same_cluster_endpoint() && !has_timeout_field(request)
- **Actions**: 
  - send_atomic_response(INVALID_COMMAND, [], 0)

**Success Path: Attribute Validation**
- **From**: NO_STATE
- **To**: STATE_CREATED OR NO_STATE (depends on attribute statuses)
- **Trigger**: receive_atomic_request(BeginWrite)
- **Guard**: all_validations_passed() && has_timeout_field(request)
- **Actions**: 
  - attribute_statuses := validate_all_attributes(AttributeRequests)
  - expanded_attributes := apply_shared_resource_expansion(AttributeRequests, attribute_statuses)
  - if any_status_not_success(attribute_statuses) then:
    - send_atomic_response(FAILURE, attribute_statuses, 0)
    - [STAY in NO_STATE]
  - else:
    - create_atomic_write_state(endpoint, cluster, atomic_writer_id, accessing_fabric, expanded_attributes)
    - effective_timeout := negotiate_timeout(requested_timeout, max_timeout_for_attributes)
    - start_timeout_timer(effective_timeout)
    - send_atomic_response(SUCCESS, attribute_statuses, effective_timeout)
    - [TRANSITION to STATE_CREATED]

**Note**: Need to split the above into separate transitions for each branch

---

## Function Definitions Needed

1. `atomic_writer_id_unavailable()` - Check if Atomic Writer ID is available
2. `is_valid_operational_node_id(id)` - Validate Operational Node ID
3. `has_duplicates(list)` - Check for duplicate values in list
4. `contains_unsupported_attributes(list)` - Check if any attribute is unsupported
5. `client_has_existing_state_on_same_cluster_endpoint(client, cluster, endpoint)` - Check for existing state
6. `validate_all_attributes(attr_list)` - Perform per-attribute validation (privilege, atomic quality, busy, resources)
7. `apply_shared_resource_expansion(requested, statuses)` - Add attributes due to shared resources
8. `any_status_not_success(statuses)` - Check if any status is not SUCCESS
9. `create_atomic_write_state(...)` - Create new Atomic Write State
10. `negotiate_timeout(requested, max)` - Return min(requested, max)
11. `start_timeout_timer(duration)` - Start countdown timer
12. `send_atomic_response(status, attr_statuses, timeout)` - Send AtomicResponse
13. `send_atomic_request(type, attrs, timeout)` - Send AtomicRequest

---

## Per-Attribute Validation Logic

For each attribute in AttributeRequests:
1. If client lacks privilege → UNSUPPORTED_ACCESS
2. If attribute doesn't support atomic writes → INVALID_COMMAND
3. If attribute currently in different atomic write → BUSY
4. If server lacks resources to pend writes → RESOURCE_EXHAUSTED
5. Otherwise → SUCCESS

---

## Write Request Phase

**Client Sends Write Request**
- **From**: TRANSACTION_ACTIVE
- **To**: TRANSACTION_ACTIVE (stay)
- **Trigger**: write_attribute(attr_id, value)
- **Guard**: attr_id in accepted_attributes
- **Actions**: send_write_request(attr_id, value)

**Server Receives Write Request - Invalid State**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: receive_write_request(attr_id, value)
- **Guard**: !is_associated_with_state(client, state) || !contains(state.attrib_ids, attr_id)
- **Actions**: send_write_response(INVALID_IN_STATE, attr_id)

**Server Receives Write Request - Success**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: receive_write_request(attr_id, value)
- **Guard**: is_associated_with_state(client, state) && contains(state.attrib_ids, attr_id) && can_buffer_write(attr_id, value)
- **Actions**: 
  - buffer_pending_write(attr_id, value)
  - send_write_response(SUCCESS, attr_id)

**Server Receives Write Request - Cannot Succeed**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: receive_write_request(attr_id, value)
- **Guard**: is_associated_with_state(client, state) && contains(state.attrib_ids, attr_id) && !can_buffer_write(attr_id, value)
- **Actions**: 
  - error_code := determine_write_error(attr_id, value)
  - send_write_response(error_code, attr_id)

---

## Read Request with Atomic Write State

**Client Reads Attribute - Has Pending Write**
- **From**: TRANSACTION_ACTIVE
- **To**: TRANSACTION_ACTIVE (stay)
- **Trigger**: read_attribute(attr_id)
- **Guard**: attr_id in accepted_attributes && has_pending_write(attr_id)
- **Actions**: 
  - send_read_request(attr_id)

**Server Processes Read - Return Pending Value**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: receive_read_request(attr_id)
- **Guard**: is_associated_with_state(client, state) && has_pending_write_for_client(client, attr_id)
- **Actions**: 
  - value := get_pending_value(client, attr_id)
  - send_read_response(SUCCESS, attr_id, value)

**Server Processes Read - Return Current Value**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: receive_read_request(attr_id)
- **Guard**: is_associated_with_state(client, state) && !has_pending_write_for_client(client, attr_id)
- **Actions**: 
  - value := get_current_value(attr_id)
  - send_read_response(SUCCESS, attr_id, value)

---

## External Command Modification

**Server Receives External Command**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: receive_command(cmd)
- **Guard**: modifies_atomic_attribute(cmd, attr_id) && contains(state.attrib_ids, attr_id)
- **Actions**: 
  - apply_command_immediately(cmd)
  - update_data_version(attr_id)
  - mark_potential_commit_failure(state)

---

## Timeout Expiry

**Automatic Timeout Rollback**
- **From**: STATE_CREATED
- **To**: NO_STATE
- **Trigger**: timeout_timer_expiry
- **Guard**: timeout_timer == 0 && !received_commit_request()
- **Actions**: 
  - discard_all_pending_writes(state)
  - discard_atomic_write_state(state)
  - [No response sent - timeout is automatic]

---

## CommitWrite Flow

**Client Sends CommitWrite**
- **From**: TRANSACTION_ACTIVE
- **To**: AWAITING_COMMIT_RESPONSE
- **Trigger**: commit_transaction command
- **Guard**: has_active_transaction == true
- **Actions**: 
  - send_atomic_request(CommitWrite, accepted_attributes, NULL)

**Server Receives CommitWrite - State Mismatch**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay, but sends error)
- **Trigger**: receive_atomic_request(CommitWrite)
- **Guard**: !state_matches(client, state, endpoint, cluster, requested_attrs)
- **Actions**: 
  - send_atomic_response(INVALID_IN_STATE, [], 0)

**Server Receives CommitWrite - Begin Validation**
- **From**: STATE_CREATED
- **To**: COMMIT_VALIDATION
- **Trigger**: receive_atomic_request(CommitWrite)
- **Guard**: state_matches(client, state, endpoint, cluster, requested_attrs)
- **Actions**: 
  - [Enter validation phase]

**Validation: Create Attribute Status List**
- **From**: COMMIT_VALIDATION
- **To**: COMMIT_VALIDATION (internal step)
- **Guard**: true
- **Actions**: 
  - attribute_statuses := validate_all_pending_writes(state.pending_writes)

**Validation: Any Write Will Fail**
- **From**: COMMIT_VALIDATION
- **To**: NO_STATE
- **Trigger**: validation_complete
- **Guard**: any_validation_failed(attribute_statuses)
- **Actions**: 
  - discard_all_pending_writes(state)
  - discard_atomic_write_state(state)
  - send_atomic_response(FAILURE, attribute_statuses, 0)

**Validation: Constraint Violation**
- **From**: COMMIT_VALIDATION
- **To**: NO_STATE
- **Trigger**: validation_complete
- **Guard**: !any_validation_failed(attribute_statuses) && would_violate_constraints(state.pending_writes)
- **Actions**: 
  - discard_all_pending_writes(state)
  - discard_atomic_write_state(state)
  - send_atomic_response(CONSTRAINT_ERROR, attribute_statuses, 0)

**Validation: Success - Proceed to Application**
- **From**: COMMIT_VALIDATION
- **To**: COMMIT_APPLICATION
- **Trigger**: validation_complete
- **Guard**: !any_validation_failed(attribute_statuses) && !would_violate_constraints(state.pending_writes)
- **Actions**: 
  - [Proceed to application phase]

**Application: Attempt All Writes**
- **From**: COMMIT_APPLICATION
- **To**: COMMIT_APPLICATION (internal)
- **Guard**: true
- **Actions**: 
  - application_results := apply_all_pending_writes_atomically(state.pending_writes)

**Application: Any Write Failed**
- **From**: COMMIT_APPLICATION
- **To**: NO_STATE
- **Trigger**: application_complete
- **Guard**: any_application_failed(application_results)
- **Actions**: 
  - [Rollback may have occurred at storage layer]
  - discard_atomic_write_state(state)
  - send_atomic_response(FAILURE, application_results, 0)

**Application: All Writes Succeeded**
- **From**: COMMIT_APPLICATION
- **To**: NO_STATE
- **Trigger**: application_complete
- **Guard**: !any_application_failed(application_results)
- **Actions**: 
  - discard_atomic_write_state(state)
  - send_atomic_response(SUCCESS, [], 0)

---

## RollbackWrite Flow

**Client Sends RollbackWrite**
- **From**: TRANSACTION_ACTIVE OR AWAITING_BEGIN_RESPONSE
- **To**: AWAITING_ROLLBACK_RESPONSE
- **Trigger**: rollback_transaction command
- **Guard**: has_active_transaction == true OR rejection_of_begin_response == true
- **Actions**: 
  - send_atomic_request(RollbackWrite, accepted_attributes OR requested_attributes, NULL)

**Server Receives RollbackWrite - State Mismatch**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: receive_atomic_request(RollbackWrite)
- **Guard**: !state_matches(client, state, endpoint, cluster, requested_attrs)
- **Actions**: 
  - send_atomic_response(INVALID_IN_STATE, [], 0)

**Server Receives RollbackWrite - Success**
- **From**: STATE_CREATED
- **To**: NO_STATE
- **Trigger**: receive_atomic_request(RollbackWrite)
- **Guard**: state_matches(client, state, endpoint, cluster, requested_attrs)
- **Actions**: 
  - discard_all_pending_writes(state)
  - discard_atomic_write_state(state)
  - send_atomic_response(SUCCESS, [], 0)

---

## Timer Management

**Timer Countdown**
- **From**: STATE_CREATED
- **To**: STATE_CREATED (stay)
- **Trigger**: timer_tick
- **Guard**: timeout_timer > 0
- **Actions**: 
  - timeout_timer := timeout_timer - 1

---

## All Functions to Define

1. atomic_writer_id_unavailable
2. is_valid_operational_node_id
3. has_duplicates
4. contains_unsupported_attributes
5. client_has_existing_state_on_same_cluster_endpoint
6. validate_all_attributes
7. apply_shared_resource_expansion
8. any_status_not_success
9. create_atomic_write_state
10. negotiate_timeout
11. start_timeout_timer
12. send_atomic_response
13. send_atomic_request
14. is_associated_with_state
15. buffer_pending_write
16. can_buffer_write
17. determine_write_error
18. has_pending_write_for_client
19. get_pending_value
20. get_current_value
21. modifies_atomic_attribute
22. apply_command_immediately
23. update_data_version
24. mark_potential_commit_failure
25. discard_all_pending_writes
26. discard_atomic_write_state
27. state_matches
28. validate_all_pending_writes
29. any_validation_failed
30. would_violate_constraints
31. apply_all_pending_writes_atomically
32. any_application_failed

---

## Security Properties

1. Atomic Writer ID Authentication - Only valid Operational Node IDs from Secure Sessions
2. Fabric Isolation - Accessing fabric must be present
3. State Isolation - Only associated client can write to state's attributes
4. Pending Write Visibility - Pending writes only visible to owning client
5. All-or-Nothing Atomicity - All writes succeed or all fail
6. Timeout Enforcement - Automatic rollback on timeout
7. Privilege-Based Access - Per-attribute privilege checks
8. Resource Protection - RESOURCE_EXHAUSTED when insufficient resources
9. Attribute Locking - BUSY when attribute in different atomic write
10. Constraint Validation - Collective constraint checking before commit

---

## Cryptographic Operations

None in this section. This is a transaction protocol without cryptographic operations.
The security relies on:
- Session layer authentication (Atomic Writer ID from Secure Session Context)
- Fabric isolation (from session layer)
- Access control (privilege checks)

---

## Assumptions

1. Session layer correctly provides Atomic Writer ID from Peer Node ID
2. Session layer correctly associates accessing fabric
3. Server has sufficient resources under normal operation
4. Timer mechanism is reliable
5. Data version tracking is accurate
6. Pending write buffer has proper isolation
7. Integrity checks and constraint validators are correct
8. Fabric isolation mechanism prevents cross-fabric access
9. Attribute locking prevents concurrent access
10. Storage layer supports atomic commit/rollback

---

## Next Step: Convert to Formal FSM JSON
