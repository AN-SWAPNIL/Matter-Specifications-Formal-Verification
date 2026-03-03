# PAFTP Defense Analysis — Independent Verification Report

**Verification Date**: February 15, 2026  
**Specification Under Review**: Matter Core Spec v1.5, Section 4.20 (PAFTP)  
**Document Verified**: `DEFENSE_FINAL_SUMMARY.md`  
**Sources Used**:

- `4.20.md` — Full PAFTP specification text (796 lines, Section 4.20 from Matter v1.5)
- `core_spec.md` — Full Matter Core Specification R1.4 (49,716 lines)
- Graph RAG index of `core_spec` (571 chunks, pages 1–585)
- `paftp_analysis_notes.md` — 84 enumerated SHALL requirements (S01–S84)
- `paftp_security_properties.json` — 50 formal property definitions (PROP_001–PROP_050)

---

## 1. Executive Summary

The DEFENSE_FINAL_SUMMARY.md contains **significant evidentiary and architectural errors** that undermine its conclusions. The most critical finding is that its **only "disproved" violation (PROP_008) relies on a fabricated specification quote** — the cited text does not exist anywhere in the PAFTP specification. Additionally, the root cause analysis mischaracterizes an intentional architectural decision as a specification defect by ignoring that BTP (the BLE equivalent, Section 4.19) follows the exact same design pattern.

| Metric                     | Defense Claim | Verified Result                                         |
| -------------------------- | ------------- | ------------------------------------------------------- |
| Violations Disproved       | 1 (PROP_008)  | **0** — disproval evidence fabricated                   |
| Violations Upheld          | 10            | **6 valid (DoS-class), 4 overstated**                   |
| Root Cause Valid           | Yes           | **Misleading** — ignores BTP parallel and PASE layering |
| Attack Scenarios Realistic | 8 presented   | **1 fully realistic, 2 partially, 5 overstated**        |

---

## What I confirmed (concise)

| Category                                                    | Properties                                     | Explanation                                                                                                     | Status                            |
| ----------------------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| Valid / confirmed (practical/DoS risks)                     | `PROP_004`, `PROP_005`, `PROP_018`, `PROP_022` | Unauthenticated ACKs / window manipulation → real Denial‑of‑Service and state‑corruption vectors                | Confirmed (DoS) ⚠️                |
| Valid but overstated as data‑compromise                     | `PROP_001`, `PROP_003`, `PROP_014`             | Transport flaws enable disruption (DoS/replay); payload confidentiality/integrity protected by PASE/CASE        | Valid (DoS only)                  |
| Correct observation (design choice / interoperability risk) | `PROP_007`, `PROP_012`                         | Idle‑timeout asymmetry & missing Device handshake timeout → exploitable for zombie‑session DoS                  | Valid (design / interoperability) |
| Minor but true                                              | `PROP_010`                                     | Receivers lack explicit validation for reserved bits                                                            | Minor                             |
| Incorrectly disproved                                       | `PROP_008`                                     | Defense cites a **non‑existent** S52 quote; spec has limited reassembly checks but no broad atomicity guarantee | Defense disproval **invalid** ❌  |

---

## 2. Critical Finding #1 — Fabricated Quote for PROP_008 Disproval

### What the Defense Claims

The defense summary's **only disproved violation** (PROP_008: SDU_TRANSMISSION_ATOMICITY) cites:

> "PAFTP SHALL ensure that application service data units (SDUs) being transmitted are either fully received by the intended peer or **if the reliable delivery is not possible a clear indication of the failure SHALL be reported to the application.**"  
> — Section 4.20.3.5, Statement S52

The defense concludes: _"VIOLATION DISPROVED. The specification mandates failure indication for incomplete SDUs."_

### What the Verification Found

1. **The quote does not exist in `4.20.md`** — I searched the entire 796-line specification text. Zero matches for "fully received", "reliable delivery", or "clear indication of the failure".

2. **The quote does not exist in the Graph RAG index** — Hybrid search across all 571 chunks of `core_spec` (v1.4) returned zero relevant matches.

3. **S52 refers to something completely different** — In `paftp_analysis_notes.md` (line 98), the actual S52 is:

   > "S52: Max window size SHALL be established in handshake."

   This is about window size negotiation, not SDU atomicity.

4. **The quote only appears in self-referential analysis documents** — It exists in `VIOLATIONS_SUMMARY.md`, `property_violation_analysis.json`, and `DEFENSE_FINAL_SUMMARY.md` — all generated by the same analysis pipeline. It was never sourced from the actual specification.

### What the Specification ACTUALLY Says (Section 4.20.3.5)

The closest real specification text is:

> "If the reassembled buffer's length does not match that specified by the sender, or if received PAFTP segment payload size would exceed the maximum PAFTP packet size, or receiver receives an Ending Segment without the presence of a previous Beginning Segment, or a Beginning Segment when another PAFTP SDU's transmission is already in progress, the receiver PAFTP SHALL close the PAFTP session and report an error to the application."

This provides **partial protection** through specific error conditions that trigger session closure + error reporting. However:

- It only catches specific malformation errors (length mismatch, oversized segments, missing Beginning, duplicate Beginning)
- It does NOT provide the broad reliability guarantee the fabricated quote claims
- It does NOT address the case where a session closes mid-SDU-transmission without the specific error conditions listed

