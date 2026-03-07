# Property Violation Analysis - Detailed Traces

**Analysis Progress:** PROP_001 through PROP_010

---

## PROP_001: Commissioning_Mode_Access_Control

**Claim:** SELECT command SHALL only succeed when device is in commissioning mode.

**Formal:** ∀device. event receive_select(device) ∧ ¬in_commissioning_mode(device) ⟹ (ignore_command ∨ send_error(0x69, 0x85))

### FSM Trace

**Transitions Examined:**
1. `IDLE → COMMISSIONING_MODE_READY` - Trigger: enable_commissioning_mode
2. `COMMISSIONING_MODE_READY → SELECTED` - Trigger: SELECT_command, Guard: `commissioning_mode == true && aid == 0xA00000090989A77E401`
3. `IDLE → ERROR_NOT_IN_COMMISSIONING` - Trigger: SELECT_command, Guard: `commissioning_mode == false`
4. `IDLE → IDLE` - Trigger: SELECT_command, Guard: `commissioning_mode == false`, Action: ignore_command()

### Verdict: **HOLDS** ✅

**Reasoning:**
- Transition from IDLE to SELECTED requires commissioning_mode == true (via COMMISSIONING_MODE_READY intermediate state)
- When commissioning_mode == false, two paths exist:
  - Send error 0x6985 (ERROR_NOT_IN_COMMISSIONING)
  - Ignore command (stay in IDLE)
- Both behaviors satisfy the property requirement

### Specification Evidence

**Quote:** "When in commissioning mode, a commissionee SHALL answer to a correct SELECT command with a successful response APDU as shown in Table 45."  
**Source:** Section 4.21.4.1, "SELECT command", Page (line 235 in 4.21.md)

**Quote:** "When not in commissioning mode, a commissionee SHALL either ignore the command (no response) or answer with an error response APDU as shown in Table 46 indicating that conditions of use are not satisfied."  
**Source:** Section 4.21.4.1, "SELECT command", Page (line 273 in 4.21.md)

### Supporting FSM Evidence
```json
{
  "from_state": "COMMISSIONING_MODE_READY",
  "to_state": "SELECTED",
  "guard_condition": "commissioning_mode == true && aid == 0xA00000090989A77E401"
}
```

### Conclusion
Property HOLDS - FSM correctly enforces commissioning mode access control.

---

## PROP_002: AID_Authentication

**Claim:** Matter commissioning SHALL only be initiated with exact AID 'A0 00 00 09 09 8A 77 E4 01'.

**Formal:** ∀device, aid. event select_command(device, aid) ⟹ (aid = 0xA00000090989A77E401 ∨ reject_command)

### FSM Trace

**Transitions Examined:**
1. `COMMISSIONING_MODE_READY → SELECTED` - Guard includes: `aid == 0xA00000090989A77E401`
2. `COMMISSIONING_MODE_READY → ERROR_INVALID_AID` - Guard: `aid != 0xA00000090989A77E401`

### Verdict: **HOLDS** ✅

**Reasoning:**
- SELECT success transition requires exact AID match: `aid == 0xA00000090989A77E401`
- Wrong AID triggers ERROR_INVALID_AID with error code 0x6A82
- No path exists to SELECTED state with wrong AID

### Specification Evidence

**Quote:** "Matter commissioning SHALL be initiated by the NFC Reader/Writer by issuing the 7816-4 SELECT command with the Application Identifier (AID) 'A0 00 00 09 09 8A 77 E4 01' as shown in Table 44."  
**Source:** Section 4.21.4.1, "SELECT command", Page (line 206 in 4.21.md)

**Table 44 shows:**
- Data field: A0:00:00:09:09:8A:77:E4:01

### Supporting FSM Evidence
```json
{
  "from_state": "COMMISSIONING_MODE_READY",
  "to_state": "ERROR_INVALID_AID",
  "description": "SELECT command received with wrong Application Identifier",
  "error_code": "0x6A82"
}
```

### Conclusion
Property HOLDS - FSM enforces exact AID matching.

---

## PROP_003: Role_Asymmetry_Enforcement

**Claim:** Commissioner always initiates commands, Commissionee always responds; roles are immutable.

**Formal:** ∀session. (is_commissioner(node) ⟹ ∀msg. sends_first(node, msg)) ∧ (is_commissionee(node) ⟹ ∀msg. responds_only(node, msg))

### FSM Trace

**Analysis:** This property is about protocol-level behavior, not explicitly modeled in FSM states.

**FSM Evidence:**
- All command triggers (SELECT_command, TRANSPORT_command, GET_RESPONSE_command) are external inputs
- All responses are actions (send_response_apdu, send_error_response)
- No transition shows Commissionee initiating commands
- No transition shows Commissioner accepting commands

