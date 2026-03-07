# Microwave Oven Control Cluster (Section 8.13) — Spec Defense Summary

**Document:** Matter Application Cluster Specification v1.5  
**Cluster:** Microwave Oven Control (0x005F, PICS: MWOCTRL)  
**Referenced sections:** §8.13 (pp. 669–676), §8.12 (Microwave Oven Mode), §1.14 (Operational State)  
**Defense against:** Claims in `8.13_microwave_oven_control_vulnerability_analysis.json`

---

## Overview

Of the 7 claimed violations, **4 are disproved** by explicit specification text and **3 remain valid** spec-level gaps.

| Property ID | Name | Verdict |
|---|---|---|
| PROP_003 | No_Timed_Interaction_Required_For_StartCooking | **DISPROVED** |
| PROP_004 | SetCookingParameters_INVALID_IN_STATE_When_Not_Stopped | VALID |
| PROP_005 | AddMoreTime_INVALID_IN_STATE_When_Not_Running | VALID |
| PROP_019 | AllFieldConstraints_Checked_Before_State_Change | **DISPROVED** |
| PROP_020 | MissingCookMode_Defaults_To_Normal_Mode | **DISPROVED** |
| PROP_028 | No_AddMoreTime_Rate_Limit | VALID |
| PROP_029 | No_CookingStart_Event_Generated | **DISPROVED** |

---

## DISPROVED Claims

---

### PROP_003 — No_Timed_Interaction_Required_For_StartCooking

**Claimed violation:** "Replay of SetCookingParameters starts microwave radiation without user presence."  
**Verdict: DISPROVED**

#### Argument 1 — Matter transport security eliminates replay attacks

A replay attack requires capturing a legitimate command and re-submitting it without re-authentication. Matter's security architecture prevents this at the session layer. All communication is conducted over CASE (Certificate Authenticated Session Establishment) sessions. Each session uses unique, freshly-derived AES-CCM keys. Messages carry monotonically increasing message counters unique to each session. A captured message from session S cannot be replayed in session S+1 (different keys) and is rejected within session S (counter already seen). The "replay" scenario as described is cryptographically infeasible against a conformant Matter implementation.

Timed Interaction in Matter is not a replay-prevention mechanism; it is a staleness guard designed to ensure that buffered commands are not executed long after user intent (e.g., a queued unlock command hitting a door lock minutes after the user walked away). For a microwave oven where the operator explicitly configures and initiates a cook cycle, the operational window is inherently user-controlled and a Timed Interaction guard adds no security benefit beyond what session security already provides.

#### Argument 2 — Operational State cluster mandates attended-operation safety

Section 1.14.6.2 (Stop Command, Operational State Cluster, p. 138):

> "Restart of the device following the receipt of the Stop command **SHALL require attended operation** unless remote start is allowed by the device type and any jurisdiction governing remote operation of the device."

This is a normative SHALL. After any Stop command, re-starting the oven requires physical attended action at the device unless the device type spec and applicable jurisdiction explicitly permit remote start. `SetCookingParameters` with `StartAfterSetting=TRUE` internally invokes the Start path of the Operational State cluster and is subject to this constraint.

#### Argument 3 — Safety mechanism is explicitly provided for unattended starts

Section 1.14.6.3 (Start Command, Operational State Cluster, p. 139):

> "There may be either regulatory or manufacturer-imposed safety and security requirements that first necessitate some specific action at the device before a Start command can be honored. In such instances, a device **SHALL respond with a status code of `CommandInvalidInState`** if a Start command is received prior to the required on-device action."

The spec explicitly acknowledges the unattended-start concern and provides the `CommandInvalidInState` response as the mechanism for devices to enforce it. The concern is documented and addressed; the spec is not silent on it.

---

### PROP_019 — AllFieldConstraints_Checked_Before_State_Change

**Claimed violation:** "Partial updates configure dangerous state (max CookTime) while returning error."  
**Verdict: DISPROVED**

#### Spec text is unambiguous

Section 8.13.6.2.6 (Effect on Receipt, SetCookingParameters Command, p. 673–674):

> "If this command is received and any fields sent with the command do not meet the constraints of any of the associated attributes (i.e. bearing the same name as the field or as described in the field description), the server **SHALL respond with a response of CONSTRAINT\_ERROR and the attributes and state SHALL remain unchanged.**"

The phrase "the attributes and state SHALL remain unchanged" is absolute and applies when **any** field fails constraint validation. The spec mandates an all-or-nothing semantic: either every field passes and all attributes are updated, or any single constraint failure causes the entire command to be rejected with no attribute modifications. Partial updates are not permitted by this language. The scenario of "max CookTime being set while the command returns error" directly contradicts this explicit SHALL.

This is a correct spec requirement that implementations must honour. Any implementation that partially applies fields is non-conformant with Section 8.13.6.2.6.

