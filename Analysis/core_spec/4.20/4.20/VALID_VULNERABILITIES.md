# PAFTP Valid Specification Vulnerabilities

**Matter Core Specification v1.5, Section 4.20**  
**Date**: February 19, 2026

---

## PROP_001: VERSION_DOWNGRADE_PREVENTION

**Severity**: CRITICAL

### Specification Reference

**Section 4.20.3.3 (Session Establishment):**
> "The Commissionable Device SHALL select a PAFTP protocol version that is the newest which it and the Commissioner both support, where newer protocol version numbers are strictly larger than those of older versions."

**Section 4.20.3.1 (Handshake Request Format):**
> "Supported versions are listed once each, newest first, in descending order."

### Specification Gap

- ❌ No cryptographic protection specified for version list
- ❌ No authentication mechanism for handshake messages
- ❌ No downgrade attack prevention mechanism

### Attack Scenario

```
1. Commissioner (smartphone) supports PAFTP v2, v3, v4
2. Device (smart lock) supports PAFTP v2, v3, v4
3. Commissioner sends Handshake Request: Ver[4,3,2,0,0,0,0,0]
4. ⚡ ATTACKER (Wi-Fi monitor mode) intercepts Public Action Frame
5. Attacker modifies to: Ver[2,0,0,0,0,0,0,0] (removes v4, v3)
6. Device receives modified request
7. Device algorithm: select_newest_common([4,3,2 local], [2 received]) → v2
8. Device sends Handshake Response: Final_Version=2
9. Session established on PAFTP v2 (potentially vulnerable)
10. If v2 has known security flaws → Attacker exploits them
```

**Why Attack Succeeds**:
- Wi-Fi Public Action Frames are broadcast (visible to all stations)
- PAFTP handshake occurs BEFORE PASE encryption
- No cryptographic binding between version list and device identity

**Impact**: Smart home takeover, physical security compromise (door locks)

---

## PROP_003: SEQUENCE_NUMBER_INTEGRITY

**Severity**: CRITICAL

### Specification Reference

**Section 4.20.3.6 (Sequence Numbers):**
> "Peers SHALL check to ensure that all received PAFTP packets properly increment the sender's previous sequence number by 1. If this check fails, the peer SHALL close the PAFTP session and report an error to the application."

### Specification Gap

- ❌ Validation checks sequence VALUE only, not packet ORIGIN
- ❌ No source authentication mechanism specified
- ❌ No MAC/signature to verify packet authenticity

### Attack Scenario

```
Scenario: Factory Commissioning Supply Chain Attack

1. Factory commissioning 10,000 smart speakers
2. Automated Commissioner provisions each device
3. ⚡ ATTACKER compromises factory Wi-Fi network (insider threat)
4. Attacker observes PAFTP session: expected_seq = 15
5. Legitimate packet seq=15 contains: "Enable OTA updates from updates.vendor.com"
6. Attacker races to inject malicious packet FIRST:
   - Seq=15 (correct value)
   - Payload="Enable OTA from attacker.com, disable signature check"
7. Device receives attacker packet first (Wi-Fi race condition)
8. validate_sequence_number(15) == true → ACCEPTED
9. Milliseconds later, legitimate packet seq=15 arrives
10. Device: "Duplicate seq=15" → REJECTED
11. Backdoor configuration installed on device
12. All 10,000 units shipped with backdoor
```

**Why Attack Succeeds**:
- Sequence validation only checks if `seq == expected_seq`
- Does NOT verify packet came from legitimate peer
- Wi-Fi allows race conditions (attacker with proximity/power advantage)

**Impact**: Supply chain compromise, persistent backdoors, botnet creation

---

## PROP_004: ACKNOWLEDGEMENT_VALIDITY

**Severity**: HIGH

### Specification Reference

**Section 4.20.3.8 (Packet Acknowledgements):**
> "Per PAFTP Frame Formats, PAFTP packet receipt acknowledgements SHALL be received as unsigned 8-bit integer values in the header of a PAFTP packet. The value of this field SHALL indicate the sequence number of the acknowledged packet."

> "An acknowledgement is invalid if the acknowledged sequence number does not correspond to an outstanding, unacknowledged PAFTP packet sequence number."

### Specification Gap

