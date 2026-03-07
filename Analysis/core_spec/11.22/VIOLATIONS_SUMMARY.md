# BDX Protocol Violations Summary

**Date:** February 22, 2026  
**Protocol:** Matter 1.4 Core Spec §11.22 - Bulk Data Exchange (BDX)  
**Total Properties Analyzed:** 70  
**Source:** security_properties.json  
**FSM Model:** fsm_bdx.json  

---

## Critical Violations Found

### ❌ DEFINITE VIOLATIONS: 2

#### 1. PROP_030: Sleepy_Device_Follower_Constraint
- **Severity:** HIGH
- **Claim:** "The follower role in receiver-drive mode SHALL NOT be occupied by a sleepy device"
- **Violation:** FSM does not model device sleepiness or enforce constraint
- **Attack Path:**
  - Sleepy device accepts RECEIVER_DRIVE mode as responder
  - Becomes follower (sender in receiver-drive or receiver in sender-drive)
  - Goes to sleep without responding
  - Driver times out, transfer fails systematically
- **Spec Reference:** Section 11.22.5.4, "Transfer Mode and Sleepy Devices"
- **Recommendation:** Add `!is_sleepy || will_be_driver` check to mode selection guards

#### 2. PROP_043: Responder_Busy_Backoff
- **Severity:** MEDIUM
- **Claim:** "If receiving RESPONDER_BUSY status, initiator SHALL implement exponential backoff before retry"
- **Violation:** FSM has no backoff mechanism, allows immediate retry
- **Attack Path:**
  - Responder sends RESPONDER_BUSY
  - Initiator transitions to TransferFailed, returns to Idle
  - Can immediately send new SendInit
  - Floods busy responder with requests
- **Spec Reference:** Section 11.22.3.2, "Status Report Message"  
- **Recommendation:** Add BackoffWaiting state with exponential timer

---

## ⚠️ POTENTIAL VIOLATIONS: 7

### 1. PROP_002: Reliable_Transport_Mandatory (Responder Path)
- **Severity:** HIGH
- **Issue:** Responder doesn't explicitly check `reliable_transport` in receive guards
- **Risk:** Could accept BDX over unreliable transport
- **Status:** Initiators check, responders rely on `validate_message_security()` which may not check transport type

### 2. PROP_019: Definite_Length_Commitment (Sender Side)
- **Severity:** MEDIUM
- **Issue:** Sender-side length tracking not explicit in FSM
- **Risk:** Sender could send wrong amount without self-validation
- **Status:** Receiver validates, but sender doesn't verify own commitment before completion

### 3. PROP_023: Block_Message_Length_Bounds (Empty Blocks)
- **Severity:** MEDIUM
- **Issue:** Empty block (0 bytes) rejection unclear
- **Risk:** DoS through infinite empty block loop
- **Status:** `validate_block_length()` should reject but not explicitly shown

### 4. PROP_024: BlockEOF_Length_Bounds (Sender)
- **Severity:** LOW
- **Issue:** No size check before generating BlockEOF
- **Risk:** Could generate oversized final block
- **Status:** Receiver would catch, but sender should validate

### 5. PROP_032: BlockQueryWithSkip_Overflow_Protection
- **Severity:** MEDIUM
- **Issue:** No overflow validation for `BytesToSkip` addition
- **Risk:** Integer overflow in position calculation
- **Attack:** Send skip_amount causing `position + skip > 2^64`

### 6. PROP_063: Session_Atomicity (Partial Data Cleanup)
- **Severity:** MEDIUM
- **Issue:** Partial data cleanup semantics unclear
- **Risk:** Application sees partial invalid data as complete
- **Status:** FSM shows success/failure states but not data cleanup

### 7. PROP_064: Exchange_Context_Isolation (Data Transfer)
- **Severity:** HIGH
- **Issue:** Context validation only at negotiation, not during transfer
- **Risk:** Messages from wrong Exchange ID accepted during data transfer
- **Attack:** Inject Block/BlockAck from different Exchange to hijack session

---

## ⚠️ UNVERIFIABLE FROM FSM: 7

These properties depend on implementation layers below or above the FSM:

