# NTL Behavioral Analysis for FSM Extraction

## Section Overview
- **Section**: 4.21 NFC Transport Layer (NTL)
- **Purpose**: Transfer Matter commissioning messages over NFC interface
- **Protocol Stack**: Matter messages → ISO/IEC 7816-4 APDUs → ISO-DEP blocks → NFC-A frames

## Key Attributes/State Variables

### Device-Level Attributes
1. **commissioning_mode**: boolean (true when device ready for commissioning)
2. **device_role**: {Commissioner, Commissionee}
3. **nfc_mode**: {Poll_Mode (Commissioner), Listen_Mode (Commissionee)}
4. **protocol_version**: uint8 (SHALL be 0x01)
5. **vendor_id**: uint16
6. **product_id**: uint16
7. **discriminator**: 12-bit value
8. **extended_data**: optional bitstring

### Session-Level Attributes
1. **session_state**: {IDLE, SELECTED, TRANSPORT_ACTIVE, CHAINING_IN_PROGRESS, RESPONSE_INCOMPLETE, ERROR, TIMEOUT}
2. **aid**: bitstring (MUST be A0:00:00:09:09:8A:77:E4:01 for Matter)
3. **current_command**: {None, SELECT, TRANSPORT, GET_RESPONSE}

### APDU Processing Attributes
1. **chaining_active**: boolean
2. **fragment_buffer**: bitstring (accumulates fragments)
3. **message_total_length**: uint16 (encoded in P1/P2)
4. **fragments_received_length**: uint16
5. **response_buffer**: bitstring
6. **response_sent_length**: uint16
7. **response_remaining**: uint16

### APDU Field Values
1. **CLA**: uint8 (0x00 for SELECT/GET_RESPONSE; 0x80 unchained/0x90 chained for TRANSPORT)
2. **INS**: uint8 (0xA4=SELECT, 0x20=TRANSPORT, 0xC0=GET_RESPONSE)
3. **P1**: uint8 (high byte of message length for TRANSPORT)
4. **P2**: uint8 (low byte of message length for TRANSPORT)
5. **Lc**: uint8 (length of data field)
6. **Le**: uint8 (maximum response length)
7. **SW1**: uint8 (status word 1)
8. **SW2**: uint8 (status word 2)

### Frame Size Attributes
1. **FSD**: uint16 (max frame size Commissioner can receive, from RATS)
2. **FSC**: uint16 (max frame size Commissionee can receive, from ATS)

### Timer Attributes
1. **paftp_ack_timer**: integer (milliseconds, max 15000)
2. **paftp_idle_timer**: integer (milliseconds, max 30000)
3. **frame_waiting_time**: integer (ISO-DEP timing)

## Commands/Triggers

### External Commands (from Commissioner/Reader)
1. **SELECT_command**: Initiates commissioning with AID
2. **TRANSPORT_command**: Sends Matter message (possibly fragmented)
3. **GET_RESPONSE_command**: Requests next fragment of response

### Internal Events
1. **timer_expiry**: PAFTP ACK or idle timeout
2. **frame_waiting_timeout**: ISO-DEP waiting time exceeded
3. **message_complete**: All fragments received
4. **response_ready**: Matter layer generated response
5. **memory_exceeded**: Message size exceeds capacity

## Conditional Logic Branches

### SELECT Command Processing
```
IF commissioning_mode == true AND aid == matter_aid THEN
  → Send successful response (SW1=0x90, SW2=0x00) with Version/VID/PID
  → Transition to SELECTED state
ELSE IF commissioning_mode == false THEN
  → Either ignore (no response) OR send error (SW1=0x69, SW2=0x85)
  → Remain in IDLE
ELSE IF aid != matter_aid THEN
  → Send error response
  → Remain in IDLE
```