### Verdict

**PROP_008 disproval is INVALID.** The defense used a non-existent specification quote. PROP_008 should be reclassified as **partially upheld** — the spec provides error handling for specific malformation cases but lacks a general incomplete-SDU-delivery guarantee.

---

## 3. Critical Finding #2 — PAFTP is Intentionally Pre-Security (BTP Parallel)

### The Defense's Root Cause Claim

> "PRIMARY DEFECT: Missing Security Dependency Specification — Section 4.20 fails to explicitly document: (1) WHICH layer provides cryptographic protection for PAFTP packets, (2) WHAT protection is required, (3) WHICH PAFTP fields must be protected, (4) Cross-references to Chapters 4–6 mechanisms"

### Why This Is Architecturally Misleading

#### 3.1. PAFTP Sits BELOW the Security Layer

The Matter architecture has a clear layering:

```
┌─────────────────────────┐
│  Matter Application     │  ← uses secure sessions
├─────────────────────────┤
│  PASE / CASE            │  ← establishes security (encryption, authentication)
├─────────────────────────┤
│  PAFTP / BTP            │  ← transport layer (carries PASE messages)
├─────────────────────────┤
│  WFA-USD / BLE GATT     │  ← physical/link layer
└─────────────────────────┘
```

Evidence from spec (page 161):

> "PASE SHALL only be used for session establishment mechanism during device commissioning."
> "BTP MAY be used as the transport for device commissioning."
> "CASE, PASE, User-Directed Commissioning protocol, and Secure Channel Status Report messages SHALL be the only allowed **unencrypted** messages."

PAFTP **transports** the PASE messages that establish encryption. It CANNOT depend on PASE because PASE runs on top of it. Demanding a "security dependency" from PAFTP to PASE is like demanding TCP reference TLS — the transport cannot depend on what it carries.

#### 3.2. BTP (Section 4.19) Has the Exact Same Design

BTP, the established BLE transport protocol in Matter since v1.0, has:

- **Zero security cross-references** — Section 4.19 contains no references to PASE, CASE, encryption, authentication, or Chapters 4–6 security mechanisms
- **Identical asymmetric idle timeout language** — `core_spec.md` line 10035:

  > "BTP_CONN_IDLE_TIMEOUT: The maximum amount of time no unique data has been sent over a BTP session before the **Central Device** must close the BTP session."

  Compare with PAFTP Table 42:

  > "PAFTP_CONN_IDLE_TIMEOUT: The maximum amount of time no unique data has been sent over a PAFTP session before the **Commissioner** must close the PAFTP session."

- **Same frame format, same control flags, same timer structure, same sequence numbering, same window mechanism**

If the lack of security cross-references were a genuine specification defect, it would have been identified in BTP years ago. PAFTP is explicitly described as "akin to BTP" (Section 4.20, opening paragraph), confirming this is a deliberate design pattern.

#### 3.3. The TCP/TLS Analogy Is Backwards

The defense states:

> "TCP doesn't provide encryption, but TLS documentation explicitly states 'TLS operates over TCP' and references TCP's role. Section 4.20 lacks equivalent explicit security layering documentation."

This analogy **supports the opposite conclusion**: TCP does not reference TLS. TLS references TCP. Similarly, PASE should reference PAFTP/BTP as transports, not the other way around. The defense's own analogy disproves its root cause claim.

---

## 4. Claim-by-Claim Verification

### 4.1. PROP_008 — SDU_TRANSMISSION_ATOMICITY (Defense: Disproved)

| Aspect         | Defense Claim                     | Verification                                        |
| -------------- | --------------------------------- | --------------------------------------------------- |
| Evidence       | S52 quote about reliable delivery | **Quote does not exist in specification**           |
| Actual S52     | (not checked by defense)          | "Max window size SHALL be established in handshake" |
| Real spec text | Not referenced                    | Error handling for specific malformation cases only |

**Verified verdict**: **INVALID DISPROVAL** — Should be partially upheld. Spec handles specific errors but lacks general incomplete-delivery guarantee.

---

### 4.2. PROP_001 — VERSION_DOWNGRADE_PREVENTION (Defense: Upheld/CRITICAL)

**Defense says**: No protection mechanism against version list modification in Section 4.20.3.3.

**Spec says** (Section 4.20.3.3):

> "The Commissionable Device SHALL select a PAFTP protocol version that is the newest which it and the Commissioner both support"

**Verification**:

- **Correct at PAFTP layer**: No integrity protection on the version list. An active attacker on the Wi-Fi channel could strip versions from the handshake request.
- **Overstated impact**: PAFTP currently defines only one version value (`4 = PAFTP as defined by Matter v1.5`). Downgrade to a "vulnerable older version" is hypothetical since no older version exists.
- **PASE mitigates data compromise**: Even if downgraded, PASE session above provides end-to-end authentication. The attacker cannot extract credentials through a PAFTP version downgrade alone.
- **DoS impact valid**: Stripping all versions forces the Device to close the connection (spec says: "If the Commissionable Device determines that it and the Commissioner do not share a supported PAFTP protocol version, the Commissionable Device SHALL close its WFA-USD connection").

**Verified verdict**: **Partially valid** — transport-layer DoS is realistic; data compromise via downgrade is overstated.

