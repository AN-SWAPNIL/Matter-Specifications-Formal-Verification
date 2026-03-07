# NTL FSM Model - Coverage Gaps Summary

**Quick Reference Document**  
**Full Report:** [ntl_fsm_coverage_report.md](ntl_fsm_coverage_report.md)

---

## SUMMARY

**Overall Coverage: ~85%**

✅ **Core protocol flows fully covered**  
⚠️ **Edge cases and error recovery partially covered**  
❌ **Critical gaps in re-selection and error state handling**

---

## CRITICAL GAPS (Must Fix)

### 1. ❌ SELECT Re-Selection Undefined
**Issue:** No transitions defined when SELECT received in active session states

**Missing Transitions:**
- SELECTED → ? (SELECT_command)
- TRANSPORT_ACTIVE → ? (SELECT_command)
- CHAINING_IN_PROGRESS_RECEIVING → ? (SELECT_command)
- RESPONSE_INCOMPLETE → ? (SELECT_command)

**Security Impact:** Session hijacking, state confusion, DoS potential

**Recommendation:** Add ERROR_SEQUENCING transitions or session restart logic

---

### 2. ❌ Memory Exceeded from TRANSPORT_ACTIVE
**Issue:** No error transition when TRANSPORT_ACTIVE receives chained TRANSPORT where first fragment exceeds max_supported_size

**Missing Transition:**
```
TRANSPORT_ACTIVE → ERROR_MEMORY_EXCEEDED
  trigger: TRANSPORT_command
  guard: CLA==0x90 && Lc > max_supported_size
  action: send_error_response(0x6A, 0x84)
```

**Impact:** Buffer overflow risk if guard failure not handled

---

### 3. ❌ Error State Recovery Missing
**Issue:** All ERROR_* states and SESSION_TIMEOUT have NO exit transitions

**Missing:**
- ERROR_NOT_IN_COMMISSIONING → ?
- ERROR_MEMORY_EXCEEDED → ?
- ERROR_SEQUENCING → ?
- ERROR_INVALID_AID → ?
- ERROR_INVALID_STATE → ?
- SESSION_TIMEOUT → ?

**Impact:** Resource leakage, stuck sessions, memory exhaustion

**Recommendation:** Add timeout transitions to IDLE or define error state command handling

---

## HIGH PRIORITY GAPS

### 4. ❌ TRANSPORT in RESPONSE_INCOMPLETE
**Missing:** RESPONSE_INCOMPLETE → ERROR_SEQUENCING (TRANSPORT_command)

**Issue:** Sending TRANSPORT during GET_RESPONSE sequence should error

---

### 5. ❌ GET_RESPONSE from IDLE/COMMISSIONING States
**Missing:**
- IDLE → ERROR_INVALID_STATE (GET_RESPONSE_command)
- COMMISSIONING_MODE_READY → ERROR_INVALID_STATE (GET_RESPONSE_command)

**Issue:** GET_RESPONSE before session established should error

---

### 6. ❌ Commands in Error States
**Missing:** Any command received in ERROR_* states has no defined behavior

**Options:**
- Ignore all commands (stay in error)
- Repeat error response
- Allow SELECT to recover session

---

## MEDIUM PRIORITY GAPS

### 7. ⚠️ Extended Field Coding Rejection
**Issue:** Spec mandates short field only, but no explicit rejection of extended field APDUs

**Recommendation:** Add validation in valid_transport_params() to detect and reject extended Lc/Le encoding

---

### 8. ❌ Invalid APDU Structure Errors
**Missing:** ISO/IEC 7816-4 generic errors:
- 0x6700 (wrong length)
- 0x6800 (unsupported function)
- 0x6B00 (wrong parameters P1-P2)
- 0x6D00 (INS not supported)
- 0x6E00 (CLA not supported)

**Recommendation:** Add ERROR_INVALID_APDU state for malformed APDUs

---

## FULLY COVERED ✅

### All SHALL Requirements (with noted exceptions)
- [x] APDU chaining (C-APDU and R-APDU)
- [x] SELECT with correct AID
- [x] SELECT response format
- [x] TRANSPORT processing (unchained and chained)
- [x] GET_RESPONSE processing
- [x] Memory exceeded errors (from SELECTED and CHAINING states)
- [x] P1/P2 consistency checking
- [x] GET_RESPONSE sequencing (from active states)
- [x] Invalid AID error
- [x] Not in commissioning mode error
- [x] TRANSPORT before SELECT error
- [x] Response encoding (SW1/SW2, data fields)
- [x] Idle timeout (30s)
- [x] Protocol version (0x01)
- [x] Commissioning mode access control

### All Response Encodings
- [x] SW1=0x90, SW2=0x00 (complete success)
- [x] SW1=0x61, SW2=remaining (incomplete)
- [x] SW1=0x69, SW2=0x85 (conditions not satisfied)
- [x] SW1=0x6A, SW2=0x84 (memory exceeded)
- [x] SW1=0x6A, SW2=0x82 (invalid AID)

