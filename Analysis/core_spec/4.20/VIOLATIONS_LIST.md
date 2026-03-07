# PAFTP Property Violations - Quick Reference

## Analysis Complete: 25/25 Properties

**Status Distribution:**
- ❌ **11 VIOLATED** (44%)
- ✅ **10 HOLDING** (40%)
- ⚠️ **4 PARTIALLY HOLDING** (16%)

---

## ❌ VIOLATED Properties (11)

### CRITICAL Severity (2)

1. **PROP_001: VERSION_DOWNGRADE_PREVENTION**
   - Attacker can modify version list in handshake → force downgrade to vulnerable old version
   - No cryptographic protection on handshake request
   - Spec: S08, S13 (Section 4.20.3.3)

2. **PROP_003: SEQUENCE_NUMBER_INTEGRITY**
   - Attacker can inject packets with forged but valid sequence numbers
   - Validation checks seq value, not packet authenticity
   - Spec: S49 (Section 4.20.3.6)

### HIGH Severity (4)

3. **PROP_004: ACKNOWLEDGEMENT_VALIDITY**
   - Attacker can forge acks for undelivered packets
   - Causes premature window reopen, bypasses flow control
   - Spec: S71 (Section 4.20.3.8)

4. **PROP_005: FLOW_CONTROL_WINDOW_ENFORCEMENT**
   - Window counter manipulated via forged acks
   - Bypasses flow control → buffer overflow
   - Spec: S60 (Section 4.20.3.7)

5. **PROP_018: CUMULATIVE_ACKNOWLEDGEMENT_CORRECTNESS**
   - Single forged ack falsely acknowledges multiple packets
   - Amplified impact: 1 forged ack = N false acknowledgements
   - Spec: S69 (Section 4.20.3.8)

6. **PROP_022: WINDOW_COUNTER_CONSISTENCY**
   - Remote/local window counters desynchronized via forged inputs
   - Causes deadlock, buffer overflow, flow control bypass
   - Spec: S60, S61 (Section 4.20.3.7)

### MEDIUM Severity (4)

7. **PROP_007: IDLE_TIMEOUT_ENFORCEMENT**
   - Only Commissioner enforces idle timeout, not Device
   - Zombie sessions on Device → resource exhaustion
   - Spec: Table 42 (PAFTP_CONN_IDLE_TIMEOUT)

8. **PROP_008: SDU_TRANSMISSION_ATOMICITY**
   - No detection of partial SDU on session close
   - Incomplete data delivered to application OR memory leak
   - Spec: S52, S53 (Section 4.20.3.5)

9. **PROP_012: HANDSHAKE_TIMEOUT_ENFORCEMENT**
   - Device waiting for handshake request has no timeout
   - DoS: connection slot exhaustion
   - Spec: Table 42 (PAFTP_HANDSHAKE_TIMEOUT) - ambiguous

10. **PROP_014: SEGMENT_ORDERING_ENFORCEMENT**
    - Out-of-order delivery with 8-bit seq wraparound → incorrect reassembly
    - Conflict: S49 (strict) vs S51 (reassemble in order)
    - Spec: S48, S49, S51 (Section 4.20.3.5, 4.20.3.6)

### LOW Severity (1)

11. **PROP_010: RESERVED_BITS_ZERO**
    - Reserved bits not validated on reception
    - Forward-compatibility hazard, implementation fingerprinting
    - Spec: S47, S81, S84

---

## ⚠️ PARTIALLY HOLDING Properties (4)

12. **PROP_006: DEADLOCK_PREVENTION**
    - Race condition when both peers reach window=1 simultaneously
    - No recovery mechanism beyond timeout

13. **PROP_009: REASSEMBLY_LENGTH_VERIFICATION**
    - Length check implemented but Message Length field unprotected
    - Attacker can modify field → truncation or overflow

14. **PROP_015: OVERSIZED_SEGMENT_REJECTION**
    - Check implemented but max size from negotiation (vulnerable to downgrade)

15. **PROP_021: MANDATORY_PIGGYBACKING**
    - Piggybacking attempted but blocked when window=0

---

## ✅ HOLDING Properties (10)

- ✅ PROP_002: VERSION_INCOMPATIBILITY_DISCONNECT
- ✅ PROP_011: M_BIT_CONSISTENCY_ACROSS_SEGMENTS
- ✅ PROP_013: ACK_TIMEOUT_ENFORCEMENT
- ✅ PROP_016: SESSION_ISOLATION
- ✅ PROP_017: MATTER_ONLY_TRANSPORT
- ✅ PROP_019: TIMER_RELATIONSHIP_CONSTRAINT
- ✅ PROP_020: ASYMMETRIC_INITIALIZATION_CORRECTNESS
- ✅ PROP_023: STANDALONE_ACK_ACKNOWLEDGEMENT
- ✅ PROP_024: EARLY_ACK_ON_WINDOW_PRESSURE
- ✅ PROP_025: FIFO_ORDERING_FOR_QUEUED_SDUS

