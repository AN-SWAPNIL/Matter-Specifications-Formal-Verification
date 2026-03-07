# Window Covering Cluster — Specification Defense Summary

**Cluster**: Window Covering (0x0102) · PICS Code: WNCV  
**Specification**: Matter 1.5 Application Cluster Specification, Section 5.3, Pages 477–493  
**Analyzed Claims**: 5.3_window_covering_vulnerability_analysis.json — 5 VIOLATED properties (PROP_WNCV_003, 011, 015, 018, 023)  
**Defense Date**: 2026-03-07

---

## Role and Methodology

This document defends the Matter 1.5 Window Covering Cluster specification against the five "VIOLATED" findings raised in the FSM security analysis. For each claim this review:

- Searches the specification for normative text that disproves the claim, with exact quotes and section references  
- Concedes the claim where the specification is genuinely silent or incomplete  
- Provides an executable attack/issue scenario for every claim that cannot be disproved

There is no middle ground. Each property closes with a binary verdict: **DISPROVED** or **VALID**. Reasons that make a claim invalid regardless of missing normative text (non-creatable attack, read-only attribute, hardware-safety delegation) are argued explicitly.

---

## 1. PROP_WNCV_003 — No_Mandatory_Halt_On_ObstacleDetected

**Original Verdict**: VIOLATED (CRITICAL)  
**Claimed Impact**: Motorized closing motion may entrap persons, animals, or objects when `SafetyStatus.ObstacleDetected = 1`

---

### Defense

**VERDICT: DISPROVED**

The vulnerability analysis rests on two claims: (a) that a conformant device is _permitted_ to continue closing when `ObstacleDetected` is set, and (b) that the spec is silent on the behavioral consequence of this bit. Both claims fail under direct scrutiny of the specification.

#### 1.1 SafetyStatus Is an Optional Attribute — Each Bit Is Individually Optional

Section 5.3.6, Attributes table (Page 485):

| ID     | Name           | Type               | Constraint | Quality | Conformance |
|--------|----------------|--------------------|------------|---------|-------------|
| 0x001A | SafetyStatus   | SafetyStatusBitmap | desc       | P       | **O**       |

Section 5.3.6.14, "SafetyStatus Attribute" (Page 490):

> *"The SafetyStatus attribute reflects the state of the safety sensors and the common issues preventing movements. By default for nominal operation all flags are cleared (0). **A device might support none, one or several bit flags from this attribute (all optional).**"*

Conformance O (Optional) for the entire attribute, combined with the explicit statement that each bit is individually optional, means:

- Devices **without obstacle-detection hardware** legitimately omit SafetyStatus entirely or omit the `ObstacleDetected` bit. There is no protocol-level gap for these devices because they have no obstacle-detection capability to enforce.
- Devices **with obstacle-detection hardware** implement the bit. In those devices, the bit's own definition IS the behavioral requirement (see §1.2 below).

There is no class of conformant device for which the spec is defectively silent on what to do when obstacle detection fires.

#### 1.2 The ObstacleDetected Bit Definition IS the Behavioral Requirement

Section 5.3.5.4, SafetyStatusBitmap Type (Page 481):

> *"ObstacleDetected (bit 5): **An obstacle is preventing actuator movement.**" — Conformance: M (within the attribute)*

The phrase "**is preventing**" is active present tense. It does not say "an obstacle has been noticed" or "a sensor reported something." It states that the obstacle **is**, right now, preventing actuator movement. A device that sets this bit is, by the semantic definition of the bit, already operating in a state where its hardware safety layer has halted the actuator.

This is a status-reporting bit, not a request bit. The device sets the bit BECAUSE its hardware is preventing movement. A window covering with certified obstacle detection (e.g., EN 60335 anti-entrapment circuitry) halts at the hardware level; the cluster bit merely makes that state visible to network observers.

#### 1.3 The Spec Explicitly Delegates Physical Safety to Product Safety Standards

Section 5.3.5.4, SafetyStatusBitmap, bit 7 (Page 482):