---

### 4.3. PROP_003 — SEQUENCE_NUMBER_INTEGRITY (Defense: Upheld/CRITICAL)

**Defense says**: Checking sequence value doesn't prevent injection of packets with correct sequence numbers.

**Spec says** (Section 4.20.3.6):

> "Peers SHALL check to ensure that all received PAFTP packets properly increment the sender's previous sequence number by 1. If this check fails, the peer SHALL close the PAFTP session and report an error to the application."

**Verification**:

- **Correct at PAFTP layer**: Sequence checking without authentication cannot prevent a MitM from replacing a legitimate packet with a forged packet bearing the correct sequence number.
- **Overstated impact**: Any injected data would be processed by PASE, which performs cryptographic authentication. Injected PASE messages would fail verification.
- **DoS impact valid**: An attacker could race to inject a packet before the legitimate one arrives, causing the legitimate packet to fail sequence check and close the session.

**Verified verdict**: **Partially valid** — session disruption/DoS is realistic; data injection is mitigated by PASE.

---

### 4.4. PROP_004 — ACKNOWLEDGEMENT_VALIDITY (Defense: Upheld/HIGH)

**Defense says**: Section 4.20.3.8 defines validity based on sequence number correspondence only, not authenticity.

**Spec says** (Section 4.20.3.8):

> "An acknowledgement is invalid if the acknowledged sequence number does not correspond to an outstanding, unacknowledged PAFTP packet sequence number."
> "If a peer's acknowledgement-received timer expires, or if a peer receives an invalid acknowledgement, the peer SHALL close the PAFTP session and report an error to the application."

**Verification**:

- **Valid**: Forged acknowledgements that match outstanding sequence numbers would be accepted. This could cause the sender to prematurely free retransmission buffers, losing data.
- **Impact correctly categorized**: This is a genuine DoS vector — data loss through confirmed-but-undelivered packets.

**Verified verdict**: **Valid (DoS-class)**. This is one of the most credible vulnerabilities.

---

### 4.5. PROP_005 — FLOW_CONTROL_WINDOW_ENFORCEMENT (Defense: Upheld/HIGH)

**Defense says**: Section 4.20.3.7 specifies counter algorithm but assumes acknowledgements are trustworthy.

**Spec says** (Section 4.20.3.7):

> "Each peer SHALL decrement this counter when it sends a packet and increment this counter when a sent packet is acknowledged."

**Verification**:

- **Valid**: Forged acks can artificially reopen the remote window, causing a sender to overwhelm a constrained receiver.
- **Impact correctly categorized**: DoS via buffer overflow on resource-constrained devices is realistic.

**Verified verdict**: **Valid (DoS-class)**.

---

### 4.6. PROP_018 — CUMULATIVE_ACKNOWLEDGEMENT_CORRECTNESS (Defense: Upheld/HIGH)

**Defense says**: Section 4.20.3.8 (S69) defines cumulative semantics without authentication.

**Spec says** (Section 4.20.3.8):

> "Acknowledgement of a sequence number indicates acknowledgement of the previous sequence number, if it too is unacknowledged. By induction, acknowledgement of a given packet implies acknowledgement of all packets received on the same PAFTP session prior to the acknowledged packet."

**Verification**:

- **Valid**: Forging a single high-numbered ack implicitly acknowledges all prior packets, causing mass data loss from retransmission buffers.
- **Amplification effect**: One forged packet can clear entire send buffer. This is correctly identified as HIGH severity.

**Verified verdict**: **Valid (DoS-class with amplification)**.

---

### 4.7. PROP_022 — WINDOW_COUNTER_CONSISTENCY (Defense: Upheld/HIGH)

**Defense says**: Counter updates from unprotected acks.

**Verification**:

- This is the same underlying issue as PROP_004 and PROP_005 — unauthenticated acks affect state.
- **Valid but redundant** with PROP_004/005.

**Verified verdict**: **Valid but overlaps with PROP_004/005**.

---

### 4.8. PROP_007 — IDLE_TIMEOUT_ENFORCEMENT (Defense: Upheld/MEDIUM)

**Defense says**: Asymmetric enforcement — only Commissioner must close.

**Spec says** (Table 42):

> "PAFTP_CONN_IDLE_TIMEOUT: The maximum amount of time no unique data has been sent over a PAFTP session before the **Commissioner** must close the PAFTP session." — 30 seconds

**Verification**:

- **Factually correct**: Only the Commissioner is mandated to enforce idle timeout.
- **But this is identical to BTP**: `BTP_CONN_IDLE_TIMEOUT` uses identical asymmetric language: _"before the Central Device must close the BTP session."_
- **Design rationale**: The Commissioner/Central Device is the initiator and typically has more resources. The Device is a constrained endpoint that may not need to independently enforce idle timeouts.

**Verified verdict**: **Valid observation but a deliberate design pattern consistent with BTP, not a PAFTP-specific defect.** Severity should be LOW, not MEDIUM.

---

### 4.9. PROP_012 — HANDSHAKE_TIMEOUT_ENFORCEMENT (Defense: Provisionally Upheld)

**Defense says**: Cannot verify — Table 42 content omitted from provided documentation.

**Verification**: Table 42 IS available in `4.20.md` (lines 760–796). It shows:

