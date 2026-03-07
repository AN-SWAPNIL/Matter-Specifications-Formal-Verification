# Energy EVSE Cluster (9.3) — Vulnerability Defense Summary

**Specification:** Matter 1.5 Application Cluster Specification, Section 9.3 (Pages 716–742)  
**Cluster ID:** 0x0099  
**Defense Role:** Spec owner defending the specification against vulnerability claims  
**Source analysis:** `9.3_energy_evse_vulnerability_analysis.json`

---

## Overview

Seven properties were marked as VIOLATED in the vulnerability analysis. This document examines each claim against the exact specification text. Three claims are **DISPROVED** because the spec already addresses the concern. Two claims are **DISPROVED** because the vulnerabilities are impossible at the Matter protocol level by spec design. Two claims are **CONFIRMED VALID** as genuine gaps in the specification.

| Property ID | Property Name | Original Verdict | Defense Verdict |
|---|---|---|---|
| PROP_EVSE_001 | All_Commands_Require_Timed_Invoke | VIOLATED | **DISPROVED** |
| PROP_EVSE_007 | Physical_Safety_Lockout_Before_Remote_Enable | VIOLATED | **DISPROVED** |
| PROP_EVSE_008 | GFCI_CCID_Faults_Require_Physical_Clearance | VIOLATED | **DISPROVED** |
| PROP_EVSE_011 | Diagnostics_DoS_Via_Unbounded_Duration | VIOLATED | **CONFIRMED VALID** |
| PROP_EVSE_031 | RandomizationDelayWindow_Grid_Demand_Management | VIOLATED | **DISPROVED** |
| PROP_EVSE_035 | RFID_Authorization_External_Dependency | VIOLATED | **DISPROVED** |
| PROP_EVSE_036 | Time_Synchronization_Dependency_For_Epoch_Attributes | VIOLATED | **CONFIRMED VALID** |

---

## PROP_EVSE_001 — All_Commands_Require_Timed_Invoke

**Original claim:** All EVSE commands lack Timed Invoke enforcement; the FSM model sets `timed_required: false` for all commands, enabling replay and injection attacks.

### Defense: DISPROVED

**The claim confuses a modeling error with a specification gap. The spec is explicit and correct.**

The Commands table in Section 9.3.9 lists all seven EVSE commands with access `"O T"`. The `T` flag is the Matter access column notation for mandatory Timed Invoke per the Matter Core Specification (Section 8.7). Every single command row—without exception—carries this flag:

> "| 0x01 | Disable | client → server | Y | **O T** | M |"  
> "| 0x02 | EnableCharging | client → server | Y | **O T** | M |"  
> "| 0x03 | EnableDischarging | client → server | Y | **O T** | V2X |"  
> "| 0x04 | StartDiagnostics | client → server | Y | **O T** | O |"  
> "| 0x05 | SetTargets | client → server | Y | **O T** | PREF |"  
> "| 0x06 | GetTargets | client → server | Y | **O T** | PREF |"  
> "| 0x07 | ClearTargets | client → server | Y | **O T** | PREF |"  
> — Section 9.3.9 Commands Table

The vulnerability does not exist in the specification. The FSM extraction model that was built from the spec failed to translate the `T` access flag into `timed_required: true` guard conditions. That is a defect in the FSM model artifact, not in the specification document. The spec is unambiguous: all EVSE commands require Timed Invoke. Any server that does not enforce Timed Invoke is non-conformant with this explicit requirement.

**The claim targets the FSM model, not the spec. The spec correctly mandates Timed Invoke for all commands.**

---

## PROP_EVSE_007 — Physical_Safety_Lockout_Before_Remote_Enable

**Original claim:** The spec uses `MAY` for the physical safety lockout, making it optional; an implementation without the lockout is spec-compliant and may allow charging to begin before hardware safety interlocks are confirmed.

### Defense: DISPROVED

**The physical safety is not delegated to Matter—it is enforced by the hardware protocol the cluster is built upon. Matter is a software control layer that sits on top of mandatory hardware safety protocols.**

The spec's opening paragraph for Section 9.3 states the cluster's foundational hardware assumption:

> "The cluster generically **assumes** a signaling protocol (J1772 in NA and IEC61851 in Europe and Asia) between the EVSE and Electric Vehicle (EV) that utilizes a **pilot signal to manage the states of the charging process**."  
> — Section 9.3, Introductory paragraph

