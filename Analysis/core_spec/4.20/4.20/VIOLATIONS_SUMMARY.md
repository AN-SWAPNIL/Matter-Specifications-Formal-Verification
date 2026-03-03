# PAFTP Security Property Violations Summary

**Analysis Status**: COMPLETE (25/25 properties analyzed)  
**Specification**: Matter Core Spec v1.5, Section 4.20  
**FSM Model**: paftp_fsm.json  
**Date**: 2024

---

## Executive Summary

**Violation Statistics:**
- **11 VIOLATED** properties (44%)
- **10 HOLDING** properties (40%)
- **4 PARTIALLY HOLDING** properties (16%)

**Severity Breakdown:**
- **2 CRITICAL** vulnerabilities
- **4 HIGH** severity vulnerabilities
- **4 MEDIUM** severity vulnerabilities
- **1 LOW** severity vulnerability

**Root Cause:** Lack of cryptographic protection on PAFTP packets. Spec explicitly states "PAFTP itself specifies no cryptographic protection (no encryption, MAC, or signatures)" relying on WFA-USD/Matter layers, but **fails to specify WHAT protection is needed or WHERE it's provided**.

---

## CRITICAL Violations (Severity: CRITICAL)

### 1. PROP_001: VERSION_DOWNGRADE_PREVENTION
**Status**: VIOLATED (Confidence: 0.95)

**Vulnerability**: MITM attacker can modify version list in handshake request to force downgrade to vulnerable older PAFTP versions.

**Attack Path**:
1. Commissioner sends handshake request: [4, 3, 2, 0, 0, 0, 0, 0] (supports v2-v4)
2. Attacker intercepts and modifies to: [2, 0, 0, 0, 0, 0, 0, 0] (removes v4, v3)
3. Device receives modified list, selects v2 (oldest common) instead of v4 (newest)
4. Session established on vulnerable PAFTP v2

**FSM Evidence**: T_DL_04 transition has guard `valid_handshake_request()` which checks format (0x65, 0x6C, sorted) but NOT authenticity/integrity.

**Spec Quote**: 
> "The Commissionable Device SHALL select a PAFTP protocol version that is the newest which it and the Commissioner both support" (Section 4.20.3.3)

**Specification Gap**: Spec requires selecting newest version but doesn't specify HOW to ensure version list is authentic and unmodified.

**Impact**: If older PAFTP versions have known vulnerabilities, attacker can exploit them by forcing downgrade.

**Recommendation**: Spec should require: "Version negotiation SHALL be cryptographically authenticated by Matter session layer" with mechanism specified.

---

### 2. PROP_003: SEQUENCE_NUMBER_INTEGRITY
**Status**: VIOLATED (Confidence: 0.90)

**Vulnerability**: Attacker can inject packets with forged but valid sequence numbers, bypassing sequence integrity checks.

**Attack Path**:
1. Legitimate session established, expected_seq = 5
2. Attacker observes traffic, infers expected_seq = 5
3. Attacker crafts malicious packet: [Seq=5][Payload=malicious_command]
4. Attacker injects packet on Wi-Fi
5. Receiver executes: `validate_sequence_increment()` → seq=5 matches expected → PASS
6. Malicious payload processed as legitimate
7. Legitimate sender's packet with seq=5 arrives later → FAILS validation (doesn't increment)

**FSM Evidence**: `valid_sequence_number()` checks seq == expected_seq but doesn't verify packet authenticity. Attacker knowing expected_seq can craft valid packet.

**Spec Quote**: 
> "Peers SHALL check to ensure that all received PAFTP packets properly increment the sender's previous sequence number by 1" (Section 4.20.3.6, S49)

**Specification Gap**: Spec requires checking sequence INCREMENT but not sequence AUTHENTICITY. Assumes packets cannot be injected/forged.

**Impact**: 
- Command injection
- Replay attacks
- Session hijacking

**Recommendation**: Spec must explicitly state: "PAFTP sequence number integrity depends on [WFA-USD/Matter] providing authenticated encryption" with section reference.

---

## HIGH Severity Violations

### 3. PROP_004: ACKNOWLEDGEMENT_VALIDITY
**Status**: VIOLATED (Confidence: 0.90)

**Vulnerability**: Attacker can forge acknowledgements with valid sequence numbers, causing premature window reopening and bypassing flow control.

