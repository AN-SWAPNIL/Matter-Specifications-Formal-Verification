# Property Violation Analysis - PROP_021 through PROP_030

**Analysis Progress:** PROP_021 through PROP_030

---

## PROP_021: P1_P2_Message_Length_Encoding

**Claim:** P1 and P2 SHALL correctly encode total message length as 2-byte big-endian integer.

**Formal:** ∀msg, p1, p2. encode_length(msg, p1, p2) ⟹ (p1 << 8 | p2) = total_length(msg)

### FSM Trace

**FSM Evidence:**
- All transitions using P1 and P2 compute: `(P1 << 8 | P2)`
- This value compared against actual message length
- Guards check: `(P1 << 8 | P2) == message_total_length`
- Function valid_transport_params() validates P1/P2 encoding

### Verdict: **HOLDS** ✅

**Reasoning:**
- FSM correctly interprets P1/P2 as big-endian 16-bit value
- All transitions compute `(P1 << 8 | P2)` for length
- Inconsistencies detected by guard conditions
- Property enforced by length validation

### Specification Evidence

**Quote:** "P1 and P2 SHALL encode the number of octets of the full message to transmit. It is encoded as a 2-bytes integer with P1 being the most significant byte."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Table 47 description (line 324 in 4.21.md)

### Conclusion
Property HOLDS - FSM correctly interprets P1/P2 as big-endian 16-bit length.

---

## PROP_022: Le_Field_Correct_Encoding

**Claim:** Le field SHALL correctly encode maximum response length Commissioner can receive.

**Formal:** ∀cmd, max_recv. Le_field(cmd) = max_receive_length(commissioner)

### FSM Trace

**FSM Evidence:**
- Le field used in response size calculations
- Guards check: `response_size > Le` to determine if response incomplete
- Actions: `extract_fragment(response_buffer, 0, Le)` uses Le for fragmentation
- Function description: "Le = max response length"

### Verdict: **HOLDS (assumed correct from Commissioner)** ✅

**Reasoning:**
- FSM uses Le value to fragment responses appropriately
- If Le incorrect from Commissioner, FSM still honors it (conservative)
- FSM doesn't generate Le (Commissioner does), only respects it
- Property concerns Commissioner correctness, FSM respects whatever Le provided

### Specification Evidence

**Quote:** "The Le single-octet field SHALL encode the maximum length in octets that the reader/writer can receive in the response APDU in compliance with ISO/IEC 7816-4."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Table 47 description (line 326 in 4.21.md)

### Conclusion
Property HOLDS - FSM correctly uses Le provided by Commissioner.

---

## PROP_023: Data_Field_Fragment_Containment

**Claim:** Data field SHALL contain valid message fragment (possibly complete message).

**Formal:** ∀cmd, data. data_field(cmd) = data ⟹ is_valid_fragment(data) ∨ is_complete_message(data)

### FSM Trace

**FSM Evidence:**
- Data field processed by higher layer function: `process_and_generate_response()`
- FSM treats data as opaque bitstring (no validation of fragment structure)
- Validation assumed to be in higher layer (Matter protocol)

### Verdict: **UNVERIFIABLE (opaque data)** ⚪

**Reasoning:**
- FSM treats Matter message data as opaque bitstring
- No fragment validation at NTL layer
- Property requires higher-layer validation (Matter protocol parser)
- FSM cannot determine if fragment is "valid" - passes to higher layer

### Specification Evidence

**Quote:** "The Data field SHALL contain a fragment of the message to transmit, possibly the only one."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Table 47 description (line 325 in 4.21.md)

### Conclusion
Property UNVERIFIABLE in FSM - Data validation is higher-layer responsibility.

---

## PROP_024: Success_Status_Code_Correctness

**Claim:** Complete successful response SHALL use status codes SW1=0x90, SW2=0x00.

**Formal:** ∀response. is_complete(response) ∧ is_success(response) ⟹ SW1(response) = 0x90 ∧ SW2(response) = 0x00

### FSM Trace

**Transitions Examined:**
1. `TRANSPORT_ACTIVE → TRANSPORT_ACTIVE` (complete response)
   - Action: `send_complete_response(0x90, 0x00, response)`

2. `RESPONSE_INCOMPLETE → TRANSPORT_ACTIVE` (final GET_RESPONSE)
   - Action: `send_complete_response(0x90, 0x00, fragment)`

3. `CHAINING_IN_PROGRESS_RECEIVING → TRANSPORT_ACTIVE` (complete chained message)
   - Action: `send_complete_response(0x90, 0x00, response)`

### Verdict: **HOLDS** ✅

**Reasoning:**
- All complete success responses use: `send_complete_response(0x90, 0x00, ...)`
- Function send_complete_response() first two parameters are SW1, SW2
- All call sites use 0x90, 0x00 for success
- No path sends complete response with different status codes

### Specification Evidence

**Quote:** "In case the full message fits within the number of bytes encoded by Le in C-APDU, a successful response SHALL be indicated by the SW1 and SW2 values in Table 48."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Page (line 328 in 4.21.md)

**Table 48:** SW1=0x90, SW2=0x00 (Complete success)

