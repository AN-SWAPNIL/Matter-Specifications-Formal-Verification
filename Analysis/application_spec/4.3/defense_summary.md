# Thermostat Cluster — Specification Defense Summary

**Cluster**: Thermostat (0x0201) · PICS Code: TSTAT  
**Specification**: Matter 1.5 Application Cluster Specification, Section 4.3, Pages 327–373  
**Analyzed Claims**: thermostat_vulnerability_analysis.json (7 non-HOLDS findings)  
**Defense Date**: 2026-03-07  

---

## Role and Methodology

This document defends the Matter 1.5 Thermostat Cluster specification against the vulnerability and violation claims raised in the FSM security analysis. For every claim, this review:

- Searches the specification for normative text that disproves the claim with exact quotes and section references
- Concedes gaps where the specification is genuinely silent
- Provides an executable attack scenario for every finding that cannot be disproved

There is no middle ground. Each property concludes with a clear verdict: **DISPROVED**, **PARTIALLY DISPROVED**, or **VALID**. The distinction between a spec deficiency and a FSM modeling deficiency is made explicitly throughout.

---

## 1. PROP_TSTAT_001 — EmergencyHeat_Autonomous_Activation

**Original Verdict**: VIOLATED (CRITICAL)  
**Claimed Impact**: Permanent lock in EmergencyHeat (overheating, fire risk) or EmergencyHeat never activates (hypothermia, pipe freezing)

---

### 1.1 Attack Vector 1: EmergencyHeatDelta = 0 → "Permanent EmergencyHeat Lock"

**VERDICT: DISPROVED. The "permanent lock" claim is factually wrong about the specification.**

The specification provides an explicit, normative exit condition in Section 4.3.9.42 (Page 362):

> *"...the Thermostat server SHALL immediately switch to the SystemMode attribute value that provides the highest stage of heating (e.g., emergency heat) and **continue operating in that running state until the OccupiedHeatingSetpoint value is reached**."*

The phrase "until the OccupiedHeatingSetpoint value is reached" is the de-escalation trigger. It is built into the same sentence that mandates entry into EmergencyHeat. The server is normatively required to exit EmergencyHeat when the heating setpoint is achieved.

**The FSM's missing exit transition (Mode_EmergencyHeat → Mode_Heat) is a FSM modeling deficiency, not a specification gap.** The spec is complete.

**Residual — Zero-Delta Rapid Cycling (VALID)**  
With EmergencyHeatDelta = 0, the guard `(OccupiedHeatingSetpoint − LocalTemp) >= 0` is TRUE whenever LocalTemp is at or below setpoint — the ordinary heating condition. EmergencyHeat exits when the setpoint is reached, but normal heat loss immediately re-satisfies the condition. The result is rapid cycling of maximum-stage heating. This IS operationally harmful (equipment wear, energy waste) but is **not permanent lock-in** because the spec-mandated exit condition limits each EmergencyHeat interval. The attack is real; the described mechanism (permanent) is wrong.

**Residual — De-escalation Target State Undefined (Editorial Gap)**  
The spec does not specify which SystemMode the thermostat transitions to after exiting EmergencyHeat. The exit condition is normative; the target state is not. This warrants a clarifying amendment.

---

### 1.2 Attack Vector 2: EmergencyHeatDelta = 255 → EmergencyHeat Never Activates

**VERDICT: VALID. No minimum constraint exists.**

The attribute table (Page 351) for attribute 0x003A (EmergencyHeatDelta):

| Attribute | Type | Constraint | Default | Access |
|---|---|---|---|---|
| EmergencyHeatDelta | UnsignedTemperature | all | 25.5°C | RW VM |

The default is already 25.5°C — the maximum of the UnsignedTemperature type. In a realistic scenario (LocalTemp = −5°C, OccupiedHeatingSetpoint = 20°C), the delta is 25°C, which is less than 25.5°C — emergency heat never activates even during severe cold. The spec provides no minimum value constraint (Constraint column: "all"). A Manage actor can hold the attribute at 25.5°C, permanently suppressing emergency heat activation.

**Access note**: Attribute 0x003A requires Manage privilege (`RW VM`). This attack requires an explicitly granted, trusted Manage actor. It is within the designed trust boundary but is still an exploitable configuration path with no normative lower bound safeguard.

