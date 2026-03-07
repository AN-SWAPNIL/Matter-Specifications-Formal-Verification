# Property Violation Analysis - PROP_011 through PROP_020

**Analysis Progress:** PROP_011 through PROP_020

---

## PROP_011: GET_RESPONSE_Sequencing

**Claim:** GET RESPONSE command SHALL only be accepted immediately after receiving incomplete response (SW1=0x61).

**Formal:** ∀session. event receive_get_response(session) ⟹ event immediately_after(incomplete_response(session, 0x61), receive_get_response(session))

### FSM Trace

**Transitions Examined:**
1. `RESPONSE_INCOMPLETE → RESPONSE_INCOMPLETE` - GET_RESPONSE with more data remaining
   - Guard: `session_state == RESPONSE_INCOMPLETE && response_remaining > Le`
   - Valid continuation of incomplete response

2. `RESPONSE_INCOMPLETE → TRANSPORT_ACTIVE` - GET_RESPONSE completing response
   - Guard: `session_state == RESPONSE_INCOMPLETE && response_remaining <= Le`
   - Valid completion

3. `SELECTED → ERROR_SEQUENCING` - GET_RESPONSE without incomplete response
   - Guard: `session_state == SELECTED`
   - Error: out of sequence

4. `TRANSPORT_ACTIVE → ERROR_SEQUENCING` - GET_RESPONSE without incomplete response
   - Guard: `session_state == TRANSPORT_ACTIVE`
   - Error: out of sequence

5. `CHAINING_IN_PROGRESS_RECEIVING → ERROR_SEQUENCING` - GET_RESPONSE during chaining
   - Guard: `session_state == CHAINING_IN_PROGRESS`
   - Error: out of sequence

6. `IDLE → ERROR_INVALID_STATE` - GET_RESPONSE before session
   - Guard: `session_state == IDLE`

7. `COMMISSIONING_MODE_READY → ERROR_INVALID_STATE` - GET_RESPONSE before session
   - Guard: `session_state == IDLE`

### Verdict: **HOLDS** ✅

**Reasoning:**
- GET_RESPONSE only succeeds from RESPONSE_INCOMPLETE state
- RESPONSE_INCOMPLETE only reachable after sending SW1=0x61 response
- All other states reject GET_RESPONSE with error codes
- No path exists to accept GET_RESPONSE without prior incomplete response

### Specification Evidence

**Quote:** "This command SHALL be issued following the reception of an incomplete successful R-APDU, in compliance with ISO/IEC 7816-4."  
**Source:** Section 4.21.4.3, "GET RESPONSE command", Table 51 intro (line 385 in 4.21.md)

**Quote:** "In case GET RESPONSE is received, but not following a TRANSPORT successful Response APDU - Incomplete message, the commissionee SHALL answer with an error indicating the condition of use is not satisfied, as shown in Table 54"  
**Source:** Section 4.21.4.3, "GET RESPONSE command", error case (line 446 in 4.21.md)

**Table 54:** SW1=0x69, SW2=0x85 (Condition of use not satisfied)

### Conclusion
Property HOLDS - FSM enforces strict GET_RESPONSE sequencing.

---

## PROP_012: Short_Field_Encoding_Mandatory

**Claim:** Both Commissioner and Commissionee SHALL always use short field coding of APDUs.

**Formal:** ∀node, apdu. is_commissioner(node) ∨ is_commissionee(node) ⟹ encoding(apdu) = short_field

### FSM Trace

**FSM Evidence:**
- Function `valid_transport_params()` checks: "Lc <= 255 AND length(data) == Lc"
- Function description: "Validates short field encoding per specification requirement"
- All Lc and Le fields are uint8 (single octet) as per function parameters

### Verdict: **HOLDS (by validation function)** ✅

**Reasoning:**
- valid_transport_params() enforces Lc <= 255 (single byte limit)
- All transitions using TRANSPORT_command include valid_transport_params() in guard
- Extended field encoding (multi-byte Lc/Le) would be rejected
- Function enforces short field constraint

### Specification Evidence