### Verdict: **HOLDS (by FSM design)** ✅

**Reasoning:**
- FSM models Commissionee device only
- All transitions triggered by received commands (external inputs from Commissioner)
- All actions are responses (send_response_apdu, send_error_response)
- Role asymmetry is implicit in FSM structure: triggers = commands from Commissioner, actions = responses from Commissionee

### Specification Evidence

**Quote:** "NTL provides a reliable, datagram-oriented, transport interface with asymmetric roles: one end always transmits first, and the other end always responds. When NTL is used for Matter commissioning, the Commissioner always transmits first and the Commissionee responds."  
**Source:** Section 4.21, intro paragraph (line 45-47 in 4.21.md)

**Quote:** "The commands (C-APDU) are always issued by the NFC Reader/Writer which is the Matter commissioner, and the responses (R-APDU) are always issued by the NFC Listener which is the Matter commissionee."  
**Source:** Section 4.21.4, "APDU layer", Page (line 193-195 in 4.21.md)

### Conclusion
Property HOLDS - FSM structure enforces role asymmetry by design.

---

## PROP_004: State_Transition_Ordering

**Claim:** TRANSPORT command can only be issued after successful SELECT command completion.

**Formal:** ∀session. event send_transport(session) ⟹ event before(select_success(session), send_transport(session))

### FSM Trace

**Transitions Examined:**
1. `IDLE → ERROR_INVALID_STATE` - Trigger: TRANSPORT_command, Guard: `session_state == IDLE`
2. `COMMISSIONING_MODE_READY → ERROR_INVALID_STATE` - Trigger: TRANSPORT_command, Guard: `session_state == IDLE`
3. `SELECTED → TRANSPORT_ACTIVE` - Trigger: TRANSPORT_command, Guard: `session_state == SELECTED`
4. `SELECTED → CHAINING_IN_PROGRESS_RECEIVING` - Trigger: TRANSPORT_command (chained)

### Verdict: **HOLDS** ✅

**Reasoning:**
- TRANSPORT commands from IDLE or COMMISSIONING_MODE_READY transition to ERROR_INVALID_STATE
- TRANSPORT commands only succeed from SELECTED state (or later active states)
- SELECTED state only reachable via successful SELECT command
- No path exists to execute TRANSPORT before SELECT

### Specification Evidence

**Quote:** "Once commissioning has been successfully initiated with the SELECT command, Matter messages SHALL be exchanged using the proprietary TRANSPORT command."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Page (line 296 in 4.21.md)

**Error transition evidence:**
```json
{
  "from_state": "IDLE",
  "to_state": "ERROR_INVALID_STATE",
  "trigger": "TRANSPORT_command",
  "actions": ["send_error_response(0x69, 0x85)", "error_reason := TRANSPORT_before_SELECT"]
}
```

### Conclusion
Property HOLDS - FSM enforces SELECT-before-TRANSPORT ordering.

---

## PROP_005: Protocol_Version_Binding

**Claim:** Commissioner SHALL use the NTL protocol version advertised by Commissionee in SELECT response.

**Formal:** ∀session, v_advertised, v_used. event select_response(session, v_advertised) ⟹ protocol_version(session) = v_advertised

### FSM Trace

**Analysis:** This property concerns Commissioner behavior, but FSM models Commissionee.

**FSM Evidence:**
- State COMMISSIONING_MODE_READY has invariant: `protocol_version == 0x01`
- Transition COMMISSIONING_MODE_READY → SELECTED sets: `protocol_version := 0x01`
- Function build_select_response() includes: `protocol_version` parameter (SHALL be 0x01)
- SELECT response advertises version 0x01

### Verdict: **PARTIALLY HOLDABLE (Commissionee side)** ⚠️

**Reasoning:**
- **Commissionee side HOLDS**: FSM correctly advertises version 0x01 in SELECT response
- **Commissioner side UNVERIFIABLE**: FSM doesn't model Commissioner behavior
- Property requires Commissioner to USE the advertised version, which is outside FSM scope
- FSM can only verify that Commissionee advertises correct version (0x01)

### Specification Evidence

**Quote:** "Version is a uint8 that SHALL encode the NTL protocol version supported by the commissionee. The version SHALL be 0x01. Other values SHALL be reserved for future use. The commissioner SHALL use the corresponding NTL protocol to communicate with the commissionee."  
**Source:** Section 4.21.4.1, "SELECT command", Table 45 description (line 266 in 4.21.md)

### Conclusion
Property HOLDS for Commissionee behavior (correct version advertisement).  
Commissioner compliance is out of scope for this FSM.

---

