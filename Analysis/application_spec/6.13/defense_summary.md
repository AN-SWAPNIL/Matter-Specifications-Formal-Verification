# Defense Summary — Content Control Cluster (6.13)
**Specification:** Matter 1.5 Application Cluster Specification, Section 6.13 (Pages 611–627)  
**Cluster ID:** 0x050F (CONCON)  
**Analysis Date:** 2026-03-07  
**Role:** Spec owner defense — each claimed violation is either **DISPROVED** (spec is correct and complete) or **VALID** (genuine spec gap confirmed with attack scenario).

---

## Violations Under Review

The vulnerability analysis identified 6 violated properties:

| Property ID | Name | Claimed Severity | Defense Verdict |
|---|---|---|---|
| PROP_014 | BlockChannelIndex_NULL_On_AddBlockChannels | MEDIUM | **DISPROVED** |
| PROP_018 | No_Duplicate_DayOfWeek_In_BlockContentTimeWindow | HIGH | **VALID** |
| PROP_029 | BonusTime_Cannot_Exceed_Day_Remainder | HIGH | **VALID** |
| PROP_031 | TimePeriod_EndHour_GTE_StartHour | MEDIUM | **DISPROVED** |
| PROP_032 | TimePeriod_EndMinute_GT_StartMinute_Same_Hour | MEDIUM | **DISPROVED** |
| PROP_033 | BlockContentTimeWindow_Max_Seven_Entries | MEDIUM | **DISPROVED** |

---

## PROP_014 — BlockChannelIndex_NULL_On_AddBlockChannels

**Claimed Violation:** "VIOLATED — BlockChannelList integrity compromise if implementation uses caller-supplied index."

### VERDICT: DISPROVED

The specification fully and correctly specifies both the client-side requirement (send NULL) and the server-side behavior (assign a unique index). There is no documentation gap.

**Client-side requirement — §6.13.8.12.1 (Page 624), exact quote:**
> "The BlockChannelIndex field passed in this command SHALL be NULL."

**Server-side assignment behavior — §6.13.8.12 (Page 623–624), exact quote:**
> "If there is at least one channel in Channels field which is not in the BlockChannelList attribute, the media device SHALL process the request by adding these new channels into the BlockChannelList attribute and return a successful Status Response. During this process, **the media device SHALL assign one unique index to BlockChannelIndex field for every channel passed in this command.**"

**Why the claim is wrong:** The spec mandates that the server *overrides* whatever index may have arrived and assigns its own unique value. The server is never supposed to use the caller-supplied index. Both the obligation on the client (SHALL be NULL) and the obligation on the server (SHALL assign) are normatively stated. The FSM model failing to capture the server-assignment step is a modeling deficiency — not a spec deficiency. The spec is not faulty.

---

## PROP_018 — No_Duplicate_DayOfWeek_In_BlockContentTimeWindow

**Claimed Violation:** "VIOLATED — Duplicate DayOfWeek entries create ambiguous blocking window enforcement; children may access content during scheduled blocked periods." (HIGH severity)

### VERDICT: VALID

The spec states the uniqueness constraint on the attribute but fails to provide an enforcement mechanism in the command handler.

**Attribute constraint — §6.13.7.11 (Page 619), exact quote:**
> "There SHALL NOT be multiple entries in this attribute list for the same day of week."

**Command enforcement path — §6.13.8.16 (Page 625), exact quote:**
> "If the TimeWindowIndex field is NULL, the media device SHALL check if there is an entry in the BlockContentTimeWindow attribute which **matches with the TimePeriod and DayOfWeek fields** passed in this command. If Yes, then a response with TimeWindowAlreadyExist error status SHALL be returned."

**Why the claim is valid:** The command handler's duplicate check requires both TimePeriod AND DayOfWeek to match. If two entries share the same DayOfWeek bitmap value but have different TimePeriod values, the `TimeWindowAlreadyExist` check does NOT trigger and both entries are added — directly violating the §6.13.7.11 constraint. There is no error code in §6.13.6.1 (StatusCodeEnum) that covers the case of a DayOfWeek-only conflict with a different TimePeriod. The StatusCodeEnum defines: `TimeWindowAlreadyExist (0x0A)` for exact duplicates only.