---

### PROP_020 — MissingCookMode_Defaults_To_Normal_Mode

**Claimed violation:** "Undefined when no Normal-tagged mode exists; implementation-chosen default may be max-power."  
**Verdict: DISPROVED**

#### The 'no Normal mode' scenario is structurally impossible

Section 8.12.5.1 (SupportedModes Attribute, Microwave Oven Mode Cluster, p. 667):

> "**Exactly one entry** in the SupportedModes attribute **SHALL include the Normal mode tag** in the ModeTags field."
>
> "The Normal and Defrost mode tags are mutually exclusive and SHALL NOT both be used together in a mode's ModeTags."

This is a mandatory (SHALL) constraint on the Microwave Oven Mode cluster, which itself must be co-located with the Microwave Oven Control cluster:

Section 8.13 (Introduction, p. 669):

> "The Operational State cluster and the Microwave Oven Mode clusters, or derivatives of those clusters **SHALL appear on the same endpoint as this cluster.**"

A device that lacks exactly one Normal-tagged mode in its SupportedModes is non-conformant with Section 8.12.5.1. The analysis premise ("no Normal-tagged mode exists") describes a spec-violating device. In a spec-compliant device, the Normal mode always exists and is always uniquely identifiable; the default CookMode lookup is fully defined and cannot default to an arbitrary "max-power" mode.

---

### PROP_029 — No_CookingStart_Event_Generated

**Claimed violation:** "Unauthorized cooking start is undetectable via this cluster's event stream."  
**Verdict: DISPROVED**

#### The Operational State cluster's OperationalState attribute provides cooking-start detection

Section 8.13 (Introduction, p. 669) mandates co-location:

> "The Operational State cluster and the Microwave Oven Mode clusters, or derivatives of those clusters **SHALL appear on the same endpoint as this cluster.**"

Section 1.14.5.5 (OperationalState Attribute, Operational State Cluster, p. 135):

> "This attribute specifies the current operational state of a device."

When cooking starts, the `OperationalState` attribute transitions from `Stopped (0x00)` to `Running (0x01)`. In Matter, attributes are subscribable by design. Any client that has established a subscription to the Operational State cluster's `OperationalState` attribute receives an attribute-change report the moment this transition occurs. This is mechanically equivalent to an event notification; it is the standard Matter mechanism for detecting state transitions.

The vulnerability claim is about the **Microwave Oven Control cluster's** event stream specifically. This is factually correct—Section 8.13 defines no events. However, restricting the surveillance surface to only the MWOCTRL cluster misrepresents the system architecture. The spec enforces a single-endpoint co-location model expressly so that state from the Operational State cluster is directly observable alongside cooking parameters. The detection mechanism exists in the mandatory supporting cluster, not in MWOCTRL, and this is by design.

Additionally, Section 1.14.7 (Events, Operational State, p. 140–141) defines:

| ID | Name | Priority | Access | Conformance |
|---|---|---|---|---|
| 0x00 | OperationalError | CRITICAL | V | M |
| 0x01 | OperationCompletion | INFO | V | O |

The `OperationalError` event (mandatory) fires for abnormal conditions. The `OperationCompletion` event (optional) fires at cycle end. Together with the subscribable `OperationalState` attribute, state-change detection is fully supported through the ecosystem of mandated clusters.

---

## VALID Claims (Confirmed Spec Gaps)

---

### PROP_004 — SetCookingParameters_INVALID_IN_STATE_When_Not_Stopped

**Verdict: VALID**

#### Spec uses permissive MAY, not mandatory SHALL

Section 8.13.6.1 (Command Responses Impacted By the Operational State Cluster, p. 671):

> "When the Operational State cluster or a cluster derived from it is included on the same endpoint as this cluster, the server **MAY respond** to commands defined in this cluster with an INVALID\_IN\_STATE response if the server is unable to accept those command due to restrictions imposed by the current operational state of the device or other factors."

"MAY" is permissive, not mandatory. Section 8.13.6.2.6 (Effect on Receipt, p. 673) adds a SHALL:

> "If this command is received while the operational state of the server cannot support the command in that state, the server **SHALL respond with an INVALID\_IN\_STATE response**..."

But the operative clause is "**cannot support the command in that state**." The spec does not define which operational states cannot support `SetCookingParameters`. The MAY in 8.13.6.1 confirms that implementations are permitted to accept `SetCookingParameters` in Running or Paused states. The spec provides no normative rule that blocks it.

#### Attack scenario

An attacker with Operate-level ACL access (or a misbehaving commissioner) sends:
```
SetCookingParameters(PowerSetting=100, StartAfterSetting=FALSE)
```
while the oven is in Running state, mid-cycle at PowerSetting=30. The server, if it does not choose to reject, applies the new PowerSetting immediately and begins cooking at full power—without interrupting the Running state. The spec neither prohibits this nor mandates INVALID\_IN\_STATE in response.