---

### 1.3 Spec Text Anomaly: Trigger Condition References "CoolingSetpoint"

The body text of Section 4.3.9.42 reads:

> *"If the difference between the Calculated Local Temperature and **OccupiedCoolingSetpoint or UnoccupiedCoolingSetpoint** is greater than or equal to the EmergencyHeatDelta..."*

The first sentence of the same section reads:

> *"This attribute SHALL indicate the delta between the Calculated Local Temperature and the **OccupiedHeatingSetpoint or UnoccupiedHeatingSetpoint** attributes..."*

The example on Page 362 confirms HeatingSetpoint:

> `OccupiedHeatingSetpoint − Calculated Local Temperature ≥? EmergencyHeatDelta`  
> `16°C − 10°C ≥? 2°C → TRUE >>> emergency heat mode`

The body text contains an editorial substitution error ("CoolingSetpoint" in lieu of "HeatingSetpoint"). The correct behavior is unambiguous from the first sentence and the example. This is a normative text inconsistency and should be corrected in a future errata.

---

### PROP_TSTAT_001 Overall Defense Verdict: PARTIALLY DISPROVED

| Claim | Defense |
|---|---|
| Permanent lock in EmergencyHeat | **WRONG** — Spec mandates exit when setpoint reached (§4.3.9.42) |
| No de-escalation path in spec | **WRONG** — Exit condition explicit in spec; missing from FSM only |
| EmergencyHeat never activates | **VALID** — No minimum constraint on EmergencyHeatDelta |
| Rapid cycling from zero-delta | **VALID (residual)** — Not permanent, but equipment-damaging cycling occurs |

**Residual valid attack (Manage-level):**  
Write EmergencyHeatDelta = 0 → Every normal heating cycle triggers EmergencyHeat → Max-power heating activates, reaches setpoint, exits, cools slightly, re-triggers → Continuous high-intensity cycling destroys HVAC compressor over time.

---

## 2. PROP_TSTAT_020 — SetpointChangeSource_Attribution_Accurate

**Original Verdict**: VIOLATED (MEDIUM)  
**Claimed Impact**: FSM transition T013 (SetpointRaiseLower Both mode, deadband path) does not update SetpointChangeSource — audit trail corrupted

---

### Defense Analysis

Section 4.3.9.33 (Page 359) defines the attribute:

> *"This attribute SHALL indicate the source of the current active OccupiedCoolingSetpoint or OccupiedHeatingSetpoint (i.e., who or what determined the current setpoint). This attribute enables service providers to determine whether changes to setpoints were initiated due to occupant comfort, scheduled programming or some other source (e.g., electric utility or other service provider). Because automation services MAY initiate frequent setpoint changes, this attribute clearly differentiates the source of setpoint changes made at the thermostat."*

The word **SHALL** creates a normative invariant: the attribute MUST accurately reflect the current setpoint source at all times. Any setpoint change that leaves SetpointChangeSource reflecting a stale source value violates this invariant.

**Examination of the FSM transitions:**

- T010 (SetpointRaiseLower, Heat mode): Sets SetpointChangeSource := External ✓  
- T011 (SetpointRaiseLower, Cool mode): Sets SetpointChangeSource := External ✓  
- T013 (SetpointRaiseLower, Both mode, deadband adjustment): Does **not** update SetpointChangeSource ✗

T013 modifies OccupiedHeatingSetpoint and OccupiedCoolingSetpoint but leaves SetpointChangeSource at its previous value (e.g., `Schedule` from a prior T030 transition). The result: after an external SetpointRaiseLower Both command that triggers the deadband path, the attribute no longer reflects who determined the current setpoint.

**Could this be disproved?** Only if the SetpointRaiseLower Effect on Receipt section (4.3.10.1) explicitly excludes the Both-mode deadband sub-path from the update requirement — an interpretation the spec does not support given the attribute's unconditional SHALL. The attribute description creates an implicit update obligation on every execution path that changes a setpoint.

---

### PROP_TSTAT_020 Defense Verdict: VALID — SPEC TEXTUAL GAP CONFIRMED