**Attack Path**:
1. Commissioner sends data packet seq=10, starts 15s ack-rx timer
2. Device should ack within 7.5s (send-ack timer)
3. Attacker observes seq=10 was sent
4. Attacker injects forged ack: [A=1][Ack=10]
5. Commissioner validates: `is_valid_ack(10)` → "10 in outstanding_unacked?" → YES
6. Commissioner executes: `acknowledge_cumulative(10)`, stops timer, reopens window
7. Commissioner believes Device received packet (it didn't), session stays alive (Device is unresponsive)

**FSM Evidence**: Guard `is_valid_ack(received_ack)` checks VALUE validity (ack corresponds to outstanding seq) but NOT ORIGIN authenticity.

**Spec Quote**: 
> "An acknowledgement is invalid if the acknowledged sequence number does not correspond to an outstanding, unacknowledged PAFTP packet sequence number" (Section 4.20.3.8, S71)

**Specification Gap**: Definition of "invalid" based on sequence VALUE only, not cryptographic authenticity.

**Impact**:
- Flood attacks (premature window reopen)
- DoS (prevent legitimate timeout/recovery)
- Zombie sessions (sender thinks receiver alive, receiver offline)

---

### 4. PROP_005: FLOW_CONTROL_WINDOW_ENFORCEMENT
**Status**: VIOLATED (Confidence: 0.85)

**Vulnerability**: Window enforcement relies on `remote_window_counter` computed from acks. Forged acks artificially reopen window, bypassing flow control.

**Attack Path**:
1. Commissioner window size=5, sends 5 packets → remote_window_counter=0 (closed)
2. Before Device sends real acks, attacker injects 3 forged acks
3. Commissioner: remote_window_counter += 3 → remote_window_counter=3
4. Commissioner sends 3 more packets (thinks Device has space)
5. Device receives 8 packets total, but window size=5 → buffer overflow or packet drop

**Spec Quote**: 
> "Both peers SHALL maintain a counter to reflect the current size of the remote peer's receive window. Each peer SHALL decrement this counter when it sends a packet and increment this counter when a sent packet is acknowledged." (Section 4.20.3.7, S60)

**Specification Gap**: Spec assumes acks are authentic. Counter algorithm correct but inputs untrusted.

**Impact**: Buffer overflow, memory exhaustion on resource-constrained IoT devices.

---

### 5. PROP_018: CUMULATIVE_ACKNOWLEDGEMENT_CORRECTNESS
**Status**: VIOLATED (Confidence: 0.75)

**Vulnerability**: Cumulative ack semantics amplify impact of forged acks. Single forged ack=N falsely acknowledges N+1 packets.

**Attack Path**:
1. Commissioner sends 20-packet SDU (seq 0-19) for commissioning
2. Device legitimately acks packets 0-5 (ack=5)
3. Packets 6-19 still in flight
4. Attacker observes seq=19 sent (final packet, E=1)
5. Attacker injects forged ack: [A=1][Ack=19] (claiming all 20 packets received)
6. Commissioner executes: `acknowledge_cumulative(19)` → clears outstanding [6-19]
7. Commissioner believes entire SDU transmitted, proceeds to next phase
8. Reality: Packets 6-19 never delivered (attacker dropped them)
9. Device received only 30% of SDU (packets 0-5), missing 70%

**Spec Quote**: 
> "An acknowledgement, therefore, implicitly acknowledges all packets with sequence numbers less than the acknowledged sequence number." (Section 4.20.3.8, S69)

**Specification Gap**: Cumulative semantics efficient but fragile without authenticity. One forged ack = multiple false acknowledgements.

**Impact**: 
- Data loss (sender believes delivery succeeded, receiver missing data)
- Incomplete commissioning credentials
- Application-layer failures

---

### 6. PROP_022: WINDOW_COUNTER_CONSISTENCY
**Status**: VIOLATED (Confidence: 0.75)

**Vulnerability**: Remote and local window counters can be desynchronized via forged acks and injected sequences, breaking flow control.

**Attack Vectors**:
1. **Inflate remote counter**: Forge acks → sender thinks receiver has more capacity than reality → buffer overflow at receiver
2. **Deflate own counter**: Inject phantom packets → receiver thinks own window full → stops accepting legitimate packets
3. **Desynchronize both**: Combined attack causing deadlock or data loss

**FSM Evidence**: 
- `remote_window_counter` updated from acks (untrusted input)
- `own_window_counter` computed from received seq (untrusted input)

**Spec Gap**: Counter algorithms (S60, S61) correct but assume input authenticity.

**Impact**: Flow control bypass, deadlock, resource exhaustion, buffer overflows.

---

## MEDIUM Severity Violations

### 7. PROP_007: IDLE_TIMEOUT_ENFORCEMENT
**Status**: VIOLATED (Confidence: 0.75)

**Vulnerability**: Idle timeout enforced ONLY by Commissioner, not Device. Asymmetric enforcement creates zombie sessions.

**Attack Path**:
1. Commissioner establishes PAFTP session with Device
2. Commissioner crashes (power loss) without sending close
3. Expected: Both peers timeout after 30s idle, free resources
4. Actual Commissioner: Already offline (no timeout executed)
5. Actual Device: FSM has NO idle timeout for Device role (T_PE_22-24 guards all have `role == commissioner`)
6. Device session remains open indefinitely, resources locked

**Spec Quote**: 
> "PAFTP_CONN_IDLE_TIMEOUT: The maximum amount of time no unique data has been sent over a PAFTP session **before the Commissioner must close** the PAFTP session." (Table 42)

**Specification Gap**: Explicitly says "Commissioner must close" but Device behavior unspecified. Device has "MAY terminate" not "SHALL timeout".

**Impact**: 
- Resource exhaustion on Device (zombie sessions accumulate)
- DoS (attacker repeatedly initiates sessions, crashes Commissioner, Device exhausts session slots)

---

### 8. PROP_008: SDU_TRANSMISSION_ATOMICITY
**Status**: VIOLATED (Confidence: 0.70)

**Vulnerability**: No detection that SDU transmission is incomplete on session close. Receiver may have partial SDU with no error indication.

**Attack Path**:
1. Sender transmitting 1000-byte SDU fragmented into 4 segments (seq 10, 11, 12, 13)
2. Sent segments seq=10, 11, 12 (M=1); segment 13 (M=0, final) pending
3. Error occurs (ack timeout, corrupted packet) → session closes
4. Receiver has partial SDU (750 bytes) in reassembly buffer
5. FSM: NO check that partial SDU exists before closing (no guard: `has_incomplete_sdu() == false`)
6. Receiver may deliver incomplete SDU to application OR leak memory

**Spec Quote**: 
> "PAFTP SHALL ensure that application service data units (SDUs) being transmitted are either fully received by the intended peer or if the reliable delivery is not possible a clear indication of the failure SHALL be reported to the application." (Section 4.20.3.5, S52)

**Specification Gap**: Spec claims atomicity ("entire SDU or nothing") but doesn't specify mechanism for detecting/handling partial SDU on abnormal close.

**Impact**: 
- Data corruption at application layer
- Incomplete commissioning credentials
- Memory leaks from unreleased reassembly buffers

---

### 9. PROP_012: HANDSHAKE_TIMEOUT_ENFORCEMENT
**Status**: VIOLATED (Confidence: 0.80)

**Vulnerability**: Device waiting for handshake request has no timeout. DoS vector via connection slot exhaustion.

**Attack Path**:
1. Attacker establishes multiple WFA-USD connections to Device
2. For each connection: Complete WFA-USD handshake but never send PAFTP handshake request
3. Device FSM: Multiple sessions in `DL_WFA_USD_Connected` state, waiting indefinitely
4. No timeout transition: `DL_WFA_USD_Connected → DL_Error` missing for "handshake request never arrives" case
5. Device exhausts connection slots
6. Legitimate Commissioner cannot establish connection (slots full)

**Spec Quote**: 
> "PAFTP_HANDSHAKE_TIMEOUT: The maximum amount of time a peer will wait for successful PAFTP connection establishment before canceling the attempt." (Table 42)

**Specification Gap**: Defines timeout constant but doesn't specify WHO enforces it WHEN. Commissioner has timeout waiting for response (T_CL_05) but Device has no timeout waiting for request.

**Impact**: Resource exhaustion DoS on Device preventing legitimate commissioning.

---

### 10. PROP_014: SEGMENT_ORDERING_ENFORCEMENT
**Status**: VIOLATED (Confidence: 0.85)

**Vulnerability**: Out-of-order segment delivery combined with 8-bit sequence wraparound can cause incorrect reassembly.

**Attack Path**:
1. Sender transmits large SDU requiring segments seq=253, 254, 255, 0, 1 (wraparound)
2. Attacker reorders: arrival order becomes 253, 254, 0, 255, 1
3. Receiver reassembly: "sort in ascending order" (S51)
4. Naïve numeric sort: [0, 1, 253, 254, 255] → WRONG (should be [253, 254, 255, 0, 1])
5. Payload concatenated incorrectly: segment_0 + segment_1 + segment_253 + segment_254 + segment_255
6. Corrupted SDU delivered to application

**Spec Conflict**: 
- S48: "segments SHALL be sent in order" (sender requirement)
- S49: "properly increment by 1" (strict ordering → reject out-of-order)
- S51: "reassemble in ascending order" (implies tolerating out-of-order)

**Specification Gap**: Conflict between strict ordering (S49) and reassembly flexibility (S51). Wraparound handling undefined.

**Impact**: Data corruption, buffer misalignment, potential overflows.

---

## LOW Severity Violations

### 11. PROP_010: RESERVED_BITS_ZERO
**Status**: VIOLATED (Confidence: 0.90)

**Vulnerability**: Reserved bits not validated on reception. Protocol robustness and forward-compatibility issue.

**Issue**: Spec requires reserved bits set to 0 (S47, S81, S84) on sender side but doesn't mandate receiver validation. FSM has no guard checking `reserved_bits(packet) == 0`.

**Impact**:
- Forward-compatibility hazard (if future version uses reserved bits, old implementation won't detect version mismatch)
- Implementation fingerprinting (attacker tests which reserved bits cause rejection)
- Debugging difficulty (corrupted packets with flipped bits accepted)

**Severity**: LOW. More robustness/compatibility issue than direct security vulnerability.

---

## PARTIALLY HOLDING Properties

### 12. PROP_006: DEADLOCK_PREVENTION (Confidence: 0.80)
**Status**: PARTIALLY_HOLDS

**Issue**: T_PE_28 blocks sending when window=1 and no pending ack. Race condition: if both peers transition to this state simultaneously before either's message propagates, mutual deadlock occurs. Spec acknowledges this but doesn't provide recovery mechanism beyond timeout.

---

### 13. PROP_009: REASSEMBLY_LENGTH_VERIFICATION (Confidence: 0.85)
**Status**: PARTIALLY_HOLDS

**Issue**: Spec requires checking reassembled length against Message Length (S52). FSM implements this. However, Message Length field itself can be modified by attacker (no crypto protection), causing:
- False acceptance of truncated messages (attacker reduces Message Length)
- Buffer overflow (attacker increases Message Length beyond reality)

---

### 14. PROP_015: OVERSIZED_SEGMENT_REJECTION (Confidence: 0.80)
**Status**: PARTIALLY_HOLDS

**Issue**: Spec requires rejecting segments exceeding maximum packet size (S52). FSM models this. However, "maximum packet size" value comes from handshake negotiation (Selected Maximum Service Specific Info Length) which can be downgrade-attacked (see PROP_001), causing false rejection of legitimate segments.

---

### 15. PROP_021: MANDATORY_PIGGYBACKING (Confidence: 0.70)
**Status**: PARTIALLY_HOLDS

**Issue**: Spec says acks SHALL be piggybacked on data packets when both exist (S77). FSM attempts this but guard `has_pending_ack && remote_window_counter > 0` may prevent piggybacking if window=0, forcing standalone ack. Window=0 scenario violates "SHALL piggyback".

---

## HOLDING Properties (10 properties, 40%)

The following properties are correctly enforced by the FSM and specification:

1. **PROP_002: VERSION_INCOMPATIBILITY_DISCONNECT** - Device closes connection when no common version exists (T_DL_05, T_DL_06)
2. **PROP_011: M_BIT_CONSISTENCY_ACROSS_SEGMENTS** - M-bit correctly set on all fragments except last
3. **PROP_013: ACK_TIMEOUT_ENFORCEMENT** - 15s ack timeout clearly defined and modeled (T_PE_12-15)
4. **PROP_016: SESSION_ISOLATION** - Concurrent sessions maintain separate state (timers, seq, windows)
5. **PROP_017: MATTER_ONLY_TRANSPORT** - Architectural constraint, properly scoped
6. **PROP_019: TIMER_RELATIONSHIP_CONSTRAINT** - send-ack timer (7.5s) < ack-rx timeout (15s), 2:1 ratio preserved
7. **PROP_020: ASYMMETRIC_INITIALIZATION_CORRECTNESS** - Commissioner seq=0, Device seq=1 correctly modeled
8. **PROP_023: STANDALONE_ACK_ACKNOWLEDGEMENT** - Standalone acks consume sequence and are acknowledged
9. **PROP_024: EARLY_ACK_ON_WINDOW_PRESSURE** - Own window ≤ 2 triggers immediate ack before timer
10. **PROP_025: FIFO_ORDERING_FOR_QUEUED_SDUS** - SDU queue maintains FIFO order

---

## Key Root Causes

### 1. **Lack of Cryptographic Protection (9/11 violations)**
PAFTP spec explicitly states:
> "PAFTP itself specifies no cryptographic protection (no encryption, MAC, or signatures)."

Relies on WFA-USD or Matter layers but **fails to specify**:
- WHAT protection is needed (MAC? Encryption? Both?)
- WHERE it's provided (which layer? which spec section?)
- WHICH fields must be protected (version list? seq? ack? message length? all?)

**Affected Properties**: VERSION_DOWNGRADE_PREVENTION, SEQUENCE_NUMBER_INTEGRITY, ACKNOWLEDGEMENT_VALIDITY, FLOW_CONTROL_WINDOW_ENFORCEMENT, CUMULATIVE_ACKNOWLEDGEMENT_CORRECTNESS, WINDOW_COUNTER_CONSISTENCY, REASSEMBLY_LENGTH_VERIFICATION (partial), SEGMENT_ORDERING_ENFORCEMENT, OVERSIZED_SEGMENT_REJECTION (partial)

### 2. **Asymmetric Enforcement (2 violations)**
Commissioner and Device have different timeout enforcement rules, creating vulnerabilities on one side.

**Affected Properties**: IDLE_TIMEOUT_ENFORCEMENT (Device has no timeout), HANDSHAKE_TIMEOUT_ENFORCEMENT (Device waiting has no timeout)

### 3. **Incomplete Error Handling**
Spec defines success cases clearly but failure cases vaguely or not at all.

**Affected Properties**: SDU_TRANSMISSION_ATOMICITY (partial SDU on close), RESERVED_BITS_ZERO (receiver validation unspecified)

### 4. **Specification Ambiguity**
Multiple interpretations possible, leading to implementation variations and potential bugs.

**Affected Properties**: SEGMENT_ORDERING_ENFORCEMENT (strict vs. lenient ordering), MANDATORY_PIGGYBACKING (window=0 exception), DEADLOCK_PREVENTION (race condition acknowledged but unresolved)

---

## High-Risk Attack Vectors

1. **Version Downgrade + Exploit Old Vulnerability**: Force session to older PAFTP version with known bugs, then exploit
2. **Packet Injection Campaign**: Inject commands with forged seq, forge acks to hide injection, manipulate window counters
3. **Zombie Session DoS**: Exhaust Device connection slots via idle timeout asymmetry or handshake timeout gap
4. **Data Corruption**: Modify Message Length or reorder segments to corrupt reassembled SDU
5. **Flow Control Bypass → Buffer Overflow**: Forge acks to artificially reopen window, flood Device beyond capacity

---

## Recommendations

### Immediate (Critical Priority)
1. **Spec Revision**: Add explicit section: "4.20.X PAFTP Security Dependencies" stating:
   - "All PAFTP packets (handshake, data, ack, close) SHALL be cryptographically authenticated and integrity-protected by [WFA-USD layer / Matter session layer]."
   - Reference specific sections in WFA-USD and Matter specs providing this protection.
   - List protected fields: version list, seq, ack, message length, control flags, payload.

2. **FSM Guards Enhancement**: Add authentication checks to all critical guards:
   - `valid_handshake_request()` → verify version list authenticated
   - `valid_sequence_number()` → verify packet authenticated
   - `is_valid_ack()` → verify ack field authenticated

3. **Symmetric Timeout Enforcement**: Device SHALL also enforce idle timeout (30s) and handshake timeout (30s).

### High Priority
4. **Atomicity Enforcement**: Add FSM state tracking partial SDU transmission. Block close transitions if SDU incomplete.

5. **Window Counter Bounds Checking**: Add validation: `remote_window_counter <= negotiated_max`. Close session if exceeded.

6. **Reserved Bits Validation**: Require receiver rejection of packets with non-zero reserved bits.

### Medium Priority
7. **Clarify Segment Ordering**: Choose strict enforcement (reject out-of-order, simpler) or lenient with wraparound handling (complex, more robust).

8. **Application-Layer End-to-End Verification**: Matter layer should verify successful delivery independent of PAFTP layer (defense in depth).

---

## Analysis Methodology

**Approach**: Property-by-property FSM path tracing
1. Formalize property as FSM query
2. Trace critical transitions for violation paths
3. Check guard conditions for sufficiency
4. Check actions for correctness
5. Determine verdict: HOLDS / VIOLATED / PARTIAL / UNVERIFIABLE
6. Collect specification evidence with exact quotes
7. Document attack paths with FSM state sequences
8. Identify specification gaps causing vulnerabilities

**Tools Used**: FSM model (paftp_fsm.json), Spec (4.20.md), Manual analysis

**Coverage**: 25/25 security properties (100%)

---

**End of Violations Summary**