### TRANSPORT Command Processing
```
IF session_state != SELECTED AND session_state != TRANSPORT_ACTIVE THEN
  → Invalid state, send error
ELSE IF CLA == 0x90 (chained) THEN
  → Accumulate fragment to buffer
  → IF fragments_received_length + Lc > max_supported_size THEN
      → Send memory error (SW1=0x6A, SW2=0x84)
      → Transition to ERROR_MEMORY_EXCEEDED
  → ELSE IF fragments_received_length + Lc < message_total_length THEN
      → Send ACK response
      → Remain in CHAINING_IN_PROGRESS
  → ELSE (last fragment)
      → Reassemble message
      → Process Matter message
      → Transition to TRANSPORT_ACTIVE
ELSE IF CLA == 0x80 (unchained) THEN
  → Process complete message
  → Generate response
  → IF response_size <= Le THEN
      → Send complete response (SW1=0x90, SW2=0x00)
  → ELSE
      → Send incomplete response (SW1=0x61, SW2=remaining_bytes)
      → Transition to RESPONSE_INCOMPLETE
```

### GET_RESPONSE Command Processing
```
IF session_state == RESPONSE_INCOMPLETE THEN
  → IF response_remaining <= Le THEN
      → Send remaining data (SW1=0x90, SW2=0x00)
      → Transition to TRANSPORT_ACTIVE
  → ELSE
      → Send next fragment (SW1=0x61, SW2=new_remaining)
      → Remain in RESPONSE_INCOMPLETE
ELSE
  → Out of sequence error (SW1=0x69, SW2=0x85)
```

### P1/P2 Validation (Chaining Consistency)
```
IF chaining_active == true THEN
  FOREACH fragment in chain DO
    IF (P1 << 8 | P2) != message_total_length THEN
      → Protocol error, inconsistent length encoding
```

### Timeout Handling
```
IF paftp_idle_timer >= 30000 THEN
  → Close session
  → Transition to TIMEOUT

IF paftp_ack_timer >= 15000 THEN
  → Send standalone ACK
  → Reset timer
```

## States (Derived from Attribute Combinations)

### 1. IDLE
- **Invariants**: commissioning_mode == false, session_state == IDLE
- **Variables**: None active
- **Description**: No commissioning possible, ignores SELECT

### 2. COMMISSIONING_MODE_READY
- **Invariants**: commissioning_mode == true, session_state == IDLE, current_command == None
- **Variables**: protocol_version, vendor_id, product_id, discriminator
- **Description**: Ready to receive SELECT command

### 3. SELECTED
- **Invariants**: session_state == SELECTED, aid == matter_aid, protocol_version == 0x01
- **Variables**: aid, protocol_version, vendor_id, product_id
- **Description**: SELECT successful, waiting for first TRANSPORT

### 4. TRANSPORT_ACTIVE
- **Invariants**: session_state == TRANSPORT_ACTIVE, chaining_active == false
- **Variables**: None (between messages)
- **Description**: Matter messages being exchanged, no chaining in progress

### 5. CHAINING_IN_PROGRESS_RECEIVING
- **Invariants**: session_state == CHAINING_IN_PROGRESS, chaining_active == true, CLA == 0x90
- **Variables**: fragment_buffer, fragments_received_length, message_total_length, P1P2_value
- **Description**: Accumulating chained C-APDU fragments

### 6. MESSAGE_PROCESSING
- **Invariants**: All fragments received, reassembly complete
- **Variables**: complete_message
- **Description**: Matter layer processing message (internal, may be transient)

### 7. RESPONSE_INCOMPLETE
- **Invariants**: session_state == RESPONSE_INCOMPLETE, response_remaining > 0, last_SW1 == 0x61
- **Variables**: response_buffer, response_sent_length, response_remaining
- **Description**: Response too large for single R-APDU, awaiting GET_RESPONSE

### 8. ERROR_NOT_IN_COMMISSIONING
- **Invariants**: commissioning_mode == false, received SELECT
- **Variables**: error_code = 0x6985
- **Description**: SELECT received but device not in commissioning mode