The spec's SHALL invariant is clear but the SetpointRaiseLower Effect on Receipt section needed to explicitly enumerate SetpointChangeSource update for every sub-path (including Both-mode deadband). The omission creates implementation ambiguity that the FSM correctly exposed.

**Attack Scenario:**

1. SystemMode = Auto; OccupiedHeatingSetpoint = 20°C, OccupiedCoolingSetpoint = 22°C, MinSetpointDeadBand = 2°C; SetpointChangeSource = `Schedule` (last set by T030 timer transition)
2. Attacker sends `SetpointRaiseLower{Mode=Both, Amount=+30}` via normal Operate session
3. T013 fires: OccupiedCoolingSetpoint raised to 22.3°C; OccupiedHeatingSetpoint adjusted to 20.3°C to maintain deadband
4. SetpointChangeSource remains = `Schedule` (stale — never updated in T013)
5. Building management system reads `SetpointChangeSource = Schedule` and logs the event as a scheduled setpoint change
6. Attacker's external manipulation goes undetected; anomaly detection bound to `External` source never fires
7. Audit records show the schedule adjusted the setpoint during a period when the schedule made no such request

---

## 3. PROP_TSTAT_016 — SetpointLimit_Change_Cascades_To_Setpoints

**Original Verdict**: FSM_INCOMPLETE (MEDIUM)  
**Claimed Impact**: FSM only models cascading for MinHeatSetpointLimit (T038); MaxHeat, MinCool, MaxCool limits have no FSM transitions

---

### Defense Analysis

**VERDICT: FULLY DISPROVED. The specification is complete. The FSM is incomplete.**

Sections 4.3.9.17 through 4.3.9.20 (Pages 356–357) provide identical normative text for all four setpoint limit attributes:

**Section 4.3.9.17 — MinHeatSetpointLimit:**
> *"If an attempt is made to set this attribute to a value which conflicts with setpoint values then those setpoints **SHALL be adjusted by the minimum amount** to permit this attribute to be set to the desired value. If an attempt is made to set this attribute to a value which is not consistent with the constraints and cannot be resolved by modifying setpoints then a response with the status code **CONSTRAINT_ERROR SHALL be returned**."*

**Section 4.3.9.18 — MaxHeatSetpointLimit**: Identical normative text, SHALL cascading mandated.  
**Section 4.3.9.19 — MinCoolSetpointLimit**: Identical normative text, SHALL cascading mandated.  
**Section 4.3.9.20 — MaxCoolSetpointLimit**: Identical normative text, SHALL cascading mandated.

The specification uses SHALL for cascading across all four limit attributes, not just MinHeat. The FSM captured only T038 (MinHeat cascading) and left the other three unmodeled — this is a modeling gap, not a specification gap.

---

### PROP_TSTAT_016 Defense Verdict: FULLY DISPROVED

The specification is correct and complete. Every setpoint limit attribute has explicit SHALL cascading requirements. The claim of a specification gap is false. The FSM model must be extended to add transitions equivalent to T038 for MaxHeat, MinCool, and MaxCool limit writes.

---

## 4. PROP_TSTAT_022 — MinSetpointDeadBand_Write_Silently_Ignored

**Original Verdict**: FSM_INCOMPLETE (MEDIUM)  
**Claimed Impact**: If deadband writes are applied rather than silently ignored, deadband protection is defeated

---

### Defense Analysis

**VERDICT: FULLY DISPROVED. The specification is explicit.**

Section 4.3.9.21 (Page 357):

> *"For backwards compatibility, this attribute is optionally writeable. However **any writes to this attribute SHALL be silently ignored**."*

The normative mandate "SHALL be silently ignored" is unambiguous and covers all writes without exception. There is no conditional path in which a write to MinSetpointDeadBand would be applied in a conformant implementation. Compare with Section 4.3.9.22 (ControlSequenceOfOperation), which enforces the same behavior — correctly modeled in the FSM as T037. The FSM's T038 covers MinHeatSetpointLimit cascading but the analogous MinSetpointDeadBand silent-ignore transition was never added. This is a FSM modeling deficiency.

A non-compliant implementation that applies MinSetpointDeadBand writes would indeed defeat deadband protection and enable simultaneous heating and cooling — but such an implementation is already violating this explicit SHALL, which is a conformance failure, not a specification gap.