| Constant               | Description                                                                                               | Default   |
| ---------------------- | --------------------------------------------------------------------------------------------------------- | --------- |
| PAFTP_CONN_RSP_TIMEOUT | Max time after sending handshake request to wait for handshake response before closing WFA-USD connection | 5 seconds |

Additionally, Section 4.20.3.3 explicitly states:

> "When a Commissioner sends a handshake request, it SHALL start a timer with a globally-defined duration of PAFTP_CONN_RSP_TIMEOUT seconds. If this timer expires before the Commissioner receives a handshake response from the Commissionable Device, the Commissioner SHALL close the PAFTP session and report an error to the application."

This timeout is **Commissioner-side only**. The Device side has no equivalent timeout for waiting on a handshake request — it waits indefinitely after WFA-USD connection establishment.

**Verified verdict**: **Partially valid** — Commissioner-side is fully specified with 5s timeout. Device-side lacks explicit handshake request timeout (same pattern as BTP). This is a DoS vector: attacker can exhaust Device connection slots by establishing WFA-USD connections without sending handshake requests.

---

### 4.10. PROP_014 — SEGMENT_ORDERING_ENFORCEMENT (Defense: Provisionally Upheld)

**Defense says**: Cannot verify — referenced statements not fully accessible.

**Verification**: The relevant spec text IS available. Section 4.20.3.5:

> "If a PAFTP SDU is split into more than one PAFTP segment, the PAFTP segments SHALL be sent in order of their position in the original PAFTP SDU, starting with the PAFTP segment at the buffer's head."

Section 4.20.3.6:

> "Peers SHALL check to ensure that all received PAFTP packets properly increment the sender's previous sequence number by 1."

And:

> "A peer SHALL reassemble PAFTP segments in the ascending order of the segment sequence numbers."

**Verification**: For honest peers, ordering is fully specified. For adversarial peers, segments could be reordered by a MitM, but sequence numbers enforce reassembly order. The real issue is injection/replacement (same as PROP_003), not ordering.

**Verified verdict**: **Mostly addressed by spec** — ordering specified for sending, enforced by sequence numbers for reassembly. Re-ordering attack reduces to sequence injection attack (PROP_003).

---

### 4.11. PROP_010 — RESERVED_BITS_ZERO (Defense: Upheld/LOW)

**Defense says**: Sender-only requirement with no receiver validation mandate.

**Spec says** (Section 4.20.2):

> "Unused fields SHALL be set to '0'."

**Verification**:

- **Correct**: This is a sender-side requirement only. No "SHALL reject" or "SHALL validate" on the receiver.
- **Minor**: Covert channel via reserved bits is theoretically possible but extremely low bandwidth and impractical.

**Verified verdict**: **Valid, correctly categorized as LOW.**

---

## 5. Attack Scenario Assessment

### Scenario 1: Smart Home Takeover via Version Downgrade — **OVERSTATED**

- Currently only one PAFTP version exists (v4 = Matter v1.5)
- Even if downgraded, PASE provides separate cryptographic authentication
- Actual risk: DoS (commissioning failure), not home takeover

### Scenario 2: Credential Theft via Cumulative Ack Forgery — **OVERSTATED**

- PASE encrypts commissioning credentials; they don't travel as PAFTP plaintext
- Actual risk: Failed commissioning with false success indication (DoS-class)
- False success indication IS a valid concern if implementation trusts transport-layer acks

### Scenario 3: Buffer Overflow via Window Manipulation — **PARTIALLY REALISTIC**

- DoS via window desync is feasible
- Code execution depends on implementation quality (not a spec-level guarantee)
- Most realistic for resource-constrained devices with fixed buffers

### Scenario 4: Supply Chain via Sequence Injection — **OVERSTATED**

- Injected payloads would fail Matter message authentication
- Sequence injection causes DoS (session closure), not persistent backdoors

### Scenario 5: Apartment DoS via Zombie Sessions — **REALISTIC** ✓

- Most credible scenario in the entire document
- Exploits pre-security transport — no cryptography needed
- Device connection slot exhaustion is a real threat
- Low skill, no special equipment, high impact

### Scenario 6: Data Corruption via Out-of-Order Delivery — **OVERSTATED**

- Firmware updates have independent integrity checks (signatures, checksums)
- PAFTP reassembly uses sequence numbers for ordering
- Sequence number wraparound edge case is theoretical

### Scenario 7: Enterprise Network Reconnaissance — **OVERSTATED**

- Wi-Fi credentials transmitted via PASE-encrypted session, not PAFTP plaintext
- Requires chaining multiple hypothetical vulnerabilities

### Scenario 8: Medical Device Attack — **ACKNOWLEDGED AS LOW**

- Defense already notes this depends on implementation failure
- Based on the fabricated S52 quote, making the analysis unreliable

---

## 6. Revised Assessment

### True Severity Distribution

| Category                                            | Count | Properties                             |
| --------------------------------------------------- | ----- | -------------------------------------- |
| **Valid DoS vulnerabilities**                       | 4     | PROP_004, PROP_005, PROP_018, PROP_022 |
| **Valid but overstated** (DoS, not data compromise) | 3     | PROP_001, PROP_003, PROP_014           |
| **Valid but by-design** (matches BTP)               | 2     | PROP_007, PROP_012                     |
| **Valid minor**                                     | 1     | PROP_010                               |
| **Invalid disproval**                               | 1     | PROP_008                               |