**Attack / Issue Recreation Scenario:**
1. Manage-privileged controller sends `SetBlockContentTimeWindow` with `TimeWindowIndex = NULL`, `DayOfWeek = 0x02` (Monday), `TimePeriod = [{StartHour:9, StartMinute:0, EndHour:10, EndMinute:0}]`.
2. Server checks for exact (TimePeriod+DayOfWeek) match — none found. Entry is added with index 1.
3. Controller sends a second `SetBlockContentTimeWindow` with `TimeWindowIndex = NULL`, `DayOfWeek = 0x02` (Monday), `TimePeriod = [{StartHour:14, StartMinute:0, EndHour:15, EndMinute:0}]`.
4. Server checks for exact (TimePeriod+DayOfWeek) match — different TimePeriod, so no match. **Second Monday entry is added with index 2**, violating §6.13.7.11.
5. Result: BlockContentTimeWindow now contains two Monday entries. The spec provides no defined behavior for which window is enforced, creating enforcement ambiguity. A child could access content during one of the Monday windows depending on implementation priority.

The spec acknowledges the constraint exists but does not close the enforcement loop in the command handler.

---

## PROP_029 — BonusTime_Cannot_Exceed_Day_Remainder

**Claimed Violation:** "VIOLATED — Single AddBonusTime invocation can grant unlimited screen time, defeating daily limit entirely." (HIGH severity)

### VERDICT: VALID

The spec states a normative field constraint but provides no server-side enforcement path and no corresponding error code.

**Field constraint — §6.13.8.6.2 (Page 622), exact quote:**
> "This field SHALL indicate the amount of extra time (in seconds) to increase RemainingScreenTime. **This field SHALL NOT exceed the remaining time of this day.**"

**Server processing behavior — §6.13.8.6 (Page 621), exact quote:**
> "If a client with Manage privilege or greater invokes this command, the media device SHALL ignore the PINCode field and **directly increase the RemainingScreenTime attribute by the specified BonusTime value.**"

**StatusCodeEnum — §6.13.6.1 (Page 615–616):** No error code is defined for a BonusTime value that exceeds the day's remaining time. The codes defined are: `InvalidPINCode (0x02)`, `InvalidRating (0x03)`, `InvalidChannel (0x04)`, `ChannelAlreadyExist (0x05)`, `ChannelNotExist (0x06)`, `UnidentifiableApplication (0x07)`, `ApplicationAlreadyExist (0x08)`, `ApplicationNotExist (0x09)`, `TimeWindowAlreadyExist (0x0A)`, `TimeWindowNotExist (0x0B)`.

**Why the claim is valid:** Unlike a static range constraint (e.g., "0 to 23"), "SHALL NOT exceed the remaining time of this day" is a **runtime constraint** — the valid upper bound changes continuously as the day progresses. Matter's generic CONSTRAINT_ERROR mechanism handles static type range violations during TLV parsing but is not designed for runtime application-level bounds checking. The AddBonusTime command processing description does **not** instruct the server to compare BonusTime against the current RemainingScreenTime before applying it. The server is only told to "directly increase … by the specified BonusTime value." There is no defined rejection path.

**Attack / Issue Recreation Scenario:**
1. Content control is enabled; RemainingScreenTime = 300 seconds (5 minutes left in the day).
2. A Manage-privileged controller (e.g., a compromised smart home app with Manage role) sends `AddBonusTime` with `BonusTime = 86400` (24 hours).
3. Per §6.13.8.6, the server SHALL directly increase RemainingScreenTime by 86400 seconds.
4. The StatusCodeEnum provides no error code to reject this. The processing text mandates the increase without any validation step.
5. Result: RemainingScreenTime becomes 86400+300 seconds, completely defeating the daily screen time limit configured by the parent. The constraint "SHALL NOT exceed the remaining time of this day" is a client obligation that the server has no mechanism to enforce.

---

## PROP_031 — TimePeriod_EndHour_GTE_StartHour

**Claimed Violation:** "VIOLATED — Invalid time windows may fail to enforce blocking or block during unintended hours." (MEDIUM severity)

### VERDICT: DISPROVED

The constraint is explicitly and normatively stated in the data type specification.

**Data type constraint — §6.13.5.6.3 (Page 615), exact quote:**
> "This field SHALL indicate the ending hour. **EndHour SHALL be equal to or greater than StartHour.**"

**Why the claim is wrong:** This is a normative `SHALL` constraint placed directly in the `TimePeriodStruct` data type definition. In Matter, data type field constraints defined with `SHALL` are part of the type contract — any value transmitted in this field that violates the constraint constitutes invalid data. A server receiving a `TimePeriodStruct` with `EndHour < StartHour` is receiving data that violates an explicit SHALL constraint and SHALL respond with `CONSTRAINT_ERROR` per Matter Core Specification general constraint enforcement rules (which apply universally across all clusters). The Content Control application-level spec does not need to restate generic error handling that is already mandated by the Core Specification.