### 9. ERROR_MEMORY_EXCEEDED
- **Invariants**: fragments_received_length + Lc > max_supported_size
- **Variables**: error_code = 0x6A84
- **Description**: Chained message exceeds device memory capacity

### 10. ERROR_SEQUENCING
- **Invariants**: GET_RESPONSE received without prior SW1=0x61
- **Variables**: error_code = 0x6985
- **Description**: Command received out of sequence

### 11. SESSION_TIMEOUT
- **Invariants**: paftp_idle_timer >= 30000
- **Variables**: timeout_reason
- **Description**: Session closed due to idle timeout

### 12. PROTOCOL_ACTIVATION
- **Invariants**: NFC activation sequence in progress (RATS/ATS exchange)
- **Variables**: FSD, FSC
- **Description**: ISO-DEP negotiating frame sizes (may be pre-IDLE)

## Transitions

### T1: Enter Commissioning Mode
- **From**: IDLE
- **To**: COMMISSIONING_MODE_READY
- **Trigger**: enable_commissioning_mode (user/higher layer action)
- **Guard**: commissioning_mode == false
- **Actions**: [commissioning_mode := true]

### T2: Exit Commissioning Mode
- **From**: COMMISSIONING_MODE_READY
- **To**: IDLE
- **Trigger**: disable_commissioning_mode
- **Guard**: commissioning_mode == true
- **Actions**: [commissioning_mode := false]

### T3: SELECT Success
- **From**: COMMISSIONING_MODE_READY
- **To**: SELECTED
- **Trigger**: SELECT_command
- **Guard**: commissioning_mode == true AND aid == 0xA00000090989A77E401 AND valid_select_params()
- **Actions**: [
  protocol_version := 0x01,
  send_response_apdu(SW1=0x90, SW2=0x00, data=build_select_response()),
  session_state := SELECTED,
  reset_idle_timer()
]

### T4: SELECT Error - Not in Commissioning Mode
- **From**: IDLE or COMMISSIONING_MODE_READY
- **To**: ERROR_NOT_IN_COMMISSIONING
- **Trigger**: SELECT_command
- **Guard**: commissioning_mode == false
- **Actions**: [send_error_response(SW1=0x69, SW2=0x85)] or [ignore_command()]

### T5: SELECT Error - Wrong AID
- **From**: COMMISSIONING_MODE_READY
- **To**: COMMISSIONING_MODE_READY (stay transition)
- **Trigger**: SELECT_command
- **Guard**: commissioning_mode == true AND aid != 0xA00000090989A77E401
- **Actions**: [send_error_response(SW1=0x6A, SW2=0x82)]

### T6: First TRANSPORT (Unchained)
- **From**: SELECTED
- **To**: TRANSPORT_ACTIVE
- **Trigger**: TRANSPORT_command
- **Guard**: session_state == SELECTED AND CLA == 0x80 AND (P1 << 8 | P2) == Lc AND valid_transport_params()
- **Actions**: [
  process_matter_message(data),
  response := generate_matter_response(),
  IF response_size <= Le THEN send_complete_response(SW1=0x90, SW2=0x00)
  ELSE send_incomplete_response(SW1=0x61, SW2=min(256, response_size - Le)),
  reset_idle_timer()
]
Note: This violates "no conditionals in actions" - needs splitting

### T6a: First TRANSPORT (Unchained, Response Fits)
- **From**: SELECTED
- **To**: TRANSPORT_ACTIVE
- **Trigger**: TRANSPORT_command
- **Guard**: session_state == SELECTED AND CLA == 0x80 AND (P1 << 8 | P2) == Lc AND valid_transport_params() AND response_size <= Le
- **Actions**: [
  process_matter_message(data),
  response := generate_matter_response(),
  send_complete_response(SW1=0x90, SW2=0x00, data=response),
  reset_idle_timer()
]