### Core Valid Finding

The PAFTP specification is vulnerable to **Denial of Service attacks at the transport layer** because:

1. Acknowledgements are not authenticated → forged acks cause data loss and window desync
2. Device lacks handshake request timeout → zombie session accumulation
3. Sessions can be disrupted by injecting packets with correct sequence numbers

These are genuine transport-layer DoS concerns. However, they do **NOT** escalate to data compromise because PASE provides end-to-end cryptographic protection above PAFTP.

### Core Invalid Finding

The "Missing Security Dependency Specification" root cause is **architecturally misleading**:

- PAFTP cannot reference PASE because PASE runs on top of PAFTP
- BTP (Section 4.19) has identical design with zero security cross-references
- This is a deliberate, consistent design pattern in Matter, not a specification oversight

---

## 7. Confidence Assessment

| Aspect                        | Confidence                                                 |
| ----------------------------- | ---------------------------------------------------------- |
| PROP_008 quote fabrication    | **99%** — searched all available sources                   |
| BTP parallel design pattern   | **99%** — confirmed via direct spec text comparison        |
| PASE architectural layering   | **95%** — confirmed via spec pages 88 and 161              |
| DoS vulnerability validity    | **90%** — consistent with transport protocol threat models |
| Data compromise overstatement | **85%** — depends on PASE implementation correctness       |

---

## 8. Methodology

1. **Full-text search** of `4.20.md` (796 lines) for all quoted text in DEFENSE_FINAL_SUMMARY.md
2. **Graph RAG hybrid search** across 571 chunks of `core_spec` (v1.4) for key phrases
3. **Cross-reference** with `paftp_analysis_notes.md` SHALL requirement numbering
4. **Parallel analysis** of BTP (Section 4.19) for design pattern consistency
5. **Architectural analysis** of Matter protocol stack layering (PAFTP → PASE → Application)
6. **Statement-by-statement verification** of each defense claim against actual spec text

---

_Report generated from direct specification text analysis. All quotes verified against source documents._

---

---

# Part 2 — Verified New Vulnerabilities for Formal Verification

**Analysis Date**: February 15, 2026 (revised after deep re-verification)  
**Scope**: Deep independent analysis of Section 4.20 (PAFTP) for vulnerabilities NOT covered by existing PROP_001–PROP_050  
**Methodology**: Each candidate vulnerability cross-referenced against actual spec text (`4.20.md`), BTP equivalent (Section 4.19, `core_spec.md` pages 220–231), FSM model (`paftp_fsm.json`), and graph RAG index (`core_spec`, 571 chunks)

### Verification Results

The original analysis identified 8 candidate vulnerabilities (NEW-001 through NEW-008). After deep re-verification against the actual specification text and BTP parallel analysis, **only 3 are proven**. The other 5 were removed as unproven, overstated, or implementation concerns rather than protocol-level specification vulnerabilities.

| Original ID | Name                                        | Verdict        | Reason                                                                                   |
| ----------- | ------------------------------------------- | -------------- | ---------------------------------------------------------------------------------------- |
| NEW-001     | Figure 35 DeviceState Non-Determinism       | **PROVEN** ✅  | Confirmed via spec mermaid + BTP comparison                                              |
| NEW-002     | CommissionerState → BothTicking Unreachable | **REMOVED** ❌ | Diagram shorthand for compound event; not exploitable                                    |
| NEW-003     | Missing Commissioner Response Validation    | **PROVEN** ✅  | Confirmed zero SHALL requirements; BTP has same gap                                      |
| NEW-004     | Handshake Injection in Connected State      | **REMOVED** ❌ | Standard underspecification; implicit rejection in state machines                        |
| NEW-005     | Unknown Management Opcode Handling          | **REMOVED** ❌ | Standard implicit behavior; not a protocol-level vulnerability                           |
| NEW-006     | Device-Side Handshake Wait Timeout          | **PROVEN** ✅  | Confirmed via Figure 34; BTP has at least partial coverage                               |
| NEW-007     | Invalid Control Flag Combinations           | **REMOVED** ❌ | Minor completeness issue; partially handled by reassembly checks (S41)                   |
| NEW-008     | Session Re-Establishment State Leakage      | **REMOVED** ❌ | Figure 33 always closes WFA-USD; text/diagram contradiction resolved in favor of diagram |

---

## NEW-001: Figure 35 State Machine Non-Determinism (DeviceState)

**Category**: State Machine  
**Severity**: CRITICAL  
**Formally Verifiable**: Yes  
**Verification Status**: **PROVEN** — confirmed against both PAFTP and BTP spec text

### Specification Evidence

PAFTP Figure 35 (from `4.20.md`, lines 708–741) defines two transitions from `DeviceState` with **identical trigger labels**:

```
DeviceState --> DeviceState: stand alone ack-tx\nOR piggyback ack-tx\non msg segment
DeviceState --> Closing: standalone ack-tx\nOR piggyback ack-tx\non msg segment
```

The only difference is "stand alone" (two words, self-loop) vs "standalone" (one word, Closing path) — a formatting inconsistency, not a semantic distinction.

### BTP Cross-Reference (Critical Finding)