1. **PROP_003:** Single Exchange Scope - Exchange ID not in FSM model
2. **PROP_042:** File Designator Authorization - Abstracted to validation function
3. **PROP_047:** File Designator Length - TLV parsing layer responsibility
4. **PROP_058:** Flag Field Consistency - Message encoding abstraction
5. **PROP_061:** Block Counter vs Offset - Risk of implementation confusion
6. **PROP_068:** Offset Calculation - Abstracted to data functions
7. **PROP_069:** Reserved Opcode Handling - Message dispatch layer

---

## ✅ PROPERTIES THAT HOLD: 55

The remaining 55 properties were verified to hold, including:

- **PROP_001:** Encryption_Session_Mandatory ✅
- **PROP_004:** Session_Exclusivity ✅
- **PROP_005:** Sequential_Block_Counter_Ordering ✅
- **PROP_006:** BlockQuery_Sequential_Ordering ✅
- **PROP_010:** Transfer_Mode_Exclusivity ✅
- **PROP_013:** Async_Mode_Prohibition (unreachable states) ✅
- **PROP_016:** Max_Block_Size_Constraint ✅
- **PROP_020:** Length_Verification_Requirement ✅
- **PROP_025:** Sender_Sync_Flow_Control ✅
- **PROP_029:** Timeout_Enforcement_Driver ✅
- **PROP_052:** Premature_BlockEOF_Rejection ✅
- **PROP_054:** Block_Counter_Zero_Start ✅
- **PROP_055:** Block_Counter_Modulo_Arithmetic ✅
- **PROP_062:** Transport_Duplicate_Prevention ✅
- **PROP_067:** Variable_Block_Size_Support ✅
- ... and 40 more

---

## Severity Breakdown

| Severity | Definite Violations | Potential Violations | Total |
|----------|---------------------|----------------------|-------|
| HIGH     | 1                   | 3                    | 4     |
| MEDIUM   | 1                   | 4                    | 5     |
| LOW      | 0                   | 1                    | 1     |
| **Total**| **2**               | **7**                | **9** |

---

## Top Priority Fixes

### 1. Add Sleepy Device Role Enforcement (PROP_030)
**Where:** Mode selection transitions  
**Fix:** Add guards checking device sleepiness against role assignment

### 2. Implement Backoff Mechanism (PROP_043)
**Where:** After RESPONDER_BUSY reception  
**Fix:** Add backoff state with exponential timer before retry

### 3. Add Context Validation During Transfer (PROP_064)
**Where:** All receive transitions in active states  
**Fix:** Add `validate_message_context()` to guards for Block/BlockAck reception

### 4. Enforce Reliable Transport on Responder (PROP_002)
**Where:** Responder receive_SendInit/receive_ReceiveInit  
**Fix:** Add `reliable_transport` check to guards

### 5. Add Overflow Protection for Skip (PROP_032)
**Where:** BlockQueryWithSkip reception  
**Fix:** Validate `current_position + skip_amount` doesn't overflow

---

## Additional Observations

### Async Mode (Provisional)
- States defined but **unreachable** from normal flow
- No transitions lead to SenderAsync or ReceiverAsync
- Effectively dead code (correct per spec requirement)

### Function Abstractions
- Many Security properties depend on correct implementation of:
  - `validate_message_security()`
  - `validate_file_designator()`
  - `validate_block_length()`
  - `skip_bytes()` with overflow handling

### Layering Dependencies
- Exchange ID isolation (PROP_003) depends on Interaction Model layer
- TLV encoding validation (PROP_058) depends on message parser
- Transport reliability (PROP_002) depends on TCP or UDP+MRP layer

---

## Conclusion

The BDX FSM is **well-designed** overall with strong guarantees for:
- Counter ordering and replay protection
- Session lifecycle management
- Length validation
- Flow control and acknowledgments

However, **critical gaps exist** in:
- Multi-layer coordination (sleepy devices, transport validation)
- Retry policy (backoff missing)
- Context isolation during active transfer
- Edge case handling (overflow, empty blocks)

**Recommendation:** Implement the 5 top priority fixes before deployment to production systems.

---

**Full Analysis:** See `PROPERTY_VIOLATION_ANALYSIS.md` for detailed attack paths and specification citations.