## PROP_006: Version_Value_Constraint

**Claim:** NTL protocol version in SELECT response SHALL be 0x01; other values are reserved.

**Formal:** ∀device. event send_select_response(device, version) ⟹ version = 0x01

### FSM Trace

**FSM Evidence:**
- State COMMISSIONING_MODE_READY invariant: `protocol_version == 0x01`
- Transition COMMISSIONING_MODE_READY → SELECTED action: `protocol_version := 0x01`
- Function build_select_response() parameter: `protocol_version` (SHALL be 0x01)
- Function description states: "Version field SHALL encode 0x01"

### Verdict: **HOLDS** ✅

**Reasoning:**
- protocol_version hardcoded to 0x01 in state invariant
- build_select_response() function documentation requires 0x01
- No transition or action sets protocol_version to any value other than 0x01

### Specification Evidence

**Quote:** "Version is a uint8 that SHALL encode the NTL protocol version supported by the commissionee. The version SHALL be 0x01."  
**Source:** Section 4.21.4.1, Table 45 description (line 266 in 4.21.md)

### Conclusion
Property HOLDS - FSM enforces version = 0x01 constraint.

---

## PROP_007: Vendor_Product_ID_Consistency

**Claim:** Device SHALL NOT set Vendor ID to 0 when providing non-zero Product ID.

**Formal:** ∀device, vid, pid. event advertise_ids(device, vid, pid) ⟹ (pid ≠ 0 ⟹ vid ≠ 0)

### FSM Trace

**FSM Evidence:**
- Function: build_select_response() includes vendor_id and product_id parameters
- Function description states: "Vendor ID and Product ID MAY both be 0 for privacy. If Product ID is non-zero, Vendor ID SHALL NOT be 0."

### Verdict: **HOLDS (by function specification)** ✅

**Reasoning:**
- build_select_response() function documentation explicitly states the constraint
- No FSM action violates this constraint
- Function is responsible for enforcing this rule in its implementation

### Specification Evidence

**Quote:** "Devices MAY choose not to advertise either the Vendor ID and Product ID, or only the Product ID due to privacy or other considerations. When choosing not to advertise both Vendor ID and Product ID, the device SHALL set both Vendor ID and Product ID fields to 0. When choosing not to advertise only the Product ID, the device SHALL set the Product ID field to 0. A device SHALL NOT set the Vendor ID to 0 when providing a non-zero Product ID."  
**Source:** Section 4.21.4.1, Table 45 description (line 270 in 4.21.md)

### Conclusion
Property HOLDS - Constraint documented in function specification.

---

## PROP_008: Chaining_Parameter_Consistency

**Claim:** P1 and P2 parameters SHALL have identical values across all chained TRANSPORT commands in same message.

**Formal:** ∀session, msg, fragments. is_chained(msg, fragments) ⟹ ∀f1, f2 ∈ fragments. P1P2(f1) = P1P2(f2)

### FSM Trace

**Transitions Examined:**
1. `CHAINING_IN_PROGRESS_RECEIVING → CHAINING_IN_PROGRESS_RECEIVING` (continue chaining)
   - Guard: `(P1 << 8 | P2) == P1P2_value`
   - Action: `check_consistency()`

2. `CHAINING_IN_PROGRESS_RECEIVING → ERROR_SEQUENCING` (P1/P2 mismatch)
   - Guard: `(P1 << 8 | P2) != P1P2_value`
   - Error: sequence_violation

### Verdict: **HOLDS** ✅

**Reasoning:**
- First chained fragment stores P1P2_value: `P1P2_value := (P1 << 8 | P2)`
- Subsequent fragments check: `(P1 << 8 | P2) == P1P2_value`
- Mismatch triggers ERROR_SEQUENCING transition
- No path exists to process fragments with inconsistent P1/P2

### Specification Evidence

**Quote:** "P1 and P2 SHALL encode the number of octets of the full message to transmit. It is encoded as a 2-bytes integer with P1 being the most significant byte. In case the full message fits in a single command, the value is equal to Lc. In case the message requires chaining, the value is bigger than Lc. The same value SHALL be used in all chained commands."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Table 47 description (line 324 in 4.21.md)

### Conclusion
Property HOLDS - FSM enforces P1/P2 consistency with explicit guard checks.

---

## PROP_009: Fragment_Reassembly_Atomicity

**Claim:** Chained message fragments must be completely reassembled before processing or entirely discarded on error.

**Formal:** ∀msg, fragments. reassemble(msg, fragments) ⟹ (all_received(fragments) ∧ process(msg)) ∨ discard(fragments)

### FSM Trace