BTP Figure 28 (`core_spec.md`, lines 9988–10018, page 230) has the **same trigger ambiguity** but routes to **BothTicking**, not Closing:

```
server_state_post_handshake --> server_state_post_handshake : stand alone ack-tx<br/>OR piggyback ack-tx<br/>on msg segment
server_state_post_handshake --> ack_rx_timer_ticking : standalone ack-tx<br/>OR piggyback ack-tx<br/>on msg segment
```

| Protocol         | Self-loop trigger           | Second transition with SAME trigger | Destination           |
| ---------------- | --------------------------- | ----------------------------------- | --------------------- |
| **BTP (v1.4)**   | server_state → server_state | server_state → **BothTicking**      | Active state ✓        |
| **PAFTP (v1.5)** | DeviceState → DeviceState   | DeviceState → **Closing**           | Session termination ✗ |

BTP also has the non-deterministic labels, but PAFTP's version is **more severe** because one resolution path terminates the session. This difference suggests the PAFTP `DeviceState → Closing` label is a spec diagram error — likely a copy-paste artifact where BTP's BothTicking destination was incorrectly changed to Closing.

### Why This Is Proven

1. **Direct spec text match**: The exact mermaid source code in `4.20.md` contains both transitions with identical semantic triggers
2. **BTP divergence**: BTP does NOT have a Closing path with the "ack-tx" trigger — the PAFTP version is unique and likely erroneous
3. **No guard condition in spec**: The specification provides zero disambiguation between the two paths
4. **FSM JSON had to fabricate a resolution**: The FSM model's T_PE_15 maps this transition to "invalid_ack_received" (Section 4.20.3.8 S71), which is a text-based requirement, NOT what the Figure 35 label actually says

### Impact

- **Formal verification blocker**: Model checkers will flag this as non-deterministic, blocking all safety/liveness proofs on DeviceState
- **Interoperability risk**: Different implementations will resolve the ambiguity differently — some will terminate sessions when others continue
- **FSM JSON fix applied**: T_PE_15 spec_ref updated to source from S71 text rather than the ambiguous Figure 35 label

### Formal Property

```
∀peer:device, s:session, event:ack_tx ⊢
  state(peer, s) = DeviceState ∧ occurs(event) ==>
  deterministic_next_state(peer, s, event) is uniquely defined
```

### ProVerif Query

```proverif
query s:session, e:event ⊢
  (in_state(DeviceState, s) ∧ event_ack_tx(e, s)) ==>
  (next_state(s) = DeviceState ∨ next_state(s) = Closing)
  ∧ ¬(next_state(s) = DeviceState ∧ next_state(s) = Closing)
```

### Not Covered By

No existing PROP_001–PROP_050 property addresses state machine determinism or transition uniqueness.

---

## NEW-003: Missing Commissioner Validation of Handshake Response Parameters

**Category**: Security  
**Severity**: CRITICAL  
**Formally Verifiable**: Yes  
**Verification Status**: **PROVEN** — confirmed zero Commissioner validation SHALL requirements in both PAFTP and BTP

### Specification Evidence

PAFTP Section 4.20.3.3 (`4.20.md`, lines 451–462) places ALL parameter selection requirements on the **Device**:

> "The Commissionable Device **SHALL** select a window size equal to the minimum of its and the Commissioner's maximum window sizes."  
> "The Commissionable Device **SHALL** select a maximum PAFTP Segment Size... by taking the minimum..."  
> "The Commissionable Device **SHALL** select a PAFTP protocol version that is the newest which it and the Commissioner both support"

There are **zero SHALL requirements** for the Commissioner to validate that the response complies with these rules.

### BTP Cross-Reference (Same Gap)

BTP Section 4.19.4.3 (`core_spec.md`, lines 9700–9710, page 221) has the identical pattern:

> "The server **SHALL** select a window size equal to the minimum of its and the client's maximum window sizes."  
> "Likewise, the server **SHALL** select a maximum BTP Segment Size..."  
> "The server **SHALL** select a BTP protocol version that is the newest which it and the client both support"

Zero client validation requirements in BTP either. This confirms a **systemic design pattern** in Matter transport protocols, not a PAFTP-specific oversight.

### Why This Is Proven

1. **Exhaustive search of Section 4.20.3.3**: No "Commissioner SHALL verify/check/validate" text exists
2. **BTP parallel confirms pattern**: BTP Section 4.19.4.3 has identical gap — all SHALL on server, none on client
3. **FSM JSON gap**: T_CL_04 uses `valid_handshake_response(response)` in guard — this function is **undefined** in the spec
4. **Three distinct attack vectors**: Version injection (undefined behavior), parameter inflation (buffer overflows), parameter deflation (DoS)

### Attack Scenarios

**Version Injection** (most impactful):

1. Malicious Device (or MitM) responds with `selected_version=7` (undefined value)
2. Commissioner accepts and attempts to use protocol v7
3. All subsequent packet parsing uses undefined format → **undefined behavior**

**Parameter Inflation** (DoS):

1. Commissioner sends `max_window=5, max_ssi=350`
2. Malicious Device responds with `selected_window=255, selected_ssi=2000`
3. Commissioner allocates buffers for inflated values → memory exhaustion on constrained Commissioner

**Parameter Deflation** (DoS):