---

## Root Cause Analysis

**PRIMARY CAUSE (9/11 violations)**: **Lack of cryptographic protection**

PAFTP spec states:
> "PAFTP itself specifies no cryptographic protection (no encryption, MAC, or signatures)"

But **FAILS TO SPECIFY**:
- ❌ WHAT protection is needed (MAC? Encryption?)
- ❌ WHERE it's provided (WFA-USD? Matter layer?)
- ❌ WHICH fields must be protected (version? seq? ack? all?)

**SECONDARY CAUSES**:
- Asymmetric enforcement (Commissioner ≠ Device rules)
- Incomplete error handling (success cases clear, failure cases vague)
- Specification ambiguities (multiple interpretations possible)

---

## Attack Impact Matrix

| Attack Vector | Affected Properties | Severity | Impact |
|--------------|---------------------|----------|--------|
| **Version Downgrade** | PROP_001 | CRITICAL | Exploit old vulnerabilities |
| **Packet Injection** | PROP_003, PROP_014 | CRITICAL/MEDIUM | Command injection, data corruption |
| **Ack Forgery** | PROP_004, PROP_005, PROP_018, PROP_022 | HIGH | Flow control bypass, data loss, buffer overflow |
| **Zombie Sessions** | PROP_007, PROP_012 | MEDIUM | Resource exhaustion DoS |
| **Data Corruption** | PROP_008, PROP_009, PROP_014 | MEDIUM/HIGH | Incomplete SDU, truncation, overflow |

---

## Top 5 High-Risk Scenarios

1. **Version Downgrade → Exploit Chain**
   - Force PAFTP v2 → exploit known v2 vulnerability → gain control

2. **Cumulative Ack Forgery → Data Loss**
   - Forge ack=N → falsely acknowledge N+1 packets → sender thinks delivered → close session → receiver missing 70% of data → commissioning fails

3. **Window Counter Desync → Buffer Overflow**
   - Forge acks → inflate remote counter → sender floods → Device buffer overflow → crash or memory corruption

4. **Device DoS via Zombie Sessions**
   - Establish N connections → never send handshake request → Device waits indefinitely → exhaust connection slots → legitimate Commissioner blocked

5. **Sequence Injection → Command Hijacking**
   - Observe expected_seq → craft malicious packet with correct seq → inject → legitimate command rejected, malicious accepted

---

## Critical Recommendations

### 1. **Add Cryptographic Protection Requirement** (CRITICAL PRIORITY)

Spec must add section:

**"4.20.X PAFTP Security Dependencies"**
> "All PAFTP packets SHALL be cryptographically authenticated and integrity-protected by [WFA-USD / Matter session layer].
>
> Protected fields SHALL include:
> - Version list in handshake request/response
> - Sequence numbers
> - Acknowledgement numbers  
> - Message Length field
> - Control flags
> - Payload data
>
> See [WFA-USD Spec Section X.Y] and [Matter Spec Section Z.W] for protection mechanisms."

### 2. **Symmetric Timeout Enforcement** (HIGH PRIORITY)

Change Table 42:
- ❌ OLD: "Commissioner must close after idle timeout"
- ✅ NEW: "**Both peers** SHALL close after idle timeout"

Add requirement:
> "Commissionable Device SHALL close WFA-USD connection if PAFTP handshake request not received within PAFTP_HANDSHAKE_TIMEOUT (30s)"

### 3. **Add FSM Guards** (HIGH PRIORITY)

All packet reception transitions must check:
- `authenticated(packet) == true`
- `integrity_verified(packet) == true`
- `reserved_bits(packet) == 0`

### 4. **SDU Atomicity Enforcement** (MEDIUM PRIORITY)

Add FSM state: `sdu_transmission_in_progress = true/false`

Guard all close transitions:
```
IF sdu_transmission_in_progress == true:
  call clear_partial_reassembly_buffers()
  notify_application(SDU_DELIVERY_FAILED)
```

### 5. **Window Counter Bounds Checking** (MEDIUM PRIORITY)

Add validation:
```
IF remote_window_counter > negotiated_max_window_size:
  close_session(WINDOW_OVERFLOW_ERROR)
```

---

## Files Generated

1. **property_violation_analysis.json** - Full detailed analysis with attack paths, spec quotes, counterexamples for all 25 properties
2. **VIOLATIONS_SUMMARY.md** - This comprehensive summary document
3. **paftp_fsm.json** - The FSM model analyzed (previously generated, verified, 9 properties added this session)

---

**Analysis Methodology**: Property-by-property FSM path tracing with guard sufficiency checks and specification evidence collection

**Coverage**: 25/25 properties (100% complete)

**Status**: ✅ ANALYSIS COMPLETE