---

### PROP_005 — AddMoreTime_INVALID_IN_STATE_When_Not_Running

**Verdict: VALID**

#### No operational-state restriction defined for AddMoreTime

Section 8.13.6.3.2 (Effect on Receipt, AddMoreTime, p. 674–675) states:

> "If this command is received while the operational state of the server cannot support the command in that state, the server **SHALL respond with an INVALID\_IN\_STATE response.**"

Again, the spec does not define which states "cannot support" `AddMoreTime`. No normative text restricts `AddMoreTime` to only the Running state.

#### The CountdownTime interaction makes Stopped-state behaviour undefined

Section 8.13.6.3.2 (p. 675) further requires:

> "the server **SHALL add** the value of the TimeToAdd field to the value of the **CountdownTime attribute of the Operational State cluster** if that cluster or a derivative is on the same endpoint as this cluster."

Section 1.14.5.3 (CountdownTime Attribute, Operational State, p. 136):

> "A value of **null** represents that there is no time currently defined until operation completion. This MAY happen, for example, because **no operation is in progress**..."
>
> CountdownTime fallback: **null**

In Stopped state, CountdownTime is null. The spec unconditionally says "the server SHALL add" to CountdownTime, but CountdownTime is null when not running. The result of adding an elapsed-s value to null is not specified. The spec creates an obligation it cannot satisfy in Stopped state.

#### Attack scenario

An attacker with Operate-level ACL access, while the oven is Stopped and displaying CookTime=30s, sends:
```
AddMoreTime(TimeToAdd=86370)   // repeated or single near-max call
```
The spec allows acceptance. CookTime is inflated to 86400 s (24 hours). The next time the oven owner presses Start (physically), the oven cooks for up to 24 hours without any indication that CookTime was remotely modified. The attacker uses legitimate Stopped-state access to pre-configure a dangerous cook duration.

---

### PROP_028 — No_AddMoreTime_Rate_Limit

**Verdict: VALID**

#### No rate limiting mechanism is defined

The spec defines no rate-limiting mechanism for `AddMoreTime`. Section 8.13.6.3.2 imposes one bound: "if the sum of the value of the TimeToAdd field and the current value of the CookTime attribute is greater than the MaxCookTime attribute, the server SHALL respond with a response of CONSTRAINT\_ERROR." This is a per-call ceiling check, not a frequency or cumulative-rate limit.

A client holding Operate privilege and making rapid successive calls can escalate CookTime from any starting value to the MaxCookTime ceiling (up to 86400 s per §8.13.5.2) through a series of individually-valid calls, each of which satisfies the per-call constraint.

#### Attack scenario

CookTime=30s. MaxCookTime=86400s. Attacker sends AddMoreTime(TimeToAdd=3600) twenty-four times in rapid succession. Each call is individually valid (3600 + current CookTime ≤ MaxCookTime at each step). CookTime reaches 86400 s. No spec mechanism prevents this sequence. If the oven is Running during this attack, the cook cycle extends to 24 hours without operator interaction, creating a sustained microwave-radiation and fire-risk scenario.

---

## Summary Table

| Property | Claim | Verdict | Key Spec Reference |
|---|---|---|---|
| PROP_003 | Replay enables unauthorized cooking start | **DISPROVED** | Matter transport (message counters + CASE); §1.14.6.2 attended-operation; §1.14.6.3 safety mechanism |
| PROP_004 | SetCookingParameters must be rejected when not Stopped | **VALID** | §8.13.6.1 "MAY" (not SHALL); §8.13.6.2.6 does not define which states block the command |
| PROP_005 | AddMoreTime must be rejected when not Running | **VALID** | §8.13.6.3.2 no state restriction; §1.14.5.3 CountdownTime is null in Stopped state — SHALL add to null is undefined |
| PROP_019 | Partial field updates possible on constraint error | **DISPROVED** | §8.13.6.2.6: "SHALL respond with CONSTRAINT\_ERROR and the **attributes and state SHALL remain unchanged**" |
| PROP_020 | Missing CookMode default undefined if no Normal mode exists | **DISPROVED** | §8.12.5.1: "Exactly one entry in the SupportedModes attribute SHALL include the Normal mode tag" |
| PROP_028 | No rate limit on AddMoreTime allows CookTime escalation to max | **VALID** | §8.13.6.3.2 only checks per-call ceiling, no frequency or cumulative limit |
| PROP_029 | Cooking start is undetectable in this cluster's event stream | **DISPROVED** | §8.13 mandates co-located Operational State; §1.14.5.5 OperationalState attribute is subscribable (Stopped→Running is detectable); §1.14.7 OperationalError event (M) |
