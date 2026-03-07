# Commissioner Control Cluster - FSM Analysis

## State-Defining Attributes

1. **session_type**: CASE | PASE | none
2. **approval_status**: none | pending_event | approved | denied | timeout
3. **request_record**: exists (with RequestID, ClientNodeID, VendorID, ProductID) | does_not_exist
4. **commissioning_window_status**: closed | open | opening
5. **has_responded_with_window**: true | false (tracks if ReverseOpenCommissioningWindow sent for this RequestID)
6. **timer_active**: true | false (for ResponseTimeoutSeconds)
7. **event_generated**: true | false (CommissioningRequestResult event)

## Key Protocol Variables

- **RequestID** (uint64): Unique identifier for approval request
- **ClientNodeID** (node-id): Identity of requesting client
- **FabricID**: Fabric context of the session
- **VendorID** (vendor-id): Expected device vendor
- **ProductID** (uint16): Expected device product
- **Label** (string, max 64): Optional device label
- **ResponseTimeoutSeconds** (uint16, 30-120): Client timeout for response
- **StatusCode**: SUCCESS | TIMEOUT | FAILURE

## Protocol Flow States

### State 1: Idle
- **Invariants**: 
  - No active approval request
  - approval_status == none
  - request_record == does_not_exist
- **Description**: Initial state, waiting for approval request

### State 2: CASE_Session_Validation_Failed
- **Invariants**:
  - session_type != CASE
- **Description**: Command received without proper CASE session

### State 3: Device_Category_Check_Failed
- **Invariants**:
  - device_category not in SupportedDeviceCategories
- **Description**: Requested device category not supported

### State 4: Approval_Request_Accepted
- **Invariants**:
  - approval_status == pending_event
  - request_record exists
  - event_generated == false
- **Description**: Server accepted request, will generate event

### State 5: Duplicate_RequestID_Detected
- **Invariants**:
  - request_record exists with same RequestID + ClientNodeID
  - previous request still pending (not completed)
- **Description**: Client reused RequestID while previous still active

### State 6: Approval_Granted
- **Invariants**:
  - approval_status == approved
  - event_generated == true
  - StatusCode == SUCCESS
  - has_responded_with_window == false
- **Description**: Server granted approval, ready for CommissionNode

### State 7: Approval_Denied
- **Invariants**:
  - approval_status == denied
  - event_generated == true
  - StatusCode == FAILURE
- **Description**: Server denied approval

### State 8: Approval_Timeout
- **Invariants**:
  - approval_status == timeout
  - event_generated == true
  - StatusCode == TIMEOUT
- **Description**: User approval timed out

### State 9: Validating_CommissionNode
- **Invariants**:
  - session_type == CASE
  - Received CommissionNode command
- **Description**: Server validating CommissionNode preconditions

### State 10: CommissionNode_NodeID_Mismatch
- **Invariants**:
  - CommissionNode.NodeID != RequestCommissioningApproval.NodeID
  - OR CommissionNode.FabricID != RequestCommissioningApproval.FabricID
- **Description**: CommissionNode from different client/fabric

### State 11: CommissionNode_RequestID_Mismatch
- **Invariants**:
  - CommissionNode.RequestID not found in approved requests
- **Description**: CommissionNode with invalid/unknown RequestID

### State 12: CommissionNode_No_SUCCESS_Event
- **Invariants**:
  - No CommissioningRequestResult with StatusCode==SUCCESS for this RequestID
- **Description**: CommissionNode before approval granted

### State 13: CommissionNode_Already_Responded
- **Invariants**:
  - has_responded_with_window == true for this RequestID
  - No new approval received
- **Description**: Duplicate CommissionNode after already sent window

### State 14: Commissioning_Window_Pending
- **Invariants**:
  - approval_status == approved
  - commissioning_window_status == opening
  - timer_active == true (ResponseTimeoutSeconds)
- **Description**: Server preparing ReverseOpenCommissioningWindow

### State 15: Commissioning_Window_Opened
- **Invariants**:
  - commissioning_window_status == open
  - has_responded_with_window == true
  - ReverseOpenCommissioningWindow sent to client
- **Description**: Client should open commissioning window

### State 16: Client_Window_Validation
- **Invariants**:
  - Received ReverseOpenCommissioningWindow within timeout
  - timer_active == true
  - timer > 0
- **Description**: Client validating and opening window

### State 17: Client_Window_Timeout
- **Invariants**:
  - timer == 0 (ResponseTimeoutSeconds elapsed)
  - No ReverseOpenCommissioningWindow received
- **Description**: Client timed out waiting for response

### State 18: Device_VendorID_ProductID_Mismatch
- **Invariants**:
  - device.BasicInfo.VendorID != approval.VendorID
  - OR device.BasicInfo.ProductID != approval.ProductID
- **Description**: Actual device doesn't match approval

### State 19: Commissioning_Aborted
- **Invariants**:
  - VendorID/ProductID mismatch detected
  - Commissioning NOT completed