> *"StopInput (bit 7): Local safety sensor (not a direct obstacle) is preventing movements **(e.g. Safety EU Standard EN60335)**." — Conformance: M*

The spec directly cites EN 60335 — the IEC/EU safety standard for household appliances that governs anti-entrapment and obstacle-halting requirements for motorized window coverings. The Matter cluster specification is a **communications protocol specification**, not a product safety standard. Product-level physical safety is governed by regulatory standards (EN 60335, UL 325, CE) which are pre-conditions for market entry in every jurisdiction where window coverings are sold.

The spec's design is architecturally correct: physical safety is enforced by hardware that complies with product safety law; the cluster protocol **reports** that hardware's status. Duplicating EN 60335 requirements inside a transport protocol specification would be architecturally wrong and unnecessary.

#### 1.4 Summary: Attack Scenario Is Not a Protocol-Level Attack

The analysis constructs a scenario where a closing command is sent while `ObstacleDetected = 1` and claims the motor continues closing. On a compliant device:

- If the device has obstacle-detection hardware, that hardware's safety circuit is by definition already halting the actuator (that is what setting the bit means).
- If the device has no such hardware, it does not implement the bit, and no bit is set.

There is no valid class of conformant device for which the described entrapment outcome occurs due to a specification deficiency. The gap alleged (no SHALL in command handler sections) is intentional: the enforcement is in hardware and product safety law, not in the cluster protocol.

---

## 2. PROP_WNCV_011 — FeatureMap_Matches_Type_Attribute_Supported_Features

**Original Verdict**: VIOLATED (HIGH)  
**Claimed Impact**: FeatureMap/Type mismatch set by an Admin-privileged attacker causes controller automation failure

---

### Defense

**VERDICT: DISPROVED**

The attack scenario is structurally impossible. Both attributes involved — `Type` and `FeatureMap` — are Fixed quality and have Read-only remote access.

#### 2.1 Type Attribute Is Fixed and Read-Only

Section 5.3.6, Attributes table (Page 485):

| ID     | Name | Type     | Constraint | **Quality** | Fallback | **Access** | Conformance |
|--------|------|----------|------------|-------------|----------|------------|-------------|
| 0x0000 | Type | TypeEnum | desc       | **F**       | 0        | **R V**    | M           |

Quality `F` = Fixed. From the Matter data model: a Fixed quality attribute's value is set at manufacturing time and **SHALL NOT change for the lifetime of the device**. It is not writable through the cluster protocol.

Access `R V` = Read (any node), View privilege required — there is **no write access column**. No network client — not even an Admin-privileged node — can write to the Type attribute after manufacturing.

#### 2.2 FeatureMap Is Equally Fixed and Read-Only

The FeatureMap attribute (Cluster Global Attribute 0xFFFC) has Quality F in the Matter data model. A device's FeatureMap is defined at manufacturing time and cannot be changed remotely.

#### 2.3 The Normative Constraint Operates at the Correct Time

Section 5.3.4, Features (Page 477):

> *"Due to backward compatibility reasons **this feature map SHALL match the advertised Type Attribute Supported Features.**"*

Since both Type and FeatureMap are Fixed (F) quality, the SHALL constraint is a **manufacturing and certification time constraint**. This is the correct and only valid enforcement point for attributes that are immutable at runtime. Matter device certification testing (PICS/PIXIT validation) verifies this consistency before any device reaches the market.

#### 2.4 The Attack Scenario Is Impossible

The analysis states: *"Attacker with Admin access (or firmware bug) sets Type to 8 (TiltBlindLiftAndTilt) while FeatureMap only sets bit 0 (LF)."* This cannot happen through any network operation because: Type attribute Access = `R V` (no write path). An Admin-privileged remote client cannot write to a Fixed-quality read-only attribute. The FSM contains no input path for this operation because no such operation exists in the cluster protocol.

A firmware bug is an implementation defect, not a specification defect. Firmware defects are outside the scope of specification analysis.

---

## 3. PROP_WNCV_015 — PositionAware_Attributes_Bounded_Zero_To_10000