### T6b: First TRANSPORT (Unchained, Response Too Large)
- **From**: SELECTED
- **To**: RESPONSE_INCOMPLETE
- **Trigger**: TRANSPORT_command
- **Guard**: session_state == SELECTED AND CLA == 0x80 AND (P1 << 8 | P2) == Lc AND valid_transport_params() AND response_size > Le
- **Actions**: [
  process_matter_message(data),
  response_buffer := generate_matter_response(),
  fragment := extract_fragment(response_buffer, 0, Le),
  response_sent_length := Le,
  response_remaining := response_size - Le,
  send_incomplete_response(SW1=0x61, SW2=min(255, response_remaining), data=fragment),
  reset_idle_timer()
]

### T7: First TRANSPORT (Chained Start)
- **From**: SELECTED
- **To**: CHAINING_IN_PROGRESS_RECEIVING
- **Trigger**: TRANSPORT_command
- **Guard**: session_state == SELECTED AND CLA == 0x90 AND (P1 << 8 | P2) > Lc AND valid_transport_params()
- **Actions**: [
  fragment_buffer := data,
  fragments_received_length := Lc,
  message_total_length := (P1 << 8 | P2),
  P1P2_value := (P1 << 8 | P2),
  chaining_active := true,
  send_ack_response(),
  reset_idle_timer()
]

### T8: Continue Chaining (Not Last Fragment)
- **From**: CHAINING_IN_PROGRESS_RECEIVING
- **To**: CHAINING_IN_PROGRESS_RECEIVING (stay)
- **Trigger**: TRANSPORT_command
- **Guard**: chaining_active == true AND CLA == 0x90 AND (P1 << 8 | P2) == P1P2_value AND fragments_received_length + Lc < message_total_length AND fragments_received_length + Lc <= max_supported_size
- **Actions**: [
  append_fragment(fragment_buffer, data),
  fragments_received_length := fragments_received_length + Lc,
  send_ack_response(),
  reset_idle_timer()
]

### T9: Complete Chaining (Last Fragment, Response Fits)
- **From**: CHAINING_IN_PROGRESS_RECEIVING
- **To**: TRANSPORT_ACTIVE
- **Trigger**: TRANSPORT_command
- **Guard**: chaining_active == true AND CLA == 0x80 AND (P1 << 8 | P2) == P1P2_value AND fragments_received_length + Lc == message_total_length AND response_size <= Le
- **Actions**: [
  append_fragment(fragment_buffer, data),
  complete_message := fragment_buffer,
  process_matter_message(complete_message),
  response := generate_matter_response(),
  send_complete_response(SW1=0x90, SW2=0x00, data=response),
  clear_fragment_buffer(),
  chaining_active := false,
  reset_idle_timer()
]

### T10: Complete Chaining (Last Fragment, Response Too Large)
- **From**: CHAINING_IN_PROGRESS_RECEIVING
- **To**: RESPONSE_INCOMPLETE
- **Trigger**: TRANSPORT_command
- **Guard**: chaining_active == true AND CLA == 0x80 AND (P1 << 8 | P2) == P1P2_value AND fragments_received_length + Lc == message_total_length AND response_size > Le
- **Actions**: [
  append_fragment(fragment_buffer, data),
  complete_message := fragment_buffer,
  process_matter_message(complete_message),
  response_buffer := generate_matter_response(),
  fragment := extract_fragment(response_buffer, 0, Le),
  response_sent_length := Le,
  response_remaining := response_size - Le,
  send_incomplete_response(SW1=0x61, SW2=min(255, response_remaining), data=fragment),
  clear_fragment_buffer(),
  chaining_active := false,
  reset_idle_timer()
]

### T11: Memory Exceeded During Chaining
- **From**: CHAINING_IN_PROGRESS_RECEIVING
- **To**: ERROR_MEMORY_EXCEEDED
- **Trigger**: TRANSPORT_command
- **Guard**: chaining_active == true AND fragments_received_length + Lc > max_supported_size
- **Actions**: [
  send_error_response(SW1=0x6A, SW2=0x84),
  clear_fragment_buffer(),
  chaining_active := false
]