---

### PROP_TSTAT_022 Defense Verdict: FULLY DISPROVED

The specification mandates the silent-ignore behavior with SHALL. The FSM is incomplete. The spec is correct.

---

## 5. PROP_TSTAT_012 — SetpointHold_Expiry_Timestamp_Consistency

**Original Verdict**: HOLDS_WITH_GAPS (MEDIUM)  
**Claimed Impact**: Setpoint hold may never auto-clear if autonomous expiry is not mandated by the spec

---

### Defense Analysis

The specification covers setpoint hold in Sections 4.3.9.28–4.3.9.30 (Pages 358–359).

For hold behavior (Section 4.3.9.28):
> *"If hold status is on, the thermostat **SHOULD** maintain the temperature setpoint for the current mode until a system mode change."*  
(SHOULD — advisory, not mandatory)

For timestamp update on hold activation (Section 4.3.9.29):
> *"If this attribute is updated to SetpointHoldOn and the TemperatureSetpointHoldDuration has a non-null value and the SetpointHoldExpiryTimestamp is supported, the server **SHALL** update the SetpointHoldExpiryTimestamp with a value of current UTC timestamp, in seconds, plus the value in TemperatureSetpointHoldDuration multiplied by 60."*

For timestamp clearing on hold deactivation:
> *"If this attribute is updated to SetpointHoldOff and the SetpointHoldExpiryTimestamp is supported, the server **SHALL** set the SetpointHoldExpiryTimestamp to null."*

The SetpointHoldExpiryTimestamp attribute description reads:
> *"If there is a known time when the TemperatureSetpointHold **will** be cleared, this attribute SHALL contain the timestamp..."*

The phrasing "if there is a known time when it **will** be cleared" frames the timestamp as an informational prediction, not as a trigger for autonomous clearing. The spec mandates:

1. **WHAT** to put in the timestamp when hold is turned ON (SHA L — correct)  
2. **WHAT** to put in the timestamp when hold is turned OFF (SHALL — correct)  
3. **NOTHING** about autonomously turning the hold OFF when the timestamp is reached

There is no normative text anywhere in the specification that states: "When the current UTC time reaches SetpointHoldExpiryTimestamp, the server SHALL set TemperatureSetpointHold to SetpointHoldOff."

**CANNOT BE DISPROVED. The gap is real.**

---

### PROP_TSTAT_012 Defense Verdict: VALID SPEC GAP

The specification correctly mandates timestamp population but never mandates the corresponding autonomous clearing action. A fully compliant implementation may correctly set and maintain the expiry timestamp while never acting on it. The use of SHOULD (not SHALL) for hold maintenance further confirms the non-mandatory nature of automatic expiry.

**Attack Scenario** (Manage-level, indefinite hold):

1. Attacker with Manage privilege writes `TemperatureSetpointHold = SetpointHoldOn`, `TemperatureSetpointHoldDuration = 1440` (24-hour maximum duration)
2. Server correctly updates `SetpointHoldExpiryTimestamp = current_time + 86400` (compliant)
3. Server is a minimal compliant implementation — it does not autonomously clear the hold at expiry (no SHALL requires it to do so)
4. 24 hours pass; SetpointHoldExpiryTimestamp is in the past; hold remains SetpointHoldOn
5. All schedule-driven setpoint transitions (T030) are suppressed by the active hold
6. Building management system reads SetpointHoldExpiryTimestamp and assumes the hold will self-clear — it never does
7. Attacker re-writes the hold every 24 hours to keep it active; each write is a valid Manage operation
8. Result: indefinite setpoint freeze blocking all scheduled setpoint changes; energy waste; occupant discomfort; no normative violation by the implementation

---

## 6. PROP_TSTAT_019 — LocalTemperature_LTNE_Null_Always

**Original Verdict**: HOLDS_WITH_GAPS (LOW)  
**Claimed Impact**: Privacy leak — internal temperature exposed when LTNE feature is active if not enforced

---

### Defense Analysis

**VERDICT: FULLY DISPROVED. The specification is normatively complete.**

Section 4.3.9.2 (Page 353):

> *"Otherwise, if the LTNE feature is supported, there is no feedback externally available for the LocalTemperatureCalibration. In that case, **the LocalTemperature attribute SHALL always report null**."*