J1772 (SAE J1772) and IEC 61851-1 define a mandatory state machine that is enforced entirely in hardware through the Control Pilot signal. This hardware protocol requires the EV to signal readiness (State B → State C transition) before the EVSE may close the charging contactors. The EVSE hardware cannot advance to State C unless the cable, ground, and vehicle readiness are confirmed through the pilot signal voltage levels. This is not optional hardware behavior—it is mandated by SAE J1772, IEC 61851-1, and by electrical certification standards (UL 2594, EN 61851-1) that all compliant EVSEs must pass before deployment.

The spec's reference to a safety mechanism that `"may lockout remote operation until the initial latching conditions have been met"` describes an **additional** software-layer lockout on top of the existing mandatory hardware protocol. The `MAY` applies to this supplementary software mechanism, not to the underlying J1772/IEC61851 hardware state machine which the cluster `"assumes"` is always present and mandatory.

The State attribute itself reflects this hardware protocol:

> "This attribute SHALL indicate the current status of the EVSE. This higher-level status is **partly derived from the signaling protocol** as communicated between the EVSE and the vehicle through the pilot signal."  
> — Section 9.3.8.1

A remote EnableCharging command can transition SupplyState to `ChargingEnabled` in Matter software, but this only tells the EVSE it is permitted to flow current—actual current only flows when the J1772 pilot signal hardware sequence has confirmed physical safety. The Matter cluster does not bypass hardware safety; it coexists with it.

**The physical safety lockout is provided by J1772/IEC61851, which the cluster explicitly assumes as mandatory infrastructure. The Matter cluster is a software authorization layer on top of this hardware safety system, not a replacement for it.**

---

## PROP_EVSE_008 — GFCI_CCID_Faults_Require_Physical_Clearance

**Original claim:** The spec allows software-only remote fault reset for GFCI/CCID faults; a spec-compliant implementation can clear these faults via Matter without physical operator intervention, enabling charging through an unresolved ground fault.

### Defense: DISPROVED

**Remote software fault clearance via Matter is structurally impossible. The `FaultState` attribute is read-only, and the spec explicitly localizes fault clearance to the device hardware.**

First, the attribute access model makes remote fault clearance via Matter impossible. The attributes table (Section 9.3.8) defines FaultState (0x0002) with access `"R V"` — Read, View. There is no write access. No Matter command accepts FaultState as a writable parameter. There is no Matter command that resets, clears, or modifies FaultState in any form. A remote attacker with Operate privilege cannot write to FaultState through any path the spec defines.

Second, the spec explicitly defines where and how fault clearance occurs:

> "**It is assumed that the fault will be cleared locally on the EVSE device.** When all faults have been cleared, the EVSE device SHALL set the FaultState attribute to NoError and the SupplyState attribute SHALL be set back to its previous state."  
> — Section 9.3.10.5 (Fault Event)

The spec does not say "a controller may clear faults" or "a command may reset faults." It says the fault is cleared **locally on the EVSE device**, and only then does the **device itself** set FaultState to NoError. This is hardware-initiated clearance, not software-commanded clearance.

Third, the introductory text acknowledges the physical clearance requirement explicitly:

> "Some of the fault conditions defined in SAE J1772, such as Ground-Fault Circuit Interrupter (GFCI) or Charging Circuit Interrupting Device (CCID), **may require clearing by an operator by, for example, pressing a button on the equipment or breaker panel.**"  
> — Section 9.3 Introduction

The vulnerability analysis used `MAY` to argue this clearance is optional. But this sentence describes GFCI/CCID hardware behavior—hardware that may auto-reset vs. hardware that requires manual reset—not a softening of Matter requirements. Matter does not define how GFCI hardware resets; it acknowledges the reality that different GFCI hardware implementations behave differently. The spec does not need to mandate physical clearance because, by design, FaultState can only change when the **device hardware detects** the fault condition is resolved.

The attack scenario in the analysis—"implementation with software-only fault reset path clears FaultState remotely (e.g., via proprietary API or implementation bug)"—explicitly requires a proprietary API or implementation bug. This is an implementation quality failure, not a specification gap. A proprietary API that writes to a read-only attribute is non-conformant by definition. The spec cannot guard against implementation bugs in general.