1. MitM modifies response to `selected_window=1`
2. Single-packet-at-a-time throughput → commissioning takes prohibitively long

### Formal Property

```
∀c:commissioner, d:device, resp:handshake_response ⊢
  event receive_handshake_response(c, resp) ==>
  (selected_version(resp) ∈ supported_versions(c)
   ∧ selected_window(resp) ≤ max_window(c)
   ∧ selected_ssi(resp) ≤ supported_ssi(c))
  ∨ event close_session(c, invalid_response)
```

### ProVerif Query

```proverif
query c:principal, v:version, w:int, s:int ⊢
  event accept_response(c, v, w, s) ==>
  (member(v, supported(c)) ∧ w <= max_window(c) ∧ s <= max_ssi(c))
```

### FSM JSON Fix Applied

T_CL_04 annotated with `spec_note` documenting that `valid_handshake_response()` is an undefined function — the spec provides no definition of what constitutes a "valid" handshake response from the Commissioner's perspective.

### Not Covered By

PROP_028 (Minimum_Selection_Window_Size) and PROP_029 (Minimum_Selection_Packet_Size) address the **Device's selection** correctness only. No property addresses the **Commissioner's validation** of received parameters.

---

## NEW-006: Device-Side Handshake Request Wait Timeout Missing

**Category**: Security (DoS)  
**Severity**: HIGH  
**Formally Verifiable**: Yes  
**Verification Status**: **PROVEN** — confirmed via Figure 34 state machine and BTP comparison

### Specification Evidence

PAFTP Figure 34 (`4.20.md`, lines 694–707) defines the Device lifecycle:

```mermaid
Wait_on_capabilities_request --> Prepared_capabilities_response : PAFTP capabilities request received
Prepared_capabilities_response --> Disconnected_advertising : PAFTP connection response timed out
```

There is a timeout from `Prepared_capabilities_response` (after request received, during response preparation), but **NO timeout** from `Wait_on_capabilities_request` (before request arrives).

PAFTP Table 42 defines `PAFTP_CONN_RSP_TIMEOUT` (5 seconds) for the **Commissioner** waiting for a response. No equivalent Device-side constant exists.

### BTP Cross-Reference (Partial Coverage)

BTP Figure 27 (`core_spec.md`, page 229) shows:

```
Disconnected_advertising --> Disconnected_advertising : BTP connect timed out
```

BTP has at least a timeout mechanism from `Disconnected_advertising` before any connection is fully established. Additionally, BLE provides connection supervision timeouts at the L2CAP level — if the Central (client) doesn't communicate, the BLE supervision timeout fires and closes the connection.

PAFTP operates over **WFA-USD (Wi-Fi)**, which does not have BLE's built-in connection supervision timeouts. This makes the Device-side gap in PAFTP **more impactful** than the equivalent gap in BTP.

### Why This Is Proven

1. **Figure 34 explicit**: `Wait_on_capabilities_request` has NO timeout transition — only an inbound trigger (`PAFTP capabilities request received`)
2. **Table 42 explicit**: Only Commissioner-side timeout (`PAFTP_CONN_RSP_TIMEOUT`) defined; no Device-side equivalent
3. **BTP comparison**: BTP has timeout from Disconnected_advertising + BLE supervision timeout as backup; PAFTP has neither
4. **Attack scenario is practical**: Requires only Wi-Fi proximity, no cryptography, no protocol expertise, no special equipment

### Attack Scenario (Zombie Connection Exhaustion)

```
1. Attacker laptop near target IoT device (e.g., smart lock)
2. Device supports max N concurrent WFA-USD connections
3. Attacker establishes N WFA-USD connections:
   → Each enters Wait_on_capabilities_request
   → No PAFTP handshake request sent on any connection
4. All N Device connection slots consumed
5. Device stuck in Wait_on_capabilities_request for ALL slots
6. No PAFTP-level timeout → Device waits indefinitely
7. Legitimate Commissioner cannot connect
8. Device remains blocked until manual power cycle
```

### Impact

This is the **most practically exploitable** new vulnerability because it requires:

- Only Wi-Fi proximity (≈50m outdoors, ≈10m indoors)
- No cryptographic knowledge
- No protocol expertise (establish connections and do nothing)
- No special equipment (any Wi-Fi device)
- Device remains blocked until physical intervention

### Formal Property

```
∀d:device, c:commissioner, t_connect:time ⊢
  event wfa_usd_connected(d, c, t_connect) ==>
  (∃t_req. event receive_handshake_req(d, c, t_req) ∧ (t_req - t_connect ≤ DEVICE_HANDSHAKE_TIMEOUT))
  ∨ (∃t_close. event close_connection(d, c, t_close) ∧ (t_close - t_connect ≤ DEVICE_HANDSHAKE_TIMEOUT))
```

### ProVerif Query

```proverif
query d:principal, c:principal, t:time ⊢
  (event wfa_usd_connect(d, c, t) ∧ ¬event handshake_req(d, c)) ==>
  eventually(event timeout_close(d, c))
```

### FSM JSON Fix Applied

State `DL_Awaiting_Handshake_Request` annotated with `spec_note` documenting the missing timeout. The state has no outbound timeout transition in the FSM model, matching the spec gap.

### Not Covered By