### T12: P1P2 Inconsistency During Chaining
- **From**: CHAINING_IN_PROGRESS_RECEIVING
- **To**: ERROR_SEQUENCING
- **Trigger**: TRANSPORT_command
- **Guard**: chaining_active == true AND (P1 << 8 | P2) != P1P2_value
- **Actions**: [
  send_error_response(SW1=0x69, SW2=0x85),
  clear_fragment_buffer(),
  chaining_active := false
]

### T13: GET_RESPONSE Continue (More Remaining)
- **From**: RESPONSE_INCOMPLETE
- **To**: RESPONSE_INCOMPLETE (stay)
- **Trigger**: GET_RESPONSE_command
- **Guard**: session_state == RESPONSE_INCOMPLETE AND response_remaining > Le
- **Actions**: [
  fragment := extract_fragment(response_buffer, response_sent_length, Le),
  response_sent_length := response_sent_length + Le,
  response_remaining := response_remaining - Le,
  send_incomplete_response(SW1=0x61, SW2=min(255, response_remaining), data=fragment),
  reset_idle_timer()
]

### T14: GET_RESPONSE Complete
- **From**: RESPONSE_INCOMPLETE
- **To**: TRANSPORT_ACTIVE
- **Trigger**: GET_RESPONSE_command
- **Guard**: session_state == RESPONSE_INCOMPLETE AND response_remaining <= Le
- **Actions**: [
  fragment := extract_fragment(response_buffer, response_sent_length, response_remaining),
  send_complete_response(SW1=0x90, SW2=0x00, data=fragment),
  clear_response_buffer(),
  response_sent_length := 0,
  response_remaining := 0,
  reset_idle_timer()
]

### T15: GET_RESPONSE Out of Sequence
- **From**: Any state except RESPONSE_INCOMPLETE
- **To**: ERROR_SEQUENCING
- **Trigger**: GET_RESPONSE_command
- **Guard**: session_state != RESPONSE_INCOMPLETE
- **Actions**: [send_error_response(SW1=0x69, SW2=0x85)]

### T16: Idle Timeout
- **From**: SELECTED, TRANSPORT_ACTIVE, CHAINING_IN_PROGRESS_RECEIVING, RESPONSE_INCOMPLETE
- **To**: SESSION_TIMEOUT
- **Trigger**: timer_tick (automatic)
- **Guard**: paftp_idle_timer >= 30000
- **Actions**: [
  close_session(),
  session_state := IDLE
]

### T17: Idle Timer Tick (No Timeout Yet)
- **From**: SELECTED, TRANSPORT_ACTIVE, CHAINING_IN_PROGRESS_RECEIVING, RESPONSE_INCOMPLETE
- **To**: Same state (stay)
- **Trigger**: timer_tick (automatic)
- **Guard**: paftp_idle_timer < 30000
- **Actions**: [paftp_idle_timer := paftp_idle_timer + timer_resolution]

### T18: Reset Idle Timer (Any Activity)
- Implicit in other transitions via reset_idle_timer() action

### T19: Protocol Activation (ISO-DEP)
- **From**: Pre-session (NFC physical activation)
- **To**: IDLE or COMMISSIONING_MODE_READY (depending on commissioning_mode)
- **Trigger**: NFC_activation_complete
- **Guard**: RATS/ATS exchange successful
- **Actions**: [
  FSD := extract_fsd_from_rats(),
  FSC := extract_fsc_from_ats(),
  initialize_iso_dep_layer()
]

### T20: Subsequent TRANSPORT in Active Session
- Similar to T6a/T6b but from TRANSPORT_ACTIVE instead of SELECTED
- Multiple variations for chained/unchained and response size

## Functions Required

### APDU Construction/Parsing Functions