**Original Verdict**: VIOLATED (HIGH)  
**Claimed Impact**: GoToLiftPercentage/GoToTiltPercentage payload values > 10000 cause motor over-travel and mechanical damage

---

### Defense Attempt

**VERDICT: VALID — Specification gap confirmed**

This claim cannot be disproved. The specification fails to require command handlers to reject `GoToLiftPercentage` or `GoToTiltPercentage` payload values exceeding 10000.

#### 3.1 The Command Table Does Not Constrain the Payload Field

Section 5.3.7.4, GoToLiftPercentage Command (Page 492):

| ID | Name                   | Type          | Constraint | Quality | Fallback | Conformance |
|----|------------------------|---------------|------------|---------|----------|-------------|
| 0  | LiftPercent100thsValue | percent100ths | **desc**   |         |          | M           |

Section 5.3.7.5, GoToTiltPercentage Command (Page 493):

| ID | Name                   | Type          | Constraint | Quality | Fallback | Conformance |
|----|------------------------|---------------|------------|---------|----------|-------------|
| 0  | TiltPercent100thsValue | percent100ths | **desc**   |         |          | M           |

Constraint `desc` means "see the descriptive text for the constraint." Examining the Effect on Receipt text for GoToLiftPercentage (Page 492):

> *"Upon receipt of this command, the server will adjust the window covering to the lift/slide percentage specified in the payload of this command."*
>
> *"If the command includes LiftPercent100thsValue, then TargetPositionLiftPercent100ths attribute SHALL be set to LiftPercent100thsValue."*

No constraint on `LiftPercent100thsValue` is stated in the descriptive text. The command description applies the value unconditionally.

#### 3.2 The Output Attribute Is Not Bounded in Its Own Table Entry

Section 5.3.6, Attributes table (Page 485):

| ID     | Name                              | Type          | Constraint |
|--------|-----------------------------------|---------------|------------|
| 0x000B | TargetPositionLiftPercent100ths   | percent100ths | *(blank)*  |
| 0x000E | CurrentPositionLiftPercent100ths  | percent100ths | **max 10000** |

`CurrentPositionLiftPercent100ths` explicitly states `max 10000`. `TargetPositionLiftPercent100ths` has no explicit constraint. If the spec intended TargetPosition to be bounded to 10000, the constraint column should state `max 10000` — as it does for `CurrentPosition`. The omission is not symmetrical; it is a specification gap.

#### 3.3 The Semantic Bound Exists but Is Not Normatively Enforced at the Command Level

Section 5.3.4.3, PositionAware Features (Page 477):

> *"Relative positioning with percent100ths (min step 0.01%) attribute is mandatory, e.g. **Max 10000 equals 100.00%**…"*

This establishes that 10000 is semantically 100%, but this phrasing appears in a feature description, not in the command Effect on Receipt section. The statement does not constitute a SHALL-level rejection rule for command payloads that exceed 10000.

#### 3.4 Attack Scenario (Valid)

1. Device is at 50% lift (`CurrentPositionLiftPercent100ths` = 5000). Feature_LF and PA_LF are active.
2. Operator sends `GoToLiftPercentage` with `LiftPercent100thsValue` = 65535 (uint16 max).
3. No normative rejection text exists in Section 5.3.7.4. The server sets `TargetPositionLiftPercent100ths` = 65535 and begins closing.
4. The device reaches the physical closed limit (actual position 10000) while `TargetPositionLiftPercent100ths` remains 65535.
5. Depending on firmware quality: the motor stalls against the mechanical end-stop, `OperationalStatus.Lift` may remain `10b` (closing) indefinitely, and the next `StopMotion` sets `TargetPositionLiftPercent100ths` = `CurrentPositionLiftPercent100ths` — wherever it stopped — rather than the intended target.
6. Result: motor stall, potential damage, position tracking inconsistency.

The specification should state: *"If LiftPercent100thsValue exceeds 10000, the server SHALL return CONSTRAINT_ERROR and ignore the command."* This is absent from Sections 5.3.7.4 and 5.3.7.5.

---

## 4. PROP_WNCV_018 — SafetyStatus_RemoteLockout_Informational_Only