The constraint is in the specification. The FSM model not capturing enforcement of this constraint is a modeling deficiency — the spec itself is not faulty.

---

## PROP_032 — TimePeriod_EndMinute_GT_StartMinute_Same_Hour

**Claimed Violation:** "VIOLATED — Zero-duration time windows consume quota and may cause undefined enforcement behavior." (MEDIUM severity)

### VERDICT: DISPROVED

The constraint is explicitly and normatively stated in the data type specification.

**Data type constraint — §6.13.5.6.4 (Page 615), exact quote:**
> "This field SHALL indicate the ending minute. **If EndHour is equal to StartHour then EndMinute SHALL be greater than StartMinute.** If the EndHour is equal to 23 and the EndMinute is equal to 59, all contents SHALL be blocked until 23:59:59."

**Why the claim is wrong:** Identical reasoning to PROP_031. This is a normative `SHALL` cross-field constraint within the `TimePeriodStruct` data type. The spec explicitly forbids zero-duration or negative-duration windows by requiring EndMinute > StartMinute when both hours are equal. A server that accepts a struct with `StartHour=10, StartMinute=30, EndHour=10, EndMinute=30` (zero duration) is violating an explicit SHALL constraint in the data type, and shall reject with `CONSTRAINT_ERROR`. The constraint is in the specification. The spec is not faulty.

---

## PROP_033 — BlockContentTimeWindow_Max_Seven_Entries

**Claimed Violation:** "VIOLATED — 8th entry accepted in FSM model; potential memory overflow on constrained devices, DoS against legitimate window configuration." (MEDIUM severity)

### VERDICT: DISPROVED

The maximum entry count constraint is explicitly stated as a normative attribute constraint.

**Attribute constraint — §6.13.7 Attributes Table (Page 617), exact quote:**

| ID | Name | Type | Constraint | ... |
|----|------|------|------------|-----|
| 0x000A | BlockContentTimeWindow | list[TimeWindowStruct] | **max 7** | ... |

**Supporting design constraint — §6.13.7.11 (Page 619), exact quote:**
> "There SHALL NOT be multiple entries in this attribute list for the same day of week."

**Why the claim is wrong:** The `max 7` constraint is normatively specified in the attribute definition table. This is not implicit or informal — it is a normative attribute capacity constraint. In Matter, `max N` on a list attribute means the server SHALL reject any write operation that would cause the list to exceed N entries. Since there are exactly 7 days in a week and §6.13.7.11 prohibits multiple entries per day, the `max 7` constraint is perfectly consistent with the intent: at most one entry per day of the week. When a `SetBlockContentTimeWindow` command would add an 8th entry, the server SHALL reject it with `RESOURCE_EXHAUSTED` per Matter Core Specification general resource limit handling. The specification constrains this correctly and explicitly. The FSM model violating this is a modeling deficiency — the spec is not faulty.

---

## Summary Table

| Property ID | Verdict | Rationale |
|---|---|---|
| PROP_014 | **DISPROVED** | Spec explicitly mandates client sends NULL (§6.13.8.12.1) and server assigns its own unique index (§6.13.8.12). Both sides are fully specified. |
| PROP_018 | **VALID** | Attribute constraint §6.13.7.11 prohibits duplicate DayOfWeek, but command handler §6.13.8.16 only checks exact (TimePeriod+DayOfWeek) match — no enforcement path for same-DayOfWeek different-TimePeriod case. No error code defined. Exploitable. |
| PROP_029 | **VALID** | §6.13.8.6.2 says BonusTime "SHALL NOT exceed the remaining time of this day" but §6.13.8.6 processing mandates direct increase with no validation step, no ceiling, and no error code for overflow. Runtime constraint is unenforceable as specified. Exploitable by Manage-privileged clients. |
| PROP_031 | **DISPROVED** | §6.13.5.6.3 explicitly states "EndHour SHALL be equal to or greater than StartHour." Normative data type constraint; server enforces via Matter Core CONSTRAINT_ERROR. Spec is correct. |
| PROP_032 | **DISPROVED** | §6.13.5.6.4 explicitly states "If EndHour is equal to StartHour then EndMinute SHALL be greater than StartMinute." Normative data type constraint; spec is correct. |
| PROP_033 | **DISPROVED** | §6.13.7 attribute table explicitly states constraint "max 7" on BlockContentTimeWindow. Consistent with the 7-day structure of §6.13.7.11. Server enforces via Matter Core RESOURCE_EXHAUSTED. Spec is correct. |

**Confirmed spec gaps: 2 (PROP_018, PROP_029)**  
**Correctly disproved: 4 (PROP_014, PROP_031, PROP_032, PROP_033)**