### Conclusion
Property HOLDS - FSM uses correct status codes for complete success.

---

## PROP_025: Incomplete_Status_Code_Correctness

**Claim:** Incomplete response SHALL use SW1=0x61 and SW2 SHALL encode remaining bytes.

**Formal:** ∀response, remaining. is_incomplete(response) ⟹ SW1(response) = 0x61 ∧ SW2(response) = remaining_bytes(response)

### FSM Trace

**Transitions Examined:**
1. `TRANSPORT_ACTIVE → RESPONSE_INCOMPLETE`
   - Action: `send_incomplete_response(0x61, min(255, size(response_buffer) - Le), fragment)`

2. `RESPONSE_INCOMPLETE → RESPONSE_INCOMPLETE` (continued GET_RESPONSE)
   - Action: `send_incomplete_response(0x61, min(255, response_remaining - Le), fragment)`

### Verdict: **HOLDS** ✅

**Reasoning:**
- All incomplete responses use: `send_incomplete_response(0x61, remaining_bytes, ...)`
- SW1 = 0x61 (first parameter)
- SW2 = min(255, remaining_bytes) (second parameter)
- Correctly encodes remaining bytes in SW2

### Specification Evidence

**Quote:** "In case the full message does not fit within the number of bytes encoded by Le in C-APDU, a successful but incomplete response SHALL be indicated by the SW1 value in Table 49, and SW2 SHALL encode the number of bytes of message to be sent in the next GET RESPONSE R-APDU."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Page (line 347 in 4.21.md)

**Table 49:** SW1=0x61, SW2=remaining bytes

### Conclusion
Property HOLDS - FSM correctly encodes incomplete response status.

---

## PROP_026: Memory_Error_Code_Correctness

**Claim:** Memory exceeded error SHALL use status codes SW1=0x6A, SW2=0x84.

**Formal:** ∀device, msg. exceeds_memory(device, msg) ⟹ error_code(device) = 0x6A84

### FSM Trace

**Transitions Examined:**
1. `SELECTED → ERROR_MEMORY_EXCEEDED`
   - Action: `send_error_response(0x6A, 0x84)`

2. `TRANSPORT_ACTIVE → ERROR_MEMORY_EXCEEDED`
   - Action: `send_error_response(0x6A, 0x84)`

3. `CHAINING_IN_PROGRESS_RECEIVING → ERROR_MEMORY_EXCEEDED`
   - Action: `send_error_response(0x6A, 0x84)`

### Verdict: **HOLDS** ✅

**Reasoning:**
- All memory exceeded transitions use: `send_error_response(0x6A, 0x84)`
- Correct error code for "Not enough memory space"
- Consistent across all states

### Specification Evidence

**Quote:** "In case the chained message exceeds the maximum supported message size, an error response conforming to Table 50 SHALL be issued, indicating 'Not enough memory space'."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Page (line 366 in 4.21.md)

**Table 50:** SW1=0x6A, SW2=0x84

### Conclusion
Property HOLDS - Correct error code for memory exhaustion.

---

## PROP_027: Condition_Not_Satisfied_Error

**Claim:** Out-of-sequence GET RESPONSE SHALL return error SW1=0x69, SW2=0x85.

**Formal:** ∀session. event receive_get_response(session) ∧ ¬has_incomplete_response(session) ⟹ error_code(session) = 0x6985

### FSM Trace

**Transitions Examined:**
1. `SELECTED → ERROR_SEQUENCING` (GET_RESPONSE out of sequence)
   - Action: `send_error_response(0x69, 0x85)`

2. `TRANSPORT_ACTIVE → ERROR_SEQUENCING` (GET_RESPONSE out of sequence)
   - Action: `send_error_response(0x69, 0x85)`

3. `CHAINING_IN_PROGRESS_RECEIVING → ERROR_SEQUENCING`
   - Action: `send_error_response(0x69, 0x85)`

4. `IDLE → ERROR_INVALID_STATE` (GET_RESPONSE before session)
   - Action: `send_error_response(0x69, 0x85)`

5. `COMMISSIONING_MODE_READY → ERROR_INVALID_STATE`
   - Action: `send_error_response(0x69, 0x85)`

### Verdict: **HOLDS** ✅

**Reasoning:**
- All out-of-sequence GET_RESPONSE transitions use: `send_error_response(0x69, 0x85)`
- Correct error code for "Conditions of use not satisfied"
- Consistent error handling

### Specification Evidence

**Quote:** "In case GET RESPONSE is received, but not following a TRANSPORT successful Response APDU - Incomplete message, the commissionee SHALL answer with an error indicating the condition of use is not satisfied, as shown in Table 54"  
**Source:** Section 4.21.4.3, "GET RESPONSE command", Page (line 446 in 4.21.md)

**Table 54:** SW1=0x69, SW2=0x85

### Conclusion
Property HOLDS - Correct error code for sequencing violations.

---

## PROP_028: Commissioning_Mode_Error_Response

**Claim:** When not in commissioning mode, SELECT SHALL be ignored or return error 0x6985.