PROP_014 (Handshake_Response_Timeout_Enforcement) covers the Commissioner-side 5-second timeout only. No existing property addresses Device-side handshake request wait timeout.

---

## Removed Vulnerabilities — Rationale

### NEW-002: CommissionerState → BothTicking Unreachable Transition — **REMOVED**

**Reason**: This is a **diagram abstraction**, not a vulnerability. CommissionerState has ack-rx stopped (no outstanding packets), so receiving "ack-rx for most recent segment" is a logical contradiction. However, the FSM JSON (T_PE_11) correctly interprets this as a compound event shorthand: send packet (starts ack-rx → DeviceState) then receive non-final ack (starts ack-tx → BothTicking). BTP Figure 28 does NOT have this transition from client_state, confirming it's a PAFTP diagram simplification. An unreachable transition is dead code in the spec diagram — it cannot be exploited and does not affect protocol security.

### NEW-004: Handshake Injection in Connected State — **REMOVED**

**Reason**: Standard **underspecification pattern** common across protocol specifications. Most transport protocols (TCP, BTP, QUIC) don't explicitly specify behavior for receiving connection-establishment packets during established sessions. In state machine formalism, absence of a transition for an input implies the input is dropped or causes an error — both are safe behaviors. This is an implementation robustness concern (parser should reject H=1 in Connected state) not a protocol-level vulnerability provable through formal verification.

### NEW-005: Unknown Management Opcode Handling — **REMOVED**

**Reason**: Standard **implicit protocol behavior**. Protocols define finite opcode sets; receiving undefined opcodes is expected to result in rejection. PAFTP Table 39 defines one opcode (0x6C). Any conformant implementation's opcode dispatch would have a default rejection path. This is a fuzzing/implementation concern, not a specification-level protocol vulnerability suitable for formal verification.

### NEW-007: Invalid Control Flag Combinations — **REMOVED**

**Reason**: **Partially handled** by existing spec requirements. Section 4.20.3.5 catches "Ending without previous Beginning" (S41) and "Beginning during in-progress transmission" (S42) at the reassembly level. B=1,C=1 combinations are self-contradictory and would be caught by any reasonable parser. This is a minor spec completeness issue, not a security vulnerability — invalid flag packets would either fail reassembly checks or be syntactically unparseable.

### NEW-008: Session Re-Establishment State Leakage — **REMOVED**

**Reason**: **Resolved by state diagram taking precedence over text**. The spec text says "A PAFTP session MAY open and close with no effect on the underlying WFA-USD connection." However, Figure 33 (Commissioner) shows `Connected → Disconnected: Close WFA-USD connection` and T_PE_18 (Closing → Closed) includes `close_wfa_usd_connection()`. The state diagram consistently closes WFA-USD on PAFTP session closure. The "MAY" text is permissive but the diagrams are prescriptive. Since WFA-USD always closes per the diagram, session re-establishment on the same WFA-USD connection is not a reachable scenario.

---

## Summary of Proven New Vulnerabilities

| ID      | Name                                     | Severity     | Category      | BTP Equivalent                                                      |
| ------- | ---------------------------------------- | ------------ | ------------- | ------------------------------------------------------------------- |
| NEW-001 | Figure 35 DeviceState Non-Determinism    | **CRITICAL** | State Machine | BTP has same label ambiguity but routes to BothTicking, not Closing |
| NEW-003 | Missing Commissioner Response Validation | **CRITICAL** | Security      | BTP has identical gap (zero client validation)                      |
| NEW-006 | Device-Side Handshake Wait Timeout       | **HIGH**     | DoS           | BTP has partial coverage via BLE supervision timeout                |

### FSM JSON Fixes Applied

| Fix                                       | Transition/State                              | Change                                                                                                           |
| ----------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| T_PE_15 spec_ref corrected                | `PE_AckRx_Ticking_AckTx_Stopped → PE_Closing` | Removed incorrect Figure 35 reference; sourced from S71 text only; added `spec_note` documenting non-determinism |
| T_CL_04 validation gap documented         | `CL_Awaiting_Response → CL_Connected`         | Added `spec_note` that `valid_handshake_response()` is undefined in spec                                         |
| DL_Awaiting_Handshake_Request timeout gap | `DL_Awaiting_Handshake_Request` state         | Added `spec_note` documenting missing timeout transition                                                         |
| `validation_checklist.known_spec_gaps`    | Top-level                                     | Added array listing all 3 proven gaps with references                                                            |

### Recommended Formal Verification Priority

1. **NEW-001** (CRITICAL) — Must be resolved first. State machine non-determinism blocks all formal verification on DeviceState. Recommended fix: remove `DeviceState → Closing` with "ack-tx" trigger; route error conditions through explicit guard conditions (invalid ack, timeout).
2. **NEW-003** (CRITICAL) — Immediately exploitable by malicious Device or MitM. Recommended fix: add Commissioner SHALL validate selected_version ∈ supported_versions ∧ selected_window ≤ max_window ∧ selected_ssi ≤ max_ssi.
3. **NEW-006** (HIGH) — Most practically exploitable (low skill, no equipment). Recommended fix: add PAFTP_DEVICE_HANDSHAKE_TIMEOUT constant (e.g., 10s) and timeout transition from `Wait_on_capabilities_request → Disconnected_advertising`.

---

_End of Verification Report — Part 2 (Revised)_