- **Description**: Server aborted commissioning due to mismatch

### State 20: Commissioning_Complete
- **Invariants**:
  - Device successfully commissioned
  - VendorID/ProductID verified
  - Device attestation validated
- **Description**: Final state, commissioning succeeded

## All Conditional Branches (from spec)

### Branch 1: RequestCommissioningApproval
```
IF session_type != CASE THEN
  FAIL with UNSUPPORTED_ACCESS
ELSE IF device_category NOT IN SupportedDeviceCategories THEN
  CLIENT SHALL NOT SEND (implicit pre-check)
ELSE IF (RequestID, ClientNodeID) matches pending request THEN
  SHOULD return FAILURE
ELSE
  Return SUCCESS + generate CommissioningRequestResult
```

### Branch 2: CommissioningRequestResult Event
```
IF user_approval_obtained (optional) THEN
  StatusCode := SUCCESS
ELSE IF user_timeout THEN
  StatusCode := TIMEOUT
ELSE
  StatusCode := FAILURE
```

### Branch 3: CommissionNode
```
IF session_type != CASE THEN
  FAIL with UNEXPECTED_ACCESS
ELSE IF CommissionNode.NodeID != Approval.NodeID OR CommissionNode.FabricID != Approval.FabricID THEN
  Return FAILURE
ELSE IF CommissionNode.RequestID not in approved_requests THEN
  Return FAILURE
ELSE IF NOT (CommissioningRequestResult.StatusCode == SUCCESS) THEN
  Return FAILURE
ELSE IF has_responded_with_window == true AND NOT new_approval THEN
  Return FAILURE
ELSE
  Send ReverseOpenCommissioningWindow
```

### Branch 4: ReverseOpenCommissioningWindow (Client side)
```
IF received_within_timeout THEN
  IF device.VendorID == approval.VendorID AND device.ProductID == approval.ProductID THEN
    Open commissioning window
  ELSE
    ERROR (wrong device)
ELSE
  Response invalid (timeout)
```

### Branch 5: Server Commissioning (during Device Attestation)
```
IF device.BasicInfo.VendorID == approval.VendorID AND device.BasicInfo.ProductID == approval.ProductID THEN
  Complete commissioning
ELSE
  SHALL NOT complete commissioning
  SHOULD indicate error to user
```

## Functions to Define

### F1: check_case_session
- **Parameters**: session_context
- **Returns**: boolean
- **Description**: Verify session is CASE authenticated

### F2: check_device_category_support
- **Parameters**: device_category, SupportedDeviceCategories
- **Returns**: boolean
- **Description**: Check if device category is in supported bitmap

### F3: check_duplicate_request
- **Parameters**: RequestID, ClientNodeID, pending_requests
- **Returns**: boolean
- **Description**: Check if RequestID+ClientNodeID already pending

### F4: store_approval_request
- **Parameters**: RequestID, ClientNodeID, VendorID, ProductID, Label, FabricID
- **Returns**: void
- **Description**: Store approval request details for later validation

### F5: generate_commissioning_request_result_event
- **Parameters**: RequestID, ClientNodeID, StatusCode
- **Returns**: void
- **Description**: Generate fabric-sensitive event with approval result

### F6: request_user_approval (optional)
- **Parameters**: Label, VendorID, ProductID
- **Returns**: approval_status (SUCCESS | TIMEOUT | FAILURE)
- **Description**: Optionally prompt user for approval

### F7: validate_commission_node_identity
- **Parameters**: CommissionNode.NodeID, CommissionNode.FabricID, Approval.NodeID, Approval.FabricID
- **Returns**: boolean
- **Description**: Verify CommissionNode from same client/fabric as approval

### F8: validate_commission_node_requestid
- **Parameters**: CommissionNode.RequestID, approved_requests
- **Returns**: boolean
- **Description**: Verify RequestID exists and is approved

### F9: check_approval_success
- **Parameters**: RequestID, event_history
- **Returns**: boolean
- **Description**: Check if CommissioningRequestResult with SUCCESS exists

### F10: check_already_responded
- **Parameters**: RequestID, response_history
- **Returns**: boolean
- **Description**: Check if ReverseOpenCommissioningWindow already sent

### F11: generate_reverse_open_commissioning_window
- **Parameters**: CommissioningTimeout, PAKEPasscodeVerifier, Discriminator, Iterations, Salt
- **Returns**: ReverseOpenCommissioningWindow_message
- **Description**: Create ReverseOpenCommissioningWindow command

### F12: validate_pake_parameters
- **Parameters**: Iterations, Salt
- **Returns**: boolean
- **Description**: Verify Iterations in [1000, 100000], Salt length in [16, 32]

### F13: validate_discriminator
- **Parameters**: Discriminator
- **Returns**: boolean
- **Description**: Verify Discriminator <= 4095

### F14: start_response_timer
- **Parameters**: ResponseTimeoutSeconds
- **Returns**: timer_handle
- **Description**: Start countdown timer for client response