- ❌ Validity based on sequence number correspondence, NOT cryptographic authenticity
- ❌ No authentication of acknowledgement packets
- ❌ `is_valid_ack = (ack_num in outstanding_packets_list)` // Missing: `verify_hmac(ack_packet, key)`

### Attack Scenario

```
Scenario: Commissioning Credential Theft via Ack Forgery

1. Legitimate Commissioner → Device: 50-packet SDU (network credentials)
   - Packets 0-19: Wi-Fi SSID/password  
   - Packets 20-39: Matter fabric credentials
   - Packets 40-49: Operational certificates
2. Device legitimately acknowledges packets 0-9 (ack=9)
3. ⚡ ATTACKER uses Wi-Fi jammer to block packets 10-49
4. Commissioner state: outstanding_packets = [10,11,12,...,49]
5. Attacker injects forged packet: [A=1][Ack=49]
6. Commissioner validates:
   - ack==49 in outstanding_packets_list? YES → VALID
   - Clears packets 10-49 from retransmission buffer
   - remote_window_counter += 40 (window reopens)
7. Commissioner: "All packets acknowledged!" → Believes send complete
8. Commissioner closes session, reports "Commissioning Successful"
9. Reality: Device only received 20% of credentials (packets 0-9)
10. Device never joins network (missing Wi-Fi password)
11. User sees "Success" but device non-functional
```

**Why Attack Succeeds**:
- No cryptographic authentication of acknowledgement packets
- Validation based solely on sequence number correspondence

**Impact**: Failed commissioning with false success indication, credential theft

---

## PROP_005: FLOW_CONTROL_WINDOW_ENFORCEMENT

**Severity**: HIGH

### Specification Reference

**Section 4.20.3.7 (Receive Windows):**
> "Both peers SHALL maintain a counter to reflect the current size of the remote peer's receive window. Each peer SHALL decrement this counter when it sends a packet and increment this counter when a sent packet is acknowledged."

### Specification Gap

- ❌ Window counter updates rely on unprotected acknowledgements
- ❌ No verification that acknowledgements are authentic
- ❌ Attacker can manipulate counter via forged acks

### Attack Scenario

```
Scenario: Buffer Overflow via Window Counter Inflation

1. Low-cost IoT smart plug: 2KB RAM, window_size=5
2. Commissioner sends 5 data packets (seq 0-4) → Device buffer FULL
3. Device processing slowly (low-power MCU @ 48MHz)
4. ⚡ ATTACKER injects 5 forged acks BEFORE Device sends real acks:
   [Ack=0], [Ack=1], [Ack=2], [Ack=3], [Ack=4]
5. Commissioner receives forged acks:
   remote_window_counter += 5 → Window FULLY reopened
6. Commissioner sends 5 MORE packets (seq 5-9)
7. Device buffer state:
   - Already contains: packets 0-4 (2KB used)
   - Receives: packets 5-9 (needs 4KB total)
   - Buffer capacity: 2KB
   - Result: BUFFER OVERFLOW
8. Memory corruption:
   - Overwrites function pointers → RCE
   - OR device crashes → DoS
   - OR credential data corruption → brick device
```

**Why Attack Succeeds**:
- Counter increments based on unprotected acknowledgements (see PROP_004)
- No verification of ack authenticity before updating flow control state

**Impact**: Remote code execution, device crash, permanent device failure

---

## PROP_018: CUMULATIVE_ACKNOWLEDGEMENT_CORRECTNESS

**Severity**: HIGH

### Specification Reference

**Section 4.20.3.8 (Packet Acknowledgements):**
> "Acknowledgement of a sequence number indicates acknowledgement of the previous sequence number, if it too is unacknowledged. By induction, acknowledgement of a given packet implies acknowledgement of all packets received on the same PAFTP session prior to the acknowledged packet."

### Specification Gap

- ❌ Cumulative semantics AMPLIFY the impact of forged acknowledgements
- ❌ Single forged ack → multiple false acknowledgements
- ❌ No protection against cumulative forgery attacks

### Attack Amplification

```
Without cumulative acks (per-packet acks):
- Forge 1 ack → 1 false acknowledgement

With cumulative acks (PAFTP design):  
- Forge 1 ack for seq=N → N+1 false acknowledgements (seq 0 through N)
```

### Attack Scenario