**FaultState is read-only by specification; fault clearance is localized to the EVSE device hardware by explicit spec text; remote software-only fault clearance via Matter protocol is impossible by design.**

---

## PROP_EVSE_011 — Diagnostics_DoS_Via_Unbounded_Duration

**Original claim:** StartDiagnostics has no maximum duration; an Operate-level attacker can hold the EVSE in DisabledDiagnostics indefinitely, preventing all charging.

### Defense: CONFIRMED VALID

**This vulnerability is genuine. The spec creates a unique Denial-of-Service primitive with no remediation path within the cluster.**

The StartDiagnostics spec text is:

> "The diagnostics are **at the discretion of the manufacturer** and usually include internal checks. Upon completion of the diagnostics, the EVSE SHALL restore SupplyState to the Disabled state."  
> — Section 9.3.9.4.1

"At the discretion of the manufacturer" with no upper bound constraint is a genuine specification gap. Unlike Disable(), which can be reversed by any Operate-level actor calling EnableCharging, diagnostics mode cannot be exited by any external command. EnableCharging and EnableDischarging both reject during diagnostics:

> "If there is currently an error present on the EVSE, or **Diagnostics are currently active**, then the command SHALL be ignored and a response with a status of FAILURE SHALL be returned."  
> — Section 9.3.9.2.4 (EnableCharging) and Section 9.3.9.3.3 (EnableDischarging)

This creates a unique asymmetry: StartDiagnostics (Operate privilege) puts the EVSE into a state from which no Operate-level command can recover it. Only the manufacturer's internal diagnostic completion event can exit the state. There is no CancelDiagnostics command, no diagnostic timeout attribute, and no higher-privilege override command.

**Attack Scenario:**
1. EV arrives at 10 PM. SupplyState is Disabled (EV plugged in, no authorization yet).
2. Attacker with Operate privilege sends StartDiagnostics (requires "O T" — Timed Invoke plus Operate).
3. EVSE transitions to SupplyState = DisabledDiagnostics. Legitimate EMS sends EnableCharging; receives FAILURE.
4. Manufacturer diagnostics run for an unbounded period (no spec maximum).
5. When diagnostics complete and SupplyState returns to Disabled, attacker immediately sends a new StartDiagnostics.
6. No Matter-level mechanism breaks this cycle. EV leaves uncharged.

The prerequisite (SupplyState must be Disabled before StartDiagnostics) limits the attack window but does not eliminate it—an attacker who is fast enough after any Disable event or immediately after EV plugin (before EMS authorization) can exploit this window.

**The spec assigns the same privilege level (Operate + Timed) to StartDiagnostics as to EnableCharging, creates a state that blocks EnableCharging, and defines no maximum duration or cancellation mechanism. This is VALID.**

---

## PROP_EVSE_031 — RandomizationDelayWindow_Grid_Demand_Management

**Original claim:** RandomizationDelayWindow can be set to 0 (no spec minimum), disabling grid demand management for entire fleets and enabling demand surge attacks.

### Defense: DISPROVED

**The spec correctly scopes market-regulatory requirements to certification bodies rather than protocol specifications. The cluster provides the mechanism, a market-appropriate default, and appropriate access controls.**

The spec describes RandomizationDelayWindow as:

> "This is a feature that is **mandated in some markets** (such as UK) where the EVSE should by default randomize its start time within the randomization window. **By default in the UK this should be 600s.**"  
> — Section 9.3.8.11

The spec explicitly acknowledges this is a **market-specific** mandate. The UK, for example, enforces this through the UK Smart Meter Technical Specifications (SMETS) and EVSE product certification against BS EN 62955. Not all markets mandate this requirement. An EVSE deployed in a market without this mandate may legitimately set RandomizationDelayWindow to any value including 0. Making a non-zero minimum globally mandatory would incorrectly apply UK-specific grid management requirements to all international deployments.

The spec protects against casual misconfiguration through three mechanisms:
1. **Sensible default:** The default fallback value is 600 seconds — the UK-required value.
2. **Elevated access:** RandomizationDelayWindow has access `"RW VM"` — Manage privilege required for writes. This is not accessible to Operate-level controllers like a normal EMS or user app.
3. **Max constraint:** A max of 86400 seconds prevents setting an absurdly large window.