#### build_select_response()
- **Parameters**: protocol_version, vendor_id, product_id, discriminator, extended_data (optional)
- **Returns**: bitstring (SELECT response data field)
- **Behavior**: Construct response per Table 45: Version (8 bits) + reserved 0x00 (8 bits) + reserved 0x0 (4 bits) + Discriminator (12 bits) + Vendor ID (16 bits) + Product ID (16 bits) + Extended Data (0+ bits)
- **Usage**: T3 (SELECT Success)

#### valid_select_params()
- **Parameters**: CLA, INS, P1, P2, Lc, Le, data
- **Returns**: boolean
- **Behavior**: Verify CLA=0x00, INS=0xA4, P1=0x04, P2=0x0C, Lc=0x09, Le=0x00, data=A0:00:00:09:09:8A:77:E4:01
- **Usage**: T3 (SELECT guard)

#### valid_transport_params()
- **Parameters**: CLA, INS, P1, P2, Lc, data
- **Returns**: boolean
- **Behavior**: Verify INS=0x20, CLA in {0x80, 0x90}, P1/P2 encode valid length, Lc matches data length
- **Usage**: T6a, T6b, T7 (TRANSPORT guards)

#### valid_get_response_params()
- **Parameters**: CLA, INS, P1, P2, Le
- **Returns**: boolean
- **Behavior**: Verify CLA=0x00, INS=0xC0, P1=0x00, P2=0x00
- **Usage**: T13, T14 (GET_RESPONSE guards)

### Response Sending Functions

#### send_response_apdu(SW1, SW2, data)
- **Parameters**: SW1 (uint8), SW2 (uint8), data (bitstring, optional)
- **Returns**: void
- **Behavior**: Construct R-APDU with optional data payload and status words, transmit via ISO-DEP layer
- **Usage**: T3, T6a, T6b, etc.

#### send_complete_response(SW1, SW2, data)
- **Parameters**: SW1 (uint8), SW2 (uint8), data (bitstring)
- **Returns**: void
- **Behavior**: Send R-APDU with SW1=0x90, SW2=0x00, indicating complete successful response
- **Usage**: T6a, T9, T14

#### send_incomplete_response(SW1, SW2, data)
- **Parameters**: SW1 (uint8), SW2 (uint8), data (bitstring fragment)
- **Returns**: void
- **Behavior**: Send R-APDU with SW1=0x61, SW2=remaining_bytes_count, indicating more data available
- **Usage**: T6b, T10, T13

#### send_error_response(SW1, SW2)
- **Parameters**: SW1 (uint8), SW2 (uint8)
- **Returns**: void
- **Behavior**: Send R-APDU with error status code, no data payload
- **Usage**: T4, T5, T11, T12, T15

#### send_ack_response()
- **Parameters**: None
- **Returns**: void
- **Behavior**: Send R-APDU acknowledging fragment receipt during chaining (intermediate response)
- **Usage**: T7, T8

### Fragment Handling Functions

#### append_fragment(buffer, fragment)
- **Parameters**: buffer (bitstring), fragment (bitstring)
- **Returns**: bitstring (updated buffer)
- **Behavior**: Concatenate fragment to end of buffer, check for buffer overflow
- **Usage**: T8, T9, T10

#### extract_fragment(buffer, offset, length)
- **Parameters**: buffer (bitstring), offset (uint16), length (uint16)
- **Returns**: bitstring (fragment)
- **Behavior**: Extract substring from buffer starting at offset with specified length
- **Usage**: T6b, T10, T13, T14

#### clear_fragment_buffer()
- **Parameters**: None
- **Returns**: void
- **Behavior**: Reset fragment_buffer to empty, set fragments_received_length to 0
- **Usage**: T9, T10, T11, T12

#### clear_response_buffer()
- **Parameters**: None
- **Returns**: void
- **Behavior**: Reset response_buffer, response_sent_length, response_remaining
- **Usage**: T14

### Matter Message Processing Functions