```
Scenario: Firmware Corruption via Cumulative Ack Forgery

1. Commissioner sends 100-packet firmware update to smart door lock
2. Device receives only packets 0-9
3. ⚡ ATTACKER injects: [Ack=99]
4. Commissioner interprets:
   - Packet 99 acknowledged
   - By cumulative property: packets 0-98 also acknowledged
   - 100 packets "confirmed delivered"
5. Commissioner clears entire retransmission buffer
6. Commissioner: "Firmware update complete!"
7. Reality: Device has 10% of firmware (packets 0-9)
8. Device applies "complete" firmware → Brick device
9. Door lock inoperable → User locked out
```

**Why Attack Succeeds**:
- Cumulative semantics allow single forged ack to falsely acknowledge many packets
- Combines with PROP_004 (no ack authentication) for amplified impact

**Impact**: Data loss, firmware corruption, device bricking, physical security compromise

---

## PROP_022: WINDOW_COUNTER_CONSISTENCY

**Severity**: HIGH

### Specification Reference

**Section 4.20.3.7 (Receive Windows):**
> "Both peers SHALL maintain a counter to reflect the current size of the remote peer's receive window... Both peers SHALL also keep a counter of their own receive window size based on the sequence number difference between the last packet they received and the last packet they acknowledged."

### Specification Gap

- ❌ `remote_window_counter` updated from unprotected acknowledgements
- ❌ `local_window_counter` updated from injectable sequence numbers
- ❌ Both counters lack cryptographic protection → desynchronization attacks

### Attack Scenario

```
Scenario 1: Window Inflation → Buffer Overflow

1. Legit state: Commissioner.remote_window = 5, Device.local_window = 5
2. ⚡ ATTACKER injects forged ack at Commissioner:
   Commissioner.remote_window += 5 → 10 (INFLATED)
3. Reality: Device.local_window = 5 (UNCHANGED)
4. Commissioner sends 10 packets (believes window=10)
5. Device buffer only has 5 slots
6. Result: Buffer overflow at Device

Scenario 2: Window Deflation → Deadlock

1. ⚡ ATTACKER injects forged packets with valid seq at Device
2. Device.local_window -= 5 (DEFLATED)
3. Device blocks sending (thinks own window closed)
4. Reality: Commissioner waiting for data
5. Result: Deadlock (Device won't send, Commissioner waiting)
```

**Why Attack Succeeds**:
- Both window counters computed from unprotected inputs
- No mechanism to detect desynchronization
- No recovery from inconsistent window state

**Impact**: Flow control bypass, buffer overflow, deadlock, denial of service

---

## PROP_012: HANDSHAKE_TIMEOUT_ENFORCEMENT

**Severity**: MEDIUM

### Specification Reference

**Table 42 (Constants):**
- `PAFTP_CONN_RSP_TIMEOUT` = 30 seconds: "Commissioner waits for handshake response"

**Section 4.20.3.3 (Session Establishment):**
> "When a Commissioner sends a handshake request, it SHALL start a timer with a globally-defined duration of PAFTP_CONN_RSP_TIMEOUT seconds."

### Specification Gap

- ❌ Timeout specified for Commissioner (waiting for response)
- ❌ **NO timeout specified** for Device (waiting for request)
- ❌ Device can remain in WFA-USD-Connected state indefinitely

### Attack Scenario

```
Scenario: Apartment Building Connection Slot Exhaustion

1. Attacker in building with 50 Matter-enabled apartments
2. Each device supports max 3 concurrent WFA-USD connections
3. Attacker script:
   FOR each Device discovered:
       a. Establish WFA-USD connection ← Complete
       b. Do NOT send PAFTP handshake request ← Stall
       c. Repeat 3 times per device
4. After 10 minutes:
   - 50 devices × 3 connections = 150 zombie sessions
   - Each Device stuck in "WFA-USD-Connected" state
   - No PAFTP session established
   - No timeout to clean up
5. Legitimate residents try to commission devices:
   - Commissioner: "Connect to Device"
   - Device: "Max connections reached" → Refuses
6. Devices remain blocked until:
   - Manual power cycle (physical access required)
   - OR factory reset (loses configuration)
```

**Why Attack Succeeds**:
- Specification only defines Commissioner-side timeout
- Device has no timeout for waiting for handshake request
- Connection slots remain occupied indefinitely