### All Primary State Transitions
- [x] IDLE ↔ COMMISSIONING_MODE_READY
- [x] COMMISSIONING_MODE_READY → SELECTED
- [x] SELECTED → TRANSPORT_ACTIVE
- [x] SELECTED → CHAINING_IN_PROGRESS_RECEIVING
- [x] SELECTED → RESPONSE_INCOMPLETE
- [x] TRANSPORT_ACTIVE → TRANSPORT_ACTIVE (loop)
- [x] TRANSPORT_ACTIVE → CHAINING_IN_PROGRESS_RECEIVING
- [x] TRANSPORT_ACTIVE → RESPONSE_INCOMPLETE
- [x] CHAINING_IN_PROGRESS_RECEIVING → loops and completions
- [x] RESPONSE_INCOMPLETE → TRANSPORT_ACTIVE (last fragment)
- [x] RESPONSE_INCOMPLETE → RESPONSE_INCOMPLETE (continuation)
- [x] All active states → SESSION_TIMEOUT

---

## MISSING TRANSITIONS TABLE

| From State | Trigger | Missing To State | Error Code | Priority |
|------------|---------|------------------|------------|----------|
| SELECTED | SELECT_command | ERROR_SEQUENCING or session restart | 0x6985 | CRITICAL |
| TRANSPORT_ACTIVE | SELECT_command | ERROR_SEQUENCING | 0x6985 | CRITICAL |
| TRANSPORT_ACTIVE | TRANSPORT (CLA=0x90, Lc>max) | ERROR_MEMORY_EXCEEDED | 0x6A84 | CRITICAL |
| CHAINING_IN_PROGRESS | SELECT_command | ERROR_SEQUENCING | 0x6985 | CRITICAL |
| RESPONSE_INCOMPLETE | SELECT_command | ERROR_SEQUENCING | 0x6985 | CRITICAL |
| RESPONSE_INCOMPLETE | TRANSPORT_command | ERROR_SEQUENCING | 0x6985 | HIGH |
| IDLE | GET_RESPONSE_command | ERROR_INVALID_STATE | 0x6985 | HIGH |
| COMMISSIONING_MODE_READY | GET_RESPONSE_command | ERROR_INVALID_STATE | 0x6985 | HIGH |
| ERROR_* (all) | timer_tick (timeout) | IDLE | N/A | CRITICAL |
| ERROR_* (all) | Any command | Repeat error or allow recovery | Various | HIGH |
| SESSION_TIMEOUT | Any trigger | IDLE | N/A | HIGH |

---

## RECOMMENDED ADDITIONS

### New Transitions (11 critical additions)

1. **SELECTED → ERROR_SEQUENCING** (SELECT re-issued)
2. **TRANSPORT_ACTIVE → ERROR_SEQUENCING** (SELECT re-issued)
3. **TRANSPORT_ACTIVE → ERROR_MEMORY_EXCEEDED** (chained start, Lc > max)
4. **CHAINING_IN_PROGRESS_RECEIVING → ERROR_SEQUENCING** (SELECT during chaining)
5. **RESPONSE_INCOMPLETE → ERROR_SEQUENCING** (SELECT during GET_RESPONSE)
6. **RESPONSE_INCOMPLETE → ERROR_SEQUENCING** (TRANSPORT during GET_RESPONSE)
7. **IDLE → ERROR_INVALID_STATE** (GET_RESPONSE before session)
8. **COMMISSIONING_MODE_READY → ERROR_INVALID_STATE** (GET_RESPONSE before SELECT)
9. **ERROR_* → IDLE** (timeout cleanup, 5s after error)
10. **SESSION_TIMEOUT → IDLE** (immediate cleanup)
11. **ERROR_* → ERROR_*** (stay transitions for repeated commands - optional)

### New Functions (3)

1. `clear_error_state()` - Cleanup for error recovery
2. `clear_session_state()` - Full session cleanup (fragments + responses + timers)
3. `validate_extended_field_coding()` - Detect/reject extended field APDUs

### New Security Properties (3)

1. **ERROR_STATE_TIMEOUT** - Error states SHALL timeout to prevent resource leakage
2. **SESSION_UNIQUENESS** - Only one active session per device
3. **RESPONSE_BUFFER_BOUNDS** - Response buffer SHALL not exceed implementation limits

---

## BEHAVIORAL SCENARIOS STATUS

| Scenario | Status | Notes |
|----------|--------|-------|
| TRANSPORT chained from TRANSPORT_ACTIVE with memory exceeded | ⚠️ PARTIAL | Missing explicit ERROR_MEMORY_EXCEEDED transition |
| SELECT in SELECTED state | ❌ MISSING | No transition defined |
| SELECT in TRANSPORT_ACTIVE | ❌ MISSING | No transition defined |
| SELECT in CHAINING | ❌ MISSING | Memory leak risk if fragments not cleared |
| SELECT in RESPONSE_INCOMPLETE | ❌ MISSING | Memory leak risk if response buffer not cleared |
| Commands in error states | ❌ MISSING | Undefined behavior |
| Memory exceeded first fragment from SELECTED | ✅ COVERED | Full coverage |
| Memory exceeded later fragments | ✅ COVERED | Full coverage |
| TRANSPORT during GET_RESPONSE | ❌ MISSING | Should error |
| P1/P2 consistency | ✅ COVERED | Full coverage |
| GET_RESPONSE sequencing | ✅ COVERED | From active states |
| Idle timeout | ✅ COVERED | All active states |