**Transitions Examined:**
1. `CHAINING_IN_PROGRESS_RECEIVING → TRANSPORT_ACTIVE` (complete message received)
   - Guard: `fragments_received_length == message_total_length`
   - Actions: `complete_message := join_fragments()`, `process_and_generate_response(complete_message)`

2. `CHAINING_IN_PROGRESS_RECEIVING → ERROR_MEMORY_EXCEEDED` (discard on error)
   - Actions: `send_error_response`, `clear_fragment_buffer()`

3. `CHAINING_IN_PROGRESS_RECEIVING → ERROR_SEQUENCING` (discard on error)
   - Actions: `send_error_response`, `clear_fragment_buffer()`

4. `CHAINING_IN_PROGRESS_RECEIVING → SESSION_TIMEOUT` (discard on timeout)
   - Actions: `clear_fragment_buffer()`, `chaining_active := false`

### Verdict: **HOLDS** ✅

**Reasoning:**
- Complete message processed only when: `fragments_received_length == message_total_length`
- All error paths call `clear_fragment_buffer()` to discard partial fragments
- No transition processes incomplete fragments
- No path exists where partial fragments are preserved after error

### Specification Evidence

**Quote (implied):** The spec describes APDU chaining but doesn't explicitly state atomicity requirement. However, the chaining mechanism itself implies atomicity:
- Chained fragments accumulated until last fragment (CLA=0x80)
- Only complete message passed to higher layer
- Errors during chaining abort the entire message

**Source:** Section 4.21.4, "APDU layer", chaining descriptions (lines 200-202)

### Conclusion
Property HOLDS - FSM enforces atomic fragment reassembly: complete processing or complete discard.

---

## PROP_010: Memory_Bounds_Enforcement

**Claim:** Device SHALL reject chained messages exceeding maximum supported size with error 0x6A84.

**Formal:** ∀device, msg, max_size. msg_size(msg) > max_size(device) ⟹ event send_error(device, 0x6A, 0x84)

### FSM Trace

**Transitions Examined:**
1. `SELECTED → ERROR_MEMORY_EXCEEDED` 
   - Guard: `(P1 << 8 | P2) > max_supported_size || Lc > max_supported_size`
   - Action: `send_error_response(0x6A, 0x84)`

2. `TRANSPORT_ACTIVE → ERROR_MEMORY_EXCEEDED` (NEW)
   - Guard: `CLA == 0x90 && Lc > max_supported_size`
   - Action: `send_error_response(0x6A, 0x84)`

3. `CHAINING_IN_PROGRESS_RECEIVING → ERROR_MEMORY_EXCEEDED`
   - Guard: `fragments_received_length + Lc > max_supported_size`
   - Action: `send_error_response(0x6A, 0x84)`, `clear_fragment_buffer()`

### Verdict: **HOLDS** ✅

**Reasoning:**
- Three checkpoints for memory bounds:
  1. First fragment: check declared total length (P1<<8|P2)
  2. Chained start from active state: check Lc
  3. During chaining: check accumulated length
- All violations trigger ERROR_MEMORY_EXCEEDED with correct error code 0x6A84
- No path exists to process oversized messages

### Specification Evidence

**Quote:** "In case the chained message exceeds the maximum supported message size, an error response conforming to Table 50 SHALL be issued, indicating 'Not enough memory space'."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Page (line 366 in 4.21.md)

**Table 50:**
- SW1=0x6A, SW2=0x84 (Not enough memory space)

### Conclusion
Property HOLDS - FSM enforces memory bounds at multiple checkpoints with correct error code.

---

## Summary (PROP_001 through PROP_010)

| Property | Verdict | Critical Issue |
|----------|---------|----------------|
| PROP_001: Commissioning_Mode_Access_Control | ✅ HOLDS | None |
| PROP_002: AID_Authentication | ✅ HOLDS | None |
| PROP_003: Role_Asymmetry_Enforcement | ✅ HOLDS | None |
| PROP_004: State_Transition_Ordering | ✅ HOLDS | None |
| PROP_005: Protocol_Version_Binding | ⚠️ PARTIAL | Commissionee side only |
| PROP_006: Version_Value_Constraint | ✅ HOLDS | None |
| PROP_007: Vendor_Product_ID_Consistency | ✅ HOLDS | None |
| PROP_008: Chaining_Parameter_Consistency | ✅ HOLDS | None |
| PROP_009: Fragment_Reassembly_Atomicity | ✅ HOLDS | None |
| PROP_010: Memory_Bounds_Enforcement | ✅ HOLDS | None |

**Violations Found:** 0  
**Partial Coverage:** 1 (PROP_005 - Commissioner behavior out of FSM scope)

All CRITICAL properties in this batch HOLD in the FSM.