The normative mandate uses **SHALL** (unconditional) and **always** (without exception). This is the strongest possible combination in RFC 2119 normative language. When the LTNE feature is present, a conformant thermostat server cannot expose the local temperature under any condition.

The original HOLDS_WITH_GAPS verdict was too conservative. There is no gap. The invariant is fully and unambiguously specified.

---

### PROP_TSTAT_019 Defense Verdict: FULLY DISPROVED

The specification is complete on this property. The original verdict should be HOLDS. No attack scenario applies: any implementation that exposes LocalTemperature with LTNE active is already non-conformant, and the specification clearly prohibits it.

---

## 7. PROP_TSTAT_026 — LocalTemperatureCalibration_Clamped_Returns_Success

**Original Verdict**: HOLDS_WITH_GAPS (HIGH)  
**Claimed Impact**: If device supports wide calibration range (type allows ±12.7°C), attacker causes systematic temperature misreporting and unsafe HVAC control

---

### Defense Analysis

Section 4.3.9.12 (Page 354):

> *"If a Thermostat client attempts to write LocalTemperatureCalibration attribute to an unsupported value (e.g., out of the range supported by the Thermostat server), the Thermostat server **SHALL** respond with a status of SUCCESS and set the value of LocalTemperatureCalibration to the upper or lower limit reached."*

> *"NOTE: Prior to revision 8 of this cluster specification the value of this attribute was constrained to a range of −2.5°C to 2.5°C."*

The attribute's access code is `R[W] VM` — **Manage privilege required** for all writes.

**The constraint removal was documented and intentional.** Section 4.3.9.12 uses a NOTE to explicitly acknowledge that the ±2.5°C constraint existed prior to Revision 8 and was removed. This is a deliberate design choice enabling deployment across different HVAC classes — industrial boilers, heat pumps, and specialized environmental control systems may require larger calibration offsets than residential thermostats.

**Clamping is mandated to the device's supported range, not the type's range.** The spec says "out of the range **supported by the Thermostat server**." A device that supports only ±2°C calibration cannot be forced to accept a 10°C offset. The clamping mechanism bounds the maximum impact to what the device manufacturer has physically validated and programmed as the supported range.

**Manage privilege limits the attack surface.** Access `R[W] VM` means a fabric administrator must explicitly grant Manage privilege to any actor before it can write this attribute. This is within the spec's intended trust model.

---

**Where the defense falls short:**  
The specification provides no normative maximum calibration range. A device manufacturer choosing to support ±12.7°C (the full type range) is conformant with the spec. The spec does not say "implementations SHOULD NOT allow calibration offsets greater than X°C." For safety-critical deployment environments, this absence of guidance is a real design gap — even if the access control mitigates it for normal deployments.

---

### PROP_TSTAT_026 Defense Verdict: PARTIALLY DISPROVED

| Claim | Defense |
|---|---|
| HIGH severity | **OVERSTATED** — Requires Manage privilege (trusted actor) |
| Spec has no clamping | **WRONG** — Clamping to device's supported range is explicitly mandated (§4.3.9.12) |
| Constraint removal was accidental | **WRONG** — Explicitly documented with a NOTE in §4.3.9.12 |
| Type range (±12.7°C) implies unlimited exposure | **WRONG** — Clamping is to device's supported range, not the type range |
| No maximum calibration bound in spec | **VALID RESIDUAL** — No normative guidance prevents wide-range implementations |

**Residual valid attack scenario** (Manage-level, device with wide calibration range):

1. Device supports ±10°C calibration range (within spec — no normative maximum to prohibit this)
2. Manage actor writes `LocalTemperatureCalibration = +80` (+8.0°C)
3. Server clamps to its supported maximum (`+100` = +10.0°C) and returns SUCCESS
4. LocalTemperature now consistently reports actual_temperature + 10.0°C (e.g., 32°C when actual = 22°C)
5. Cooling threshold never reached; cooling never activates
6. Space overheats while the thermostat reports acceptable temperatures
7. In a server room or pharmacy cold chain, this is a critical control failure

---

## Summary Table