The attack scenario requires a Manage-level actor controlling thousands of EVSEs — a compromised fleet management system. At that level of compromise, the attacker can cause far more severe disruptions (e.g., Disable all EVSEs permanently, rewrite all charging schedules). Setting RandomizationDelayWindow = 0 is not a meaningful escalation of capability for a Manage-level fleet attacker.

Market-specific electrical grid requirements (SMETS, network code requirements, DNSP technical standards) are enforced through product certification, regulatory compliance checks, and grid code compliance — not through the Matter cluster specification. This is the same model used for electrical safety ratings, which are enforced by UL/CE certification rather than the Matter protocol spec.

**The spec has the right design: provide the mechanism with a sensible default, protect with Manage privilege, and Leave market-specific minimums to regulatory certification. This is not a spec gap.**

---

## PROP_EVSE_035 — RFID_Authorization_External_Dependency

**Original claim:** RFID authorization is unspecified at the cluster level; a rogue Operate-level subscriber can race the legitimate authorization system by responding to RFID events faster, enabling unauthorized charging.

### Defense: DISPROVED

**The scope exclusion is a deliberate and explicitly stated design decision. The race condition attack introduces no additional attack surface beyond what any Operate-level actor already possesses.**

The spec states explicitly:

> "**The lookup and authorization of RFID UID is outside the scope of this cluster.** An RFID event can be generated when a user taps an RFID card onto the RFID reader. The event must be subscribed to by the EVSE Management cluster client. **This client may use this to enable the EV to charge or discharge.**"  
> — Section 9.3.4.4

This is not an omission — it is a named scope exclusion. RFID UID authorization requires lookup against an identity database (charging accounts, vehicle registrations, backend authorization systems) that is outside any EVSE hardware cluster's operational scope. The design intentionally delegates this to the external management system which has the context to perform proper authorization.

The race condition attack requires the attacker to already have **Operate privilege** on the EVSE Matter endpoint. An attacker with Operate privilege can send EnableCharging directly, at any time, on any PluggedIn state, without waiting for any RFID event. The RFID event subscription does not gate or restrict EnableCharging access — it is an informational event that a legitimate controller uses to decide whether to enable charging. A malicious controller with Operate privilege does not need to intercept RFID events to authorize charging. It can call EnableCharging immediately upon EV plugging in, regardless of RFID.

The RFID feature therefore introduces zero additional attack surface for an Operate-level attacker. The relevant security boundary is Operate privilege commissioning, which is governed by Matter's commissioning and ACL security model — not by RFID authorization logic.

The RFID event access is `"V"` (View), which means subscriptions are available to any View-level actor. This is appropriate — event visibility is informational and does not grant operational capability. The capability to act on the event (EnableCharging) requires Operate privilege, which is a separate, controlled access level.

**The scope exclusion is correct by design. RFID introduces no new attack vectors beyond Operate-level access. The vulnerability claim confuses an authorization design pattern with a protocol security gap.**

---

## PROP_EVSE_036 — Time_Synchronization_Dependency_For_Epoch_Attributes

**Original claim:** The EVSE depends on external time for ChargingEnabledUntil/DischargingEnabledUntil expiry enforcement; time manipulation at the Time Synchronization cluster or NTP layer can extend or prematurely terminate charging sessions.

### Defense: CONFIRMED VALID

**The spec does not mandate time source integrity. It allows implementations that are vulnerable to time manipulation and provides no fallback enforcement mechanism when time is compromised.**

The spec defines the time dependency:

> "The server side of this cluster **SHALL depend on setting time** from another device or using a real-time clock. This can either use a **built-in real-time clock or non-Matter time source**, or can be derived using the Time Synchronization cluster."  
> — Section 9.3.5 Dependencies

The spec allows a hardware RTC as an option — a hardware RTC is immune to network-level time manipulation. However, the spec does not:
- Define any quality requirement for the time source
- Mandate that EVSE implementations prefer hardware RTC for security-critical timers
- Specify fallback behavior when time source becomes unavailable or manipulated mid-session
- Require the implementation to detect time rollback or time jump anomalies
- Cross-reference the Time Synchronization cluster's own access controls as a security mitigation

The critical attributes that depend on accurate time are:
- `ChargingEnabledUntil` (0x0003): EVSE stops charging when `current_time >= ChargingEnabledUntil`
- `DischargingEnabledUntil` (0x0004): EVSE stops discharging when `current_time >= DischargingEnabledUntil`