**Quote:** "To guarantee interoperability with all NFC Readers/Writers while limiting the number of cases to support, both the NFC Reader/Writer and NFC listener SHALL always use short field coding (aka short length field) of APDUs."  
**Source:** Section 4.21.4, "APDU layer", Page (line 198 in 4.21.md)

**Note:** Extended field coding would use 3-byte Lc field (0x00 + 2-byte length). FSM enforces single-octet Lc/Le.

### Conclusion
Property HOLDS - FSM validation functions enforce short field encoding.

---

## PROP_013: Chaining_Support_Mandatory

**Claim:** Both Commissioner and Commissionee SHALL support C-APDU and R-APDU chaining per ISO/IEC 7816-4.

**Formal:** ∀node. supports_chaining(node, C-APDU) ∧ supports_chaining(node, R-APDU)

### FSM Trace

**FSM Evidence:**
- **C-APDU Chaining:** CHAINING_IN_PROGRESS_RECEIVING state with multiple transitions
  - CLA=0x90 triggers chaining mode
  - append_fragment() function
  - Fragments accumulated until complete

- **R-APDU Chaining:** RESPONSE_INCOMPLETE state with GET_RESPONSE transitions
  - SW1=0x61 indicates incomplete
  - extract_fragment() function
  - Multiple GET_RESPONSE commands until complete (SW1=0x90)

### Verdict: **HOLDS** ✅

**Reasoning:**
- FSM explicitly models both C-APDU chaining (CHAINING_IN_PROGRESS_RECEIVING) and R-APDU chaining (RESPONSE_INCOMPLETE)
- Transitions handle chained/unchained commands (CLA=0x80 vs 0x90)
- Functions support fragment operations (append, extract, join)
- Both chaining directions fully supported

### Specification Evidence

**Quote:** "Both commissionee and commissioner SHALL support C-APDU and R-APDU chaining specified in ISO/IEC 7816-4."  
**Source:** Section 4.21.4, "APDU layer", Page (line 200 in 4.21.md)

### Conclusion
Property HOLDS - FSM fully implements both chaining directions.

---

## PROP_014: ISO_DEP_Compliance

**Claim:** Full ISO-DEP protocol SHALL be implemented in compliance with NFC Forum Digital Specification.

**Formal:** ∀device. implements_ntl(device) ⟹ implements_iso_dep(device) ∧ compliant_with_nfc_forum(device)

### FSM Trace

**FSM Evidence:**
- Assumption ASSUM_001 in FSM: "ISO-DEP protocol implementation is correct and compliant"
- Definition section: "ISO-DEP" term defined with reference to NFC Forum Digital Specification
- ISO-DEP layer is below APDU layer in NTL stack (Figure 36 equivalent)

### Verdict: **HOLDS (by assumption)** ✅

**Reasoning:**
- FSM assumes ISO-DEP layer is correct and compliant
- ISO-DEP is abstraction boundary: FSM models APDU layer, relies on ISO-DEP below
- Property is architectural constraint, not behavior verifiable in FSM
- Documented as security assumption

### Specification Evidence

**Quote:** "The full ISO-DEP protocol SHALL be implemented in compliance with NFC Forum Digital Specification."  
**Source:** Section 4.21.3, "ISO-DEP", Page (line 68 in 4.21.md)

### Conclusion
Property HOLDS by assumption - ISO-DEP compliance is prerequisite for FSM operation.

---

## PROP_015: NFC_Forum_Commissioner_Compliance

**Claim:** Commissioner SHALL comply with NFC Forum requirements for Reader/Writer Module supporting Type 4A Tag Operation.

**Formal:** ∀device. is_commissioner(device) ⟹ complies_with(device, NFC_Forum_Reader_Writer_Type_4A)

### FSM Trace

**Analysis:** This property concerns Commissioner device (external to FSM).

**FSM Evidence:**
- FSM models Commissionee device only
- Assumption references NFC Forum compliance for interoperability
- Property not verifiable in Commissionee FSM

### Verdict: **OUT_OF_SCOPE** (Commissioner behavior) ⚪