#### process_matter_message(message)
- **Parameters**: message (bitstring)
- **Returns**: void
- **Behavior**: Pass complete Matter message to higher protocol layer for processing
- **Algorithm**: Decode message, route to appropriate handler, may involve cryptographic verification
- **Usage**: T6a, T6b, T9, T10

#### generate_matter_response()
- **Parameters**: None (uses context from processed message)
- **Returns**: bitstring (Matter response message)
- **Behavior**: Higher protocol layer generates response to received Matter message
- **Algorithm**: Construct response per Matter specification, may involve cryptographic signing
- **Usage**: T6a, T6b, T9, T10

### Timer Functions

#### reset_idle_timer()
- **Parameters**: None
- **Returns**: void
- **Behavior**: Set paftp_idle_timer := 0
- **Usage**: T3, T6a, T6b, T7, T8, T9, T10, T13, T14

#### timer_tick()
- **Parameters**: None (automatic/periodic)
- **Returns**: void
- **Behavior**: Increment paftp_idle_timer by timer_resolution (e.g., 100ms)
- **Usage**: T16, T17

### Session Management Functions

#### close_session()
- **Parameters**: None
- **Returns**: void
- **Behavior**: Clean up session state, release resources, transition to IDLE
- **Usage**: T16

#### ignore_command()
- **Parameters**: None
- **Returns**: void
- **Behavior**: Discard received command without response (valid when not in commissioning mode)
- **Usage**: T4

### ISO-DEP Layer Functions

#### initialize_iso_dep_layer()
- **Parameters**: FSD (uint16), FSC (uint16)
- **Returns**: void
- **Behavior**: Configure ISO-DEP with negotiated frame sizes, set up chaining parameters
- **Usage**: T19

#### extract_fsd_from_rats()
- **Parameters**: RATS frame (bitstring)
- **Returns**: uint16 (FSD value)
- **Behavior**: Parse RATS frame, extract Frame Size Device value
- **Usage**: T19

#### extract_fsc_from_ats()
- **Parameters**: ATS frame (bitstring)
- **Returns**: uint16 (FSC value)
- **Behavior**: Parse ATS frame, extract Frame Size Card value
- **Usage**: T19

## Cryptographic Operations
None directly in NTL layer. Cryptography is handled by higher Matter protocol layers. NTL only transports encrypted messages.

## Security Properties

### SP1: Commissioning Mode Access Control
- **Type**: Access Control
- **Description**: SELECT command only succeeds when device is in commissioning mode and AID matches Matter
- **States**: IDLE, COMMISSIONING_MODE_READY, SELECTED
- **Transitions**: T3, T4

### SP2: AID Authentication
- **Type**: Authentication
- **Description**: Only Matter AID (A0:00:00:09:09:8A:77:E4:01) can initiate commissioning
- **States**: COMMISSIONING_MODE_READY
- **Transitions**: T3, T5

### SP3: State Transition Ordering
- **Type**: Correctness
- **Description**: TRANSPORT can only occur after successful SELECT
- **States**: SELECTED, TRANSPORT_ACTIVE
- **Transitions**: T6a, T6b, T7

### SP4: Protocol Version Binding
- **Type**: Security
- **Description**: Protocol version negotiated in SELECT must be used for session
- **States**: SELECTED (protocol_version fixed at 0x01)
- **Transitions**: T3

### SP5: Chaining Consistency
- **Type**: Consistency
- **Description**: P1/P2 values must remain constant across all fragments in chain
- **States**: CHAINING_IN_PROGRESS_RECEIVING
- **Transitions**: T7, T8, T9, T10, T12

### SP6: Fragment Reassembly Atomicity
- **Type**: Atomicity
- **Description**: Fragments must be completely reassembled before processing or entirely discarded on error
- **States**: CHAINING_IN_PROGRESS_RECEIVING, MESSAGE_PROCESSING
- **Transitions**: T9, T10, T11

### SP7: Memory Bounds Enforcement
- **Type**: Security
- **Description**: Device SHALL reject messages exceeding max_supported_size with error 0x6A84
- **States**: CHAINING_IN_PROGRESS_RECEIVING, ERROR_MEMORY_EXCEEDED
- **Transitions**: T11