A `SHALL stop` expiry check based on `current_time` from an unvalidated external source is directly exploitable through time manipulation. The spec's permission to use the Time Synchronization cluster as the sole time source, without mandating integrity checks on that source, means a class of fully spec-compliant implementations is vulnerable.

**Attack Scenario:**
1. EMS programs: `EnableCharging` with `ChargingEnabledUntil = epoch_02:00`.
2. Attacker with Administer privilege on the Time Synchronization cluster (or network-level NTP control) rolls back the EVSE system clock by 4 hours.
3. At real-world 02:00, EVSE clock reads 22:00. Expiry check: `22:00 < 02:00` evaluates correctly in wall-clock terms but the session does not expire because the EVSE measures absolute epoch seconds against a manipulated clock.
4. Charging continues indefinitely beyond the authorized 02:00 window.

The spec provides the *option* of a secure path (hardware RTC) but says nothing that mandates it or warns that network-based time sync introduces time-manipulation risk for these critical expiry checks. The vulnerability is fully within the spectrum of spec-compliant implementations.

**The spec creates a SHALL dependency on an untrusted time source without requiring integrity verification, fallback behavior, or minimum time source quality. This is a genuine specification gap.**

---

## Summary Table

| Property | Defense Verdict | Core Reason |
|---|---|---|
| PROP_EVSE_001 | **DISPROVED** | Spec mandates "O T" (Timed Invoke) for all 7 commands in the Commands table (Section 9.3.9). The FSM model failed to capture this; the spec did not. |
| PROP_EVSE_007 | **DISPROVED** | Physical safety is enforced by J1772/IEC61851 pilot signal hardware protocol which Section 9.3 explicitly assumes as mandatory EVSE infrastructure. Matter is a control layer above hardware safety, not a replacement. |
| PROP_EVSE_008 | **DISPROVED** | FaultState (0x0002) is Read-Only (R V). No Matter command can write it. Section 9.3.10.5 states faults "will be cleared locally on the EVSE device" — clearance is hardware-local, not remotely commanded. |
| PROP_EVSE_011 | **CONFIRMED VALID** | StartDiagnostics has no maximum duration ("at the discretion of the manufacturer"); it cannot be cancelled or overridden by any Matter command; EnableCharging is rejected during diagnostics; Operate-level actors can exploit this window for DoS. |
| PROP_EVSE_031 | **DISPROVED** | Market-specific grid requirements are intentionally delegated to regulatory certification. The spec provides a sensible default (600s), Manage-level write protection, and explicit acknowledgment of market mandates. |
| PROP_EVSE_035 | **DISPROVED** | RFID authorization is explicitly scoped out. A rogue Operate-level subscriber race requires capability that already allows direct EnableCharging without RFID involvement — no new attack surface. |
| PROP_EVSE_036 | **CONFIRMED VALID** | The spec allows network-time-only implementations without mandating time source integrity, rollback detection, or fallback behavior for ChargingEnabledUntil/DischargingEnabledUntil expiry enforcement. |

---

## Specification References

| Section | Title | Relevance |
|---|---|---|
| 9.3 (intro) | Energy EVSE Cluster overview | J1772/IEC61851 hardware protocol assumption; GFCI/CCID acknowledgment |
| 9.3.4.4 | RFID Feature | Explicit scope exclusion of RFID authorization |
| 9.3.5 | Dependencies | Time source dependency definition |
| 9.3.8 (attributes table) | Attributes | FaultState read-only (R V); RandomizationDelayWindow max constraint |
| 9.3.8.1 | State Attribute | Pilot-signal-derived state |
| 9.3.8.11 | RandomizationDelayWindow | Market mandate acknowledgment; 600s default |
| 9.3.9 (commands table) | Commands | "O T" access for all 7 commands |
| 9.3.9.2.4 | EnableCharging Effect on Receipt | Diagnostics-active rejection |
| 9.3.9.3.3 | EnableDischarging Effect on Receipt | Diagnostics-active rejection |
| 9.3.9.4.1 | StartDiagnostics Effect on Receipt | "At the discretion of the manufacturer"; no max duration |
| 9.3.10.5 | Fault Event | "Cleared locally on the EVSE device" — hardware-local clearance |