**Reasoning:**
- FSM models Commissionee, not Commissioner
- Property requires Commissioner to be NFC Forum compliant
- Commissionee FSM cannot enforce Commissioner compliance
- This is environmental assumption, not Commissionee behavior

### Specification Evidence

**Quote:** "products implementing NTL as a Commissioner SHALL comply with the NFC Forum requirements for an NFC Forum Reader/Writer Module supporting Type 4A Tag Operation"  
**Source:** Section 4.21.1, "NFC Forum requirements", Page (line 52 in 4.21.md)

### Conclusion
Property OUT_OF_SCOPE - Refers to Commissioner implementation, not verifiable in Commissionee FSM.

---

## PROP_016: NFC_Forum_Commissionee_Compliance

**Claim:** Commissionee SHALL comply with NFC Forum requirements for Type 4A Tag Module or Type 4A Tag Platform Module.

**Formal:** ∀device. is_commissionee(device) ⟹ complies_with(device, NFC_Forum_Type_4A_Tag) ∨ complies_with(device, NFC_Forum_Type_4A_Tag_Platform)

### FSM Trace

**FSM Evidence:**
- Assumption in FSM: "NFC Reader/Writer (Commissioner) and Listener (Commissionee) implementations are compliant with NFC Forum specifications"
- Property is architectural/implementation requirement, not behavioral

### Verdict: **HOLDS (by assumption)** ✅

**Reasoning:**
- FSM assumes Commissionee device is NFC Forum compliant Type 4A Tag
- This is implementation prerequisite for FSM to operate correctly
- NFC Forum compliance is lower-layer (NFC-A, ISO-DEP) concern

### Specification Evidence

**Quote:** "products implementing NTL as a Commissionee SHALL comply with the NFC Forum requirements for either NFC Forum Type 4A Tag Module or NFC Forum Type 4A Tag Platform Module (Card Emulation)."  
**Source:** Section 4.21.1, "NFC Forum requirements", Page (line 53 in 4.21.md)

### Conclusion
Property HOLDS by assumption - Commissionee compliance is architectural requirement.

---

## PROP_017: Commissioner_Poll_Mode

**Claim:** Commissioners SHALL act as NFC Forum Type 4A Tag Platform in Poll Mode.

**Formal:** ∀device. is_commissioner(device) ⟹ acts_in_mode(device, Poll_Mode)

### FSM Trace

**Analysis:** This property concerns Commissioner device mode (external to FSM).

### Verdict: **OUT_OF_SCOPE** (Commissioner behavior) ⚪

**Reasoning:**
- FSM models Commissionee, not Commissioner
- Poll Mode is Commissioner's NFC operating mode
- Commissionee operates in Listen Mode (receives polls)
- Property not verifiable in Commissionee FSM

### Specification Evidence

**Quote:** "Commissioners supporting NTL SHALL act as an NFC Forum Type 4A Tag Platform in Poll Mode as defined in NFC Forum Digital Specification."  
**Source:** Section 4.21.2, "NFC-A technology", Page (line 60 in 4.21.md)

### Conclusion
Property OUT_OF_SCOPE - Refers to Commissioner mode, not Commissionee behavior.

---

## PROP_018: Commissionee_Listen_Mode

**Claim:** Commissionees SHALL act as NFC Forum Type 4A Tag Platform in Listen Mode.

**Formal:** ∀device. is_commissionee(device) ⟹ acts_in_mode(device, Listen_Mode)

### FSM Trace

**FSM Evidence:**
- FSM structure: all triggers are received commands (external inputs)
- No transitions show Commissionee initiating RF polling
- Commissionee responds to received commands (Listen Mode behavior)
- Definition section references Listen Mode

### Verdict: **HOLDS (by FSM structure)** ✅

**Reasoning:**
- FSM models reactive behavior: wait for command, then respond
- All transitions triggered by external command reception
- This is characteristic of Listen Mode (receive polls, respond)
- No active polling behavior in FSM

### Specification Evidence