**Impact**: Building-wide smart home outage, denial of service, resource exhaustion

---

## PROP_014: SEGMENT_ORDERING_ENFORCEMENT

**Severity**: MEDIUM

### Specification Reference

**Section 4.20.3.5 (Message Segmentation and Reassembly):**
> "PAFTP segments SHALL be sent in order of their position in the original PAFTP SDU, starting with the PAFTP segment at the buffer's head."

> "A peer SHALL reassemble PAFTP segments in the ascending order of the segment sequence numbers."

**Section 4.20.3.6 (Sequence Numbers):**
> "A sequence number incremented past 255 SHALL wrap to zero."

### Specification Gap

- ❌ "Ascending order" is ambiguous with 8-bit wraparound
- ❌ Does it mean numerically ascending (0<1<253) or reception-order preserving (253<254<255<0<1)?
- ❌ Without crypto protection, attacker can reorder segments

### Attack Scenario

```
Scenario: Firmware Corruption via Packet Reordering

1. Smart door lock receiving 60KB firmware update
2. Firmware fragmented into PAFTP segments
3. Final 5 segments have sequence numbers (with wraparound):
   seq: 253, 254, 255, 0, 1
4. ⚡ ATTACKER reorders in transit:
   Original: [253][254][255][0][1]  
   Reordered: [253][254][0][255][1]
5. Device receives in reordered sequence
6. Device reassembles "in ascending order" per spec:
   - Naïve sort: [0][1][253][254][255]
   - INCORRECT! Should be: [253][254][255][0][1]
7. Firmware image corrupted:
   - Bytes 59000-59700 (seq 253-254) placed at END
   - Critical boot code misaligned
8. Device flashes corrupted firmware
9. Device reboots → Boot failure
10. Door lock inoperable → User locked out
```

**Why Attack Succeeds**:
- Specification ambiguity: "ascending order" with wraparound undefined
- No cryptographic protection prevents packet reordering
- Implementation-dependent reassembly logic

**Impact**: Data corruption, firmware bricking, physical security compromise

---

## Summary Table

| Property ID | Name | Severity | Exploitability | Impact |
|-------------|------|----------|----------------|---------|
| PROP_001 | VERSION_DOWNGRADE_PREVENTION | CRITICAL | HIGH | Protocol downgrade, vulnerability exploitation |
| PROP_003 | SEQUENCE_NUMBER_INTEGRITY | CRITICAL | MEDIUM | Packet injection, supply chain compromise |
| PROP_004 | ACKNOWLEDGEMENT_VALIDITY | HIGH | MEDIUM | False success, credential theft |
| PROP_005 | FLOW_CONTROL_WINDOW_ENFORCEMENT | HIGH | HIGH | Buffer overflow, RCE, DoS |
| PROP_018 | CUMULATIVE_ACKNOWLEDGEMENT_CORRECTNESS | HIGH | HIGH | Amplified forgery, data loss |
| PROP_022 | WINDOW_COUNTER_CONSISTENCY | HIGH | HIGH | Desynchronization, deadlock |
| PROP_012 | HANDSHAKE_TIMEOUT_ENFORCEMENT | MEDIUM | HIGH | Connection exhaustion, DoS |
| PROP_014 | SEGMENT_ORDERING_ENFORCEMENT | MEDIUM | MEDIUM | Data corruption, bricking |

---

## Root Cause

All 8 vulnerabilities stem from **lack of cryptographic protection** in PAFTP:

**Section 4.20 NEVER specifies**:
- ❌ WHEN PAFTP packets are protected (before or after PASE?)
- ❌ HOW PAFTP packets are protected (MAC? Encryption?)
- ❌ WHICH fields must be protected (version, seq, ack, flags?)
- ❌ WHO protects PAFTP packets (WFA-USD? PASE? Application?)

**Critical specification statement (Line 6136)**:
> "Unless otherwise specified, the CASE, PASE, User-Directed Commissioning protocol, and Secure Channel Status Report messages SHALL be the only allowed unencrypted messages."

This confirms PASE messages (which run over PAFTP) are **explicitly unencrypted**, meaning PAFTP handshake and initial data transfer occur in **plaintext** before PASE establishes encryption.