**Original Verdict**: VIOLATED (MEDIUM)  
**Claimed Impact**: Unauthorized movement because `RemoteLockout` enforcement is vendor-specific

---

### Defense

**VERDICT: DISPROVED**

The attack scenario is structurally impossible. The `SafetyStatus` attribute is read-only; no client can set `RemoteLockout`. The behavioral definition of the bit contains the normative enforcement requirement.

#### 4.1 SafetyStatus Is Read-Only — No Client Can Write It

Section 5.3.6, Attributes table (Page 485):

| ID     | Name         | Type               | Constraint | Quality | **Access** | Conformance |
|--------|--------------|--------------------|------------|---------|------------|-------------|
| 0x001A | SafetyStatus | SafetyStatusBitmap | desc       | P       | **R V**    | O           |

Access `R V` = Read, View privilege required. **There is no write column.** No network client — at any privilege level (View, Operate, Manage, Admin) — can write to `SafetyStatus`. Only the device's own firmware sets this attribute.

#### 4.2 The Attack Scenario Is Impossible

The analysis states: *"Building management system sets a time-based lockout: SafetyStatus.RemoteLockout=1 (covering should not move outside business hours). Attacker with Operate privilege sends DownOrClose."*

The premise is false. The building management system **cannot** set `SafetyStatus.RemoteLockout`. The attribute is read-only. The DEVICE sets `RemoteLockout` itself, based on its own internal logic (time-based access control, authorization checks, etc.). When the DEVICE sets `RemoteLockout = 1`, it has internally triggered its lockout mechanism; the bit merely makes this visible on the network.

#### 4.3 The Bit Definition IS the Normative Enforcement Statement

Section 5.3.5.4, SafetyStatusBitmap Type (Page 481):

> *"RemoteLockout (bit 0): **Movement commands are ignored (locked out).** e.g. not granted authorization, outside some time/date range." — Conformance: M*

Parse the definition carefully: it does not say "this bit may be set when movement is intended to be locked out." It says **"Movement commands are ignored (locked out)"** — present tense active voice. This describes what IS happening when the bit is set. The device that sets this bit is, by the semantic definition of its own action, simultaneously ignoring movement commands. These are the same operation: the internal mechanism that ignores movement commands also sets this bit to report that condition.

The vulnerability analysis claims this text is "informational only" because it does not appear as an explicit guard clause in Sections 5.3.7.1–5.3.7.5. However, in the Matter specification model, the definition of what an attribute bit MEANS IS the normative requirement for what the device DOES when that bit is set. A device that sets `RemoteLockout = 1` while still accepting movement commands would be contradicting its own attribute — reporting that commands are ignored while not ignoring them, which is a falsehood violating the attribute's SHALL definition.

#### 4.4 The Lockout Mechanism Is Internal by Design

Section 5.3.5.4 examples: *"e.g. not granted authorization, outside some time/date range."* These are examples of internal DEVICE logic (authorization policies, schedules) that the device applies and reflects in the bit. Higher-level access control policies (time-of-day lockout, authorization schedules) belong to the device's application logic layer, not the cluster protocol layer. This is architecturally correct: the protocol reports the enforcement state; the enforcement policy is internal.

---

## 5. PROP_WNCV_023 — Type_Attribute_Constrained_By_Feature_Combination

**Original Verdict**: VIOLATED (MEDIUM)  
**Claimed Impact**: Inconsistent Type/FeatureMap causes controller automation failure

---

### Defense

**VERDICT: DISPROVED**

This claim fails for the same fundamental reason as PROP_WNCV_011: the `Type` attribute is Fixed quality and read-only. The runtime enforcement scenario it constructs is impossible.

#### 5.1 Type Attribute Cannot Be Changed After Manufacturing

Section 5.3.6, Attributes table (Page 485):

| ID     | Name | Type     | Constraint | **Quality** | **Access** | Conformance |
|--------|------|----------|------------|-------------|------------|-------------|
| 0x0000 | Type | TypeEnum | desc       | **F**       | **R V**    | M           |