**Formal:** ∀device. event receive_select(device) ∧ ¬in_commissioning_mode(device) ⟹ (no_response(device) ∨ error_code(device) = 0x6985)

### FSM Trace

**Transitions Examined:**
1. `IDLE → ERROR_NOT_IN_COMMISSIONING`
   - Guard: `commissioning_mode == false`
   - Action: `send_error_response(0x69, 0x85)`

2. `IDLE → IDLE`
   - Guard: `commissioning_mode == false`
   - Action: `ignore_command()`

### Verdict: **HOLDS** ✅

**Reasoning:**
- Same as PROP_001 verification
- Two valid behaviors when not in commissioning mode:
  1. Send error 0x6985
  2. Ignore command (no response)
- Both satisfy specification requirement

### Specification Evidence

**Quote:** "When not in commissioning mode, a commissionee SHALL either ignore the command (no response) or answer with an error response APDU as shown in Table 46 indicating that conditions of use are not satisfied."  
**Source:** Section 4.21.4.1, "SELECT command", Page (line 273 in 4.21.md)

**Table 46:** SW1=0x69, SW2=0x85

### Conclusion
Property HOLDS - Correct handling when not in commissioning mode.

---

## PROP_029: Fragment_Order_Preservation

**Claim:** Chained fragments must be processed in transmission order for correct message reassembly.

**Formal:** ∀msg, fragments. reassemble(msg, fragments) ⟹ ∀i < j. process_order(fragment[i]) < process_order(fragment[j])

### FSM Trace

**FSM Evidence:**
- Function: `append_fragment(fragment_buffer, data)` - appends in order received
- Function: `join_fragments(fragment_buffer)` - joins in buffer order
- State variable: `fragments_received_length` - increments monotonically
- No reordering mechanism in FSM

### Verdict: **HOLDS** ✅

**Reasoning:**
- Fragments appended to buffer in order received
- Fragment buffer is linear (append-only during chaining)
- join_fragments() processes buffer sequentially
- No transitions reorder fragments
- Order preservation implicit in append/join semantics

### Specification Evidence

**Quote (implied):** Specification describes chaining but doesn't explicitly forbid reordering. However, ISO/IEC 7816-4 APDU chaining assumes sequential processing.

**Chaining description:** Section 4.21.4, "APDU layer", discusses fragment sequence in figures 38 and 39

### Conclusion
Property HOLDS - FSM preserves fragment order through sequential append/join.

---

## PROP_030: No_Replay_Protection_Awareness

**Claim:** NTL provides no inherent replay protection; must be provided by higher layers.

**Formal:** ∀msg. ¬provides_replay_protection(NTL, msg) ⟹ requires_protection(higher_layer, msg)

### FSM Trace

**FSM Evidence:**
- No nonce, timestamp, or sequence number in FSM state variables
- No replay detection mechanism in transitions
- Assumption ASSUM_003: "Higher protocol layers provide cryptographic authentication, confidentiality, and replay protection"
- Definition: "Matter Message" treated as opaque bitstring

### Verdict: **HOLDS (documented limitation)** ✅

**Reasoning:**
- FSM provides NO replay protection mechanisms
- No state to detect replayed messages
- Property is awareness/documentation requirement, not behavior requirement
- Documented in assumptions that higher layers must provide replay protection

### Specification Evidence

**Quote:** "NTL is a transport layer only; does not inspect, validate, or process Matter message contents."  
**Source:** ntl_fsm_model.json, definitions section (Matter Message definition)

**Note:** Specification doesn't explicitly state "no replay protection" but describes NTL as transport-only with no cryptographic functions.

### Conclusion
Property HOLDS - FSM correctly documents no replay protection, higher layers responsible.

---

## Summary (PROP_021 through PROP_030)

| Property | Verdict | Notes |
|----------|---------|-------|
| PROP_021: P1_P2_Message_Length_Encoding | ✅ HOLDS | Correct big-endian interpretation |
| PROP_022: Le_Field_Correct_Encoding | ✅ HOLDS | FSM respects Commissioner's Le |
| PROP_023: Data_Field_Fragment_Containment | ⚪ UNVERIFIABLE | Opaque data, higher-layer validation |
| PROP_024: Success_Status_Code_Correctness | ✅ HOLDS | 0x90/0x00 for all complete success |
| PROP_025: Incomplete_Status_Code_Correctness | ✅ HOLDS | 0x61 + remaining bytes |
| PROP_026: Memory_Error_Code_Correctness | ✅ HOLDS | 0x6A/0x84 for memory exceeded |
| PROP_027: Condition_Not_Satisfied_Error | ✅ HOLDS | 0x69/0x85 for sequencing errors |
| PROP_028: Commissioning_Mode_Error_Response | ✅ HOLDS | Error or ignore when not commissioned |
| PROP_029: Fragment_Order_Preservation | ✅ HOLDS | Sequential append/join preserves order |
| PROP_030: No_Replay_Protection_Awareness | ✅ HOLDS | Documented limitation |

**Violations Found:** 0  
**Unverifiable:** 1 (PROP_023 - opaque data)

All verifiable properties in this batch HOLD in the FSM.