| Property | Original Verdict | Defense Verdict | Spec Status |
|---|---|---|---|
| PROP_TSTAT_001 | VIOLATED (CRITICAL) | **PARTIALLY DISPROVED** | Exit condition exists in spec (§4.3.9.42); "permanent lock" claim is wrong. No-minimum-constraint gap is real. FSM missing exit is a FSM deficiency. |
| PROP_TSTAT_020 | VIOLATED (MEDIUM) | **VALID — SPEC TEXTUAL GAP** | Attribute SHALL invariant (§4.3.9.33) requires update after every setpoint change; Both-mode deadband sub-path not explicitly enumerated in command spec. |
| PROP_TSTAT_016 | FSM_INCOMPLETE (MEDIUM) | **FULLY DISPROVED** | Spec §4.3.9.17–4.3.9.20 gives complete, identical SHALL cascading requirements for all four limit attributes. FSM inadequate, spec correct. |
| PROP_TSTAT_022 | FSM_INCOMPLETE (MEDIUM) | **FULLY DISPROVED** | Spec §4.3.9.21 explicitly mandates silent ignore with SHALL. FSM missing transition, spec is correct. |
| PROP_TSTAT_012 | HOLDS_WITH_GAPS (MEDIUM) | **VALID — SPEC GAP CONFIRMED** | No normative SHALL mandates autonomous hold clearing at expiry. Timestamp is informational. Hold may persist indefinitely in a conformant implementation. |
| PROP_TSTAT_019 | HOLDS_WITH_GAPS (LOW) | **FULLY DISPROVED** | Spec §4.3.9.2: "SHALL always report null" — strongest possible normative statement. Original verdict was too conservative. Property HOLDS fully. |
| PROP_TSTAT_026 | HOLDS_WITH_GAPS (HIGH) | **PARTIALLY DISPROVED** | Manage privilege required; constraint removal intentional and documented (Revision 8 NOTE); clamping mandated to device's supported range. HIGH severity overstated. Residual: no normative maximum calibration bound. |

---

## Specification Anomalies Found During This Review

The following editorial defects were identified in the specification during the course of this analysis. None of these defects create vulnerabilities in themselves, but they create implementation ambiguity and should be addressed in a future errata or revision.

### Anomaly 1 — Section 4.3.9.42: Trigger Condition References Wrong Setpoint Attribute

The body paragraph of Section 4.3.9.42 (Page 362) states "OccupiedCoolingSetpoint or UnoccupiedCoolingSetpoint" as the comparator in the EmergencyHeat trigger condition. The first sentence of the same section, and the worked example on the same page, both use OccupiedHeatingSetpoint or UnoccupiedHeatingSetpoint. The body text contains an editorial substitution error: "Cooling" should read "Heating." The intent is unambiguous from context but the text is internally inconsistent.

**Recommended correction**: In the trigger condition paragraph, replace "OccupiedCoolingSetpoint or UnoccupiedCoolingSetpoint" with "OccupiedHeatingSetpoint or UnoccupiedHeatingSetpoint."

### Anomaly 2 — Section 4.3.9.42: De-escalation Target State Undefined

The exit condition "continue operating in that running state until the OccupiedHeatingSetpoint value is reached" specifies when to exit EmergencyHeat mode but does not specify which SystemMode value to restore. Implementations will disagree on whether to revert to the prior SystemMode, to `Heat`, or to `Auto`.

**Recommended addition**: "Upon reaching OccupiedHeatingSetpoint, the server SHALL revert SystemMode to the value in effect immediately prior to the autonomous switch to EmergencyHeat mode."

### Anomaly 3 — Section 4.3.9.33: SetpointRaiseLower Cross-Reference Missing

The SetpointChangeSource attribute description (Section 4.3.9.33) creates an implicit update obligation via its unconditional SHALL but does not cross-reference the SetpointRaiseLower command. The SetpointRaiseLower Effect on Receipt section (4.3.10.1) should explicitly list SetpointChangeSource update for ALL execution paths, including the Both-mode deadband adjustment sub-path.

**Recommended addition to 4.3.10.1**: "For all Mode values, upon successfully modifying any setpoint, the server SHALL set SetpointChangeSource to External, SetpointChangeAmount to the effective delta applied, and SetpointChangeSourceTimestamp to the current UTC time."