---

## VERIFICATION CHECKLIST

### Protocol Requirements
- [x] All SELECT scenarios (normal) ✅
- [ ] All SELECT scenarios (edge cases) ❌
- [x] All TRANSPORT scenarios (primary) ✅
- [ ] All TRANSPORT scenarios (error states) ❌
- [x] All GET_RESPONSE scenarios (sequencing) ✅ (partial)
- [ ] All GET_RESPONSE scenarios (invalid states) ❌
- [x] All error codes (0x6985, 0x6A84, 0x6A82) ✅
- [ ] All ISO/IEC 7816-4 errors ❌
- [x] All response encodings ✅
- [x] Chaining (fragments, P1/P2, memory bounds) ✅
- [x] Timeout enforcement ✅

### State Coverage
- [x] IDLE ✅
- [x] COMMISSIONING_MODE_READY ✅
- [x] SELECTED ✅ (missing SELECT re-issue)
- [x] TRANSPORT_ACTIVE ✅ (missing SELECT + memory overflow edge case)
- [x] CHAINING_IN_PROGRESS_RECEIVING ✅ (missing SELECT)
- [x] RESPONSE_INCOMPLETE ✅ (missing SELECT + TRANSPORT)
- [x] ERROR_NOT_IN_COMMISSIONING ✅ (missing exit paths)
- [x] ERROR_MEMORY_EXCEEDED ✅ (missing exit paths)
- [x] ERROR_SEQUENCING ✅ (missing exit paths)
- [x] ERROR_INVALID_AID ✅ (missing exit paths)
- [x] ERROR_INVALID_STATE ✅ (missing exit paths)
- [x] SESSION_TIMEOUT ✅ (missing cleanup transition)

### Command Coverage from Each State
- [x] SELECT from IDLE ✅
- [x] SELECT from COMMISSIONING_MODE_READY ✅
- [ ] SELECT from SELECTED ❌
- [ ] SELECT from TRANSPORT_ACTIVE ❌
- [ ] SELECT from CHAINING ❌
- [ ] SELECT from RESPONSE_INCOMPLETE ❌
- [ ] SELECT from ERROR_* ❌
- [x] TRANSPORT from IDLE ✅ (error)
- [x] TRANSPORT from COMMISSIONING_MODE_READY ✅ (error)
- [x] TRANSPORT from SELECTED ✅
- [x] TRANSPORT from TRANSPORT_ACTIVE ✅ (partial - missing memory overflow)
- [x] TRANSPORT from CHAINING ✅
- [ ] TRANSPORT from RESPONSE_INCOMPLETE ❌
- [ ] TRANSPORT from ERROR_* ❌
- [x] GET_RESPONSE from SELECTED ✅ (error)
- [x] GET_RESPONSE from TRANSPORT_ACTIVE ✅ (error)
- [x] GET_RESPONSE from CHAINING ✅ (error)
- [x] GET_RESPONSE from RESPONSE_INCOMPLETE ✅
- [ ] GET_RESPONSE from IDLE ❌
- [ ] GET_RESPONSE from COMMISSIONING_MODE_READY ❌
- [ ] GET_RESPONSE from ERROR_* ❌

---

## IMPLEMENTATION PRIORITY

### Phase 1: CRITICAL (Security & Stability)
1. Add SELECT re-selection error transitions
2. Add ERROR_MEMORY_EXCEEDED from TRANSPORT_ACTIVE
3. Add error state timeout to IDLE transitions
4. Add SESSION_TIMEOUT → IDLE cleanup

**Estimated Coverage After Phase 1: 92%**

### Phase 2: HIGH (Correctness)
5. Add TRANSPORT/GET_RESPONSE error transitions for RESPONSE_INCOMPLETE/IDLE/COMMISSIONING states
6. Add command handling in ERROR_* states (ignore or repeat error)

**Estimated Coverage After Phase 2: 96%**

### Phase 3: MEDIUM (Robustness)
7. Add extended field coding validation
8. Add ISO/IEC 7816-4 generic error handling
9. Add new security properties

**Estimated Coverage After Phase 3: 98%**

---

## CONTACT & QUESTIONS

For questions about specific gaps or recommendations, refer to detailed analysis in:
- **Full Report:** [ntl_fsm_coverage_report.md](ntl_fsm_coverage_report.md)
- **Spec Reference:** Matter Core Specification v1.4, Section 4.21
- **FSM Model:** [ntl_fsm_model.json](ntl_fsm_model.json)

---

**Report Date:** 2026-02-13  
**Status:** Ready for Phase 1 Implementation