**Quote:** "Commissionees supporting NTL SHALL act as an NFC Forum Type 4A Tag Platform in Listen Mode as defined in NFC Forum Digital Specification."  
**Source:** Section 4.21.2, "NFC-A technology", Page (line 62 in 4.21.md)

### Conclusion
Property HOLDS - FSM reactive structure matches Listen Mode behavior.

---

## PROP_019: TRANSPORT_Command_Exclusivity

**Claim:** Matter messages SHALL be exchanged using TRANSPORT command only after successful SELECT.

**Formal:** ∀session, msg. event exchange_matter_message(session, msg) ⟹ uses_transport_command(session) ∧ event before(select_success(session), exchange_matter_message(session, msg))

### FSM Trace

**Transitions Examined:**
- TRANSPORT commands only succeed from SELECTED, TRANSPORT_ACTIVE, or CHAINING_IN_PROGRESS_RECEIVING states
- All these states reachable only after successful SELECT
- TRANSPORT from IDLE or COMMISSIONING_MODE_READY → ERROR_INVALID_STATE

### Verdict: **HOLDS** ✅

**Reasoning:**
- Same as PROP_004 (State_Transition_Ordering)
- TRANSPORT command is exclusive mechanism for Matter message exchange
- No alternative commands for Matter message transport
- SELECT must succeed before TRANSPORT

### Specification Evidence

**Quote:** "Once commissioning has been successfully initiated with the SELECT command, Matter messages SHALL be exchanged using the proprietary TRANSPORT command."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Page (line 296 in 4.21.md)

### Conclusion
Property HOLDS - TRANSPORT is exclusive message exchange mechanism after SELECT.

---

## PROP_020: Lc_Field_Correct_Encoding

**Claim:** Lc field SHALL correctly encode the actual length of Data field in TRANSPORT command.

**Formal:** ∀cmd, data. Lc_field(cmd) = length(data_field(cmd))

### FSM Trace

**FSM Evidence:**
- Function valid_transport_params() checks: "Lc <= 255 AND length(data) == Lc"
- This validation enforced in guards for all TRANSPORT transitions
- Guard condition includes: "valid_transport_params(CLA, INS, P1, P2, Lc, data)"

### Verdict: **HOLDS** ✅

**Reasoning:**
- valid_transport_params() explicitly validates: length(data) == Lc
- All TRANSPORT command transitions require this validation
- Incorrect Lc encoding would fail guard, causing command rejection

### Specification Evidence

**Quote:** "The Lc single-octet field SHALL encode the length in octets of the payload's Data field in compliance with ISO/IEC 7816-4."  
**Source:** Section 4.21.4.2, "TRANSPORT command", Table 47 description (line 323 in 4.21.md)

### Conclusion
Property HOLDS - FSM validates Lc matches actual data length.

---

## Summary (PROP_011 through PROP_020)

| Property | Verdict | Notes |
|----------|---------|-------|
| PROP_011: GET_RESPONSE_Sequencing | ✅ HOLDS | Strict sequencing enforced |
| PROP_012: Short_Field_Encoding_Mandatory | ✅ HOLDS | Validated by param checks |
| PROP_013: Chaining_Support_Mandatory | ✅ HOLDS | Both C-APDU and R-APDU supported |
| PROP_014: ISO_DEP_Compliance | ✅ HOLDS | By assumption |
| PROP_015: NFC_Forum_Commissioner_Compliance | ⚪ OUT_OF_SCOPE | Commissioner property |
| PROP_016: NFC_Forum_Commissionee_Compliance | ✅ HOLDS | By assumption |
| PROP_017: Commissioner_Poll_Mode | ⚪ OUT_OF_SCOPE | Commissioner property |
| PROP_018: Commissionee_Listen_Mode | ✅ HOLDS | FSM structure matches Listen Mode |
| PROP_019: TRANSPORT_Command_Exclusivity | ✅ HOLDS | Same as PROP_004 |
| PROP_020: Lc_Field_Correct_Encoding | ✅ HOLDS | Validated by guards |

**Violations Found:** 0  
**Out of Scope:** 2 (Commissioner-specific properties)

All Commissionee-relevant properties in this batch HOLD in the FSM.