### F15: check_timer_expired
- **Parameters**: timer_handle
- **Returns**: boolean
- **Description**: Check if timer reached 0

### F16: match_device_identity
- **Parameters**: device, VendorID, ProductID
- **Returns**: boolean
- **Description**: Check device VendorID/ProductID match

### F17: open_commissioning_window
- **Parameters**: device, PAKEPasscodeVerifier, Discriminator, Iterations, Salt, CommissioningTimeout
- **Returns**: void
- **Description**: Open commissioning window on target device

### F18: verify_device_attestation
- **Parameters**: device
- **Returns**: DAC_verification_result
- **Description**: Verify Device Attestation Certificate during commissioning

### F19: check_basic_info_match
- **Parameters**: device.BasicInfo.VendorID, device.BasicInfo.ProductID, approval.VendorID, approval.ProductID
- **Returns**: boolean
- **Description**: Verify Basic Information Cluster matches approval

### F20: abort_commissioning
- **Parameters**: reason
- **Returns**: void
- **Description**: Abort commissioning and cleanup

### F21: indicate_error_to_user
- **Parameters**: error_message
- **Returns**: void
- **Description**: Display error to user (SHOULD requirement)

### F22: complete_commissioning
- **Parameters**: device, fabric
- **Returns**: void
- **Description**: Finalize device commissioning onto fabric

## Cryptographic Operations

### C1: CASE Session Authentication
- **Algorithm**: CASE (Certificate Authenticated Session Establishment)
- **Inputs**: Client certificate, server certificate, session keys
- **Outputs**: Authenticated, encrypted session
- **Assumptions**: CASE protocol is secure, certificates valid

### C2: PAKE (Password Authenticated Key Exchange)
- **Algorithm**: SPAKE2+ or similar (Matter specification)
- **Inputs**: PAKEPasscodeVerifier, Discriminator, Iterations, Salt
- **Outputs**: Shared secret for commissioning
- **Assumptions**: PAKE implementation secure, passcode verifier properly generated

### C3: Device Attestation
- **Algorithm**: ECDSA signature verification
- **Inputs**: Device Attestation Certificate (DAC), device signature
- **Outputs**: Verified device identity (VendorID, ProductID)
- **Assumptions**: DAC issued by trusted authority, private key secure

## Security Properties

### SP1: CASE_Authentication_Required
- **Type**: access_control
- **States**: Idle -> CASE_Session_Validation_Failed | Approval_Request_Accepted
- **Description**: All commands must use CASE session

### SP2: Device_Category_Authorization
- **Type**: access_control
- **States**: Idle -> Device_Category_Check_Failed | Approval_Request_Accepted
- **Description**: Only supported device categories can be commissioned

### SP3: RequestID_Uniqueness
- **Type**: consistency
- **States**: Approval_Request_Accepted -> Duplicate_RequestID_Detected
- **Description**: Duplicate RequestID+ClientNodeID rejected while pending

### SP4: Identity_Binding
- **Type**: authenticity
- **States**: Validating_CommissionNode -> CommissionNode_NodeID_Mismatch
- **Description**: CommissionNode must be from same client as approval

### SP5: Approval_Required
- **Type**: access_control
- **States**: Validating_CommissionNode -> CommissionNode_No_SUCCESS_Event
- **Description**: Cannot commission without approved request

### SP6: Single_Use_Approval
- **Type**: consistency
- **States**: Validating_CommissionNode -> CommissionNode_Already_Responded
- **Description**: Each approval used once unless re-approved

### SP7: Timeout_Enforcement
- **Type**: timing
- **States**: Client_Window_Validation -> Client_Window_Timeout
- **Description**: Responses invalid after timeout

### SP8: Device_Identity_Verification
- **Type**: authenticity
- **States**: Device_VendorID_ProductID_Mismatch -> Commissioning_Aborted
- **Description**: Device identity must match approval

### SP9: Fabric_Isolation
- **Type**: confidentiality
- **States**: All states
- **Description**: Events fabric-sensitive, cross-fabric isolation maintained

### SP10: PAKE_Parameter_Security
- **Type**: cryptography
- **States**: Commissioning_Window_Pending -> Commissioning_Window_Opened
- **Description**: PAKE parameters within secure ranges

## Timing Requirements

1. **ResponseTimeoutSeconds**: 30-120 seconds (client waits for ReverseOpenCommissioningWindow)
2. **Approval validity**: Manufacturer-determined period (spec: clients SHOULD send CommissionNode immediately)
3. **Event generation**: Asynchronous after SUCCESS response

## All Triggers (Commands/Events)

1. RequestCommissioningApproval (client -> server)
2. CommissioningRequestResult (server -> client, event)
3. CommissionNode (client -> server)
4. ReverseOpenCommissioningWindow (server -> client)
5. timer_expiry (automatic)
6. user_approval_obtained (internal)
7. user_approval_timeout (internal)
8. device_attestation_complete (internal)