Quality `F` (Fixed): value is set at manufacturing and SHALL NOT change. Access `R V`: read-only from any remote client perspective.

#### 5.2 The SHALL Constraint of Section 5.3.6.1 Operates at Manufacturing/Certification Time

Section 5.3.6.1, Type Attribute (Pages 486–487):

> *"If the window covering supports the LF feature and not the TL feature, the following types SHALL be used as the constraint for this attribute: [RollerShade, RollerShade2Motor, …]"*
>
> *"If the window covering supports the TL feature and not the LF feature, the following types SHALL be used: [Shutter, TiltBlindTiltOnly, …]"*
>
> *"If the window covering supports both the LF and TL features, the following types are allowed to be used: [TiltBlindLiftAndTilt, Unknown]"*

These are explicit, SHALL-level constraints on valid Type values given a feature combination. They are compliance requirements enforced by Matter device certification testing before any device is commissioned on a live fabric. The Matter PICS/PIXIT test framework validates Type–FeatureMap consistency as a precondition for certification.

#### 5.3 The Attack Scenario Is Impossible Through the Protocol

The analysis states: *"Firmware sets Type = 7 (TiltBlindTiltOnly) while FeatureMap sets Feature_LF=1 and Feature_TL=1."*

This cannot occur through any network operation after commissioning because:
- Type attribute is read-only (`R V`) — no remote set operation exists
- FeatureMap is Fixed — it cannot change post-manufacture

For the scenario to occur, both attributes would need to be set inconsistently at manufacturing time. A device shipped with this inconsistency would fail Matter certification testing (which validates Type/FeatureMap consistency per the SHALL constraints in Section 5.3.6.1) and would never reach the market. A non-certified device is not a specification deficiency.

A firmware bug that establishes this inconsistency at initialization is an implementation defect, not a deficiency in the specification text.

---

## Summary Table

| Property ID   | Name                                              | Original Verdict | Defense Verdict | Reason for Defense Outcome                                               |
|---------------|---------------------------------------------------|------------------|-----------------|--------------------------------------------------------------------------|
| PROP_WNCV_003 | No_Mandatory_Halt_On_ObstacleDetected             | VIOLATED         | **DISPROVED**   | SafetyStatus is optional; ObstacleDetected describes a state where hardware IS already halting the actuator; physical safety delegated to product safety standards (EN 60335) |
| PROP_WNCV_011 | FeatureMap_Matches_Type_Attribute_Supported_Features | VIOLATED      | **DISPROVED**   | Type and FeatureMap are both Fixed (F) quality and Read-only (R V); cannot be changed by any network client; attack scenario is structurally impossible |
| PROP_WNCV_015 | PositionAware_Attributes_Bounded_Zero_To_10000    | VIOLATED         | **VALID**       | No SHALL-level rejection exists in GoToLiftPercentage/GoToTiltPercentage command handler text for values > 10000; TargetPosition attribute lacks explicit max 10000 constraint |
| PROP_WNCV_018 | SafetyStatus_RemoteLockout_Informational_Only     | VIOLATED         | **DISPROVED**   | SafetyStatus is read-only (R V); no client can set RemoteLockout; the bit definition "Movement commands are ignored (locked out)" is itself the normative behavioral requirement |
| PROP_WNCV_023 | Type_Attribute_Constrained_By_Feature_Combination | VIOLATED        | **DISPROVED**   | Type is Fixed (F) quality and Read-only (R V); constraint is manufacturing/certification time; attack scenario is structurally impossible |

---

## Final Score

| Outcome | Count | Properties |
|---------|-------|------------|
| **DISPROVED** | 4 | PROP_WNCV_003, 011, 018, 023 |
| **VALID** | 1 | PROP_WNCV_015 |

**One genuine specification gap confirmed:** GoToLiftPercentage and GoToTiltPercentage command handlers (Sections 5.3.7.4–5.3.7.5) do not include a SHALL-level rejection clause for payload values exceeding 10000. This is exploitable and the specification should be amended to require `CONSTRAINT_ERROR` for `LiftPercent100thsValue` or `TiltPercent100thsValue` > 10000.