### SP8: GET_RESPONSE Sequencing
- **Type**: Correctness
- **Description**: GET_RESPONSE only valid immediately after incomplete response (SW1=0x61)
- **States**: RESPONSE_INCOMPLETE
- **Transitions**: T13, T14, T15

### SP9: Role Asymmetry
- **Type**: Access Control
- **Description**: Commissioner always initiates commands, Commissionee always responds
- **States**: All states
- **Transitions**: All transitions (enforced by roles)

### SP10: Idle Timeout Enforcement
- **Type**: Timing
- **Description**: Session MUST close after 30s with no unique data
- **States**: SESSION_TIMEOUT
- **Transitions**: T16

## Security Assumptions

### AS1: ISO-DEP Reliability
- **Statement**: ISO-DEP provides reliable frame delivery with retransmission and error detection
- **Type**: Explicit (spec states "making it a reliable transport protocol")
- **If Violated**: Frame loss or corruption could propagate to APDU layer, breaking message integrity

### AS2: Physical Proximity
- **Statement**: NFC ~10cm range provides physical proximity authentication
- **Type**: Implicit
- **If Violated**: Long-range NFC or relay attacks break proximity assumption, enabling remote MitM

### AS3: Higher Layer Cryptography
- **Statement**: Matter protocol layers above NTL provide authentication, confidentiality, integrity
- **Type**: Implicit
- **If Violated**: NTL has NO cryptographic protection; all security depends on higher layers

### AS4: Single Session
- **Statement**: Only one NTL session active at a time per device
- **Type**: Implicit
- **If Violated**: Concurrent sessions could cause state confusion, fragment buffer corruption

### AS5: Commissioning Mode Control
- **Statement**: commissioning_mode is reliably controlled by user or higher layers
- **Type**: Implicit
- **If Violated**: Unintended commissioning mode activation enables unauthorized commissioning

### AS6: Memory Availability
- **Statement**: Device has sufficient memory for max_supported_size or enforces limit correctly
- **Type**: Implicit
- **If Violated**: Memory exhaustion could crash device or overflow buffers

### AS7: Timer Accuracy
- **Statement**: Timers are accurate enough for 15s and 30s timeout enforcement
- **Type**: Implicit
- **If Violated**: Clock drift could cause premature session closure (DoS) or timeout bypass

### AS8: NFC Forum Compliance
- **Statement**: Implementations comply with NFC Forum specifications for Type 4A operation
- **Type**: Explicit (spec has SHALL requirements)
- **If Violated**: RF parameter mismatches, timing violations, interoperability failures

## Additional Notes

### Optimization Recommendations (SHOULD clauses)
- Lc SHOULD be <= min(255, FSC-10) for ISO-DEP optimization
- Le SHOULD be = min(256, FSD-6) for ISO-DEP optimization
These are not security-critical but affect performance. Model as preferences, not guards.

### Privacy Considerations
- VID/PID MAY be suppressed (set to 0) for privacy
- Not security-critical but affects device trackability
- Model as optional parameter in build_select_response()

### Error Handling Not Fully Specified
- Spec says "commissionee MAY answer with another error response" for other error cases
- Leaves implementation flexibility
- Model generic ERROR state for unspecified errors

### ISO-DEP Layer Abstraction
- Spec provides informational diagrams of ISO-DEP chaining and WTX
- These are handled by ISO-DEP layer, not directly by FSM
- Model at APDU level, assume ISO-DEP layer handles lower details

### Frame Size Negotiation
- FSD/FSC negotiated during protocol activation (RATS/ATS)
- Used to optimize APDU chaining parameters
- Model as initialization step before main FSM

### PAFTP Timeouts
- Mentioned at beginning but seem unrelated to NTL proper
- May be from different protocol section
- Include for completeness but may not integrate into NTL FSM
