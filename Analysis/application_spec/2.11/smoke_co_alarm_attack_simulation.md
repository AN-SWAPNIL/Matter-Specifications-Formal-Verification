# Smoke CO Alarm Cluster Attack Simulation Analysis

## Document Metadata

| Field                     | Value                                                      |
| ------------------------- | ---------------------------------------------------------- |
| **Cluster**               | Smoke CO Alarm Cluster (0x005C)                            |
| **PICS Code**             | SMOKECO                                                    |
| **Specification**         | Matter 1.5 Application Cluster Specification, Section 2.11 |
| **Spec Pages**            | 210-220                                                    |
| **Analysis Date**         | 2025-01-18                                                 |
| **Safety Classification** | CRITICAL - Life Safety Device                              |
| **FSM Model**             | smoke_co_alarm_fsm.json                                    |

---

## Executive Summary

This document presents detailed attack simulations for the four confirmed specification gaps in the Matter Smoke CO Alarm cluster. Each attack is modeled using FSM state traces demonstrating exploitable paths through the specification-compliant state machine.

### Deep Verification Summary

All vulnerabilities were verified against BOTH `application_spec` AND `core_spec` to confirm they are not covered elsewhere in the Matter specification.

| Gap ID     | Verification Scope | app_spec                             | core_spec                           | Final Status     |
| ---------- | ------------------ | ------------------------------------ | ----------------------------------- | ---------------- |
| GAP-AV-001 | Rate limiting      | Account Login (P.536) has it         | PASE limit (P.322) only             | **CONFIRMED**    |
| GAP-TM-001 | Mute duration      | Door Lock (P.426) has AutoRelockTime | Fail-safe timer (60s) only          | **CONFIRMED**    |
| GAP-TM-002 | Test timeout       | None found                           | None found                          | **CONFIRMED**    |
| GAP-CC-001 | Group auth         | None in cluster                      | Group Key Mgmt (S.4.16-4.17) EXISTS | **RECLASSIFIED** |

### Vulnerability Summary (Post Deep Verification)

| ID         | Vulnerability                       | Severity | Attack Vector    | Physical Safety Impact           | Status             |
| ---------- | ----------------------------------- | -------- | ---------------- | -------------------------------- | ------------------ |
| GAP-AV-001 | No Rate Limiting on SelfTestRequest | MEDIUM   | Remote (Network) | Battery drain → Device failure   | **CONFIRMED**      |
| GAP-TM-001 | No Mute Duration Specification      | HIGH     | Physical + Time  | Indefinite mute → Missed alarms  | **CONFIRMED**      |
| GAP-TM-002 | No Self-Test Duration Limits        | MEDIUM   | Fault/Remote     | Stuck state → Unavailable device | **CONFIRMED**      |
| GAP-CC-001 | Interconnect Auth Not Mandated      | LOW      | Remote (Network) | False alarms → Alarm fatigue     | **WEAK_NORMATIVE** |

---

## Attack 1: Battery Drain via SelfTestRequest Flooding (AV-003)

### Attack Overview

**Vulnerability**: The specification allows unlimited SelfTestRequest commands when the device is in Normal state. While concurrent tests are blocked (BUSY during Testing), there is no rate limiting between test completion and the next test initiation.

**Attack Goal**: Exhaust device battery to render smoke/CO detection inoperative.

### Specification Evidence

```
Section 2.11.7.1, Page 217:
"This command SHALL initiate a device self-test. The return status SHALL indicate
whether the test was successfully initiated. Only one SelfTestRequest may be
processed at a time."

"When the value of the ExpressedState attribute is any of SmokeAlarm, COAlarm,
Testing, InterconnectSmoke, InterconnectCO, the device SHALL NOT execute the
self-test, and SHALL return status code BUSY."
```

**Gap Analysis**: The specification prevents _concurrent_ tests but not _sequential_ tests. No rate limiting is specified.

**Cross-Reference Evidence** (Account Login Cluster, Page 536):

```
"The server SHALL implement rate limiting to prevent brute force attacks.
No more than 10 unique requests in a 10 minute period SHALL be allowed."
```

This proves Matter _can_ specify rate limiting; its absence in Smoke CO Alarm is a verifiable gap.

### FSM Attack Trace

```
INITIAL STATE: Normal
  ├── Attacker Capability: Operate privilege, network access
  └── Precondition: Battery-powered device, battery level = 100%

┌─────────────────────────────────────────────────────────────────────────────┐
│ ATTACK CYCLE (repeats N times until battery exhaustion)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: [Normal] ──SelfTestRequest──► [Testing]                            │
│          Guard: ExpressedState == Normal ✓                                  │
│          Action: TestInProgress := true                                     │
│                  ExpressedState := Testing                                  │
│                  BATTERY DRAIN: sensors activated, audio/visual on          │
│                                                                             │
│  Step 2: [Testing] ──InternalCompletion──► [Normal]                         │
│          Duration: ~10-30 seconds (manufacturer-defined)                    │
│          Action: TestInProgress := false                                    │
│                  ExpressedState := Normal                                   │
│                  SelfTestComplete event generated                           │
│                                                                             │
│  Step 3: [Normal] ──SelfTestRequest──► [Testing]                            │
│          ^^^ NO RATE LIMITING - IMMEDIATE RETRY ^^^                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

TERMINAL STATE: Normal (with depleted battery)
  └── Device non-functional, no smoke/CO detection capability
```

### Attack Timeline Calculation

| Parameter                  | Conservative | Aggressive |
| -------------------------- | ------------ | ---------- |
| Self-test duration         | 30 seconds   | 10 seconds |
| Tests per hour             | 120          | 360        |
| Normal battery life        | 2 years      | 2 years    |
| Battery impact per test    | 0.01%        | 0.01%      |
| Tests to drain battery     | 10,000       | 10,000     |
| Attack duration to deplete | ~83 hours    | ~28 hours  |

### Attack Sequence Diagram

```
Attacker                   Smoke/CO Alarm                    Battery
    │                            │                              │
    │──SelfTestRequest(1)───────►│                              │
    │                            │──activate sensors───────────►│-0.01%
    │                            │──audio/visual test─────────►│
    │                            │                              │
    │                   [30 sec test duration]                  │
    │                            │                              │
    │◄──Status: SUCCESS──────────│                              │
    │◄──SelfTestComplete event───│                              │
    │                            │                              │
    │──SelfTestRequest(2)───────►│  ← IMMEDIATE, NO DELAY       │
    │                            │──activate sensors───────────►│-0.01%
    │                            │                              │
    ⋮                            ⋮                              ⋮
    │                            │                              │
    │──SelfTestRequest(N)───────►│                              │
    │                            │──activate sensors───────────►│-0.01%
    │                            │     BATTERY CRITICAL          │
    │                            │──HardwareFault event────────►│
    │                            │                              │
    │                   [Device becomes inoperative]             │
```

### Physical Safety Impact

1. **Primary Impact**: Battery depleted, device cannot alert occupants to smoke/CO
2. **Detection Window**: Attack is audible (self-tests produce sound), but may occur when occupants away
3. **Recovery**: Requires battery replacement
4. **Severity**: MEDIUM - Requires sustained network access, detectable, reversible

---

## Attack 2: Indefinite Mute State Exploitation (TM-002)

### Attack Overview

**Vulnerability**: The specification defines DeviceMuted attribute and mute events but does NOT specify maximum mute duration or automatic unmute behavior.

**Attack Goal**: Exploit human behavior to leave device in muted state indefinitely, causing missed alarms.

### Specification Evidence

```
Section 2.11.6.5, Page 216:
"This attribute SHALL indicate the whether the audible expression of the device
is currently muted. Audible expression is typically a horn or speaker pattern."

Section 2.11.5.1.2, Page 211 (Warning alarms):
"Alarms in this state SHOULD be subject to being muted via physical interaction."

Section 2.11.5.1.3, Page 211 (Critical alarms):
"This value SHALL indicate that this alarm is in a critical state. Alarms in this
state SHALL NOT be subject to being muted via physical interaction."
```

**Gap Analysis**:

- DeviceMuted describes state but NOT duration
- Warning alarms can be muted, no unmute timer specified
- Critical alarms cannot be _newly_ muted, but spec is silent on: what if already muted when severity escalates?

### FSM Attack Trace

```
INITIAL STATE: Normal
  ├── Legitimate User Action: User is home, cooking causes smoke
  └── Precondition: Device in Normal state, no actual fire

┌─────────────────────────────────────────────────────────────────────────────┐
│ EXPLOITATION SCENARIO                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: [Normal] ──CookingSmoke──► [SmokeAlarm_Warning]                    │
│          Trigger: Smoke sensor detects cooking smoke                        │
│          Action: SmokeState := Warning                                      │
│                  ExpressedState := SmokeAlarm                               │
│                  SmokeAlarm event (severity: Warning)                       │
│                  AUDIBLE ALARM SOUNDS                                       │
│                                                                             │
│  Step 2: [SmokeAlarm_Warning] ──PhysicalMute──► [SmokeAlarm_Warning_Muted]  │
│          Trigger: User presses mute button (annoyed by false alarm)         │
│          Action: DeviceMuted := Muted                                       │
│                  AlarmMuted event generated                                 │
│                  AUDIBLE ALARM SILENCED                                     │
│                                                                             │
│  Step 3: [SmokeAlarm_Warning_Muted] ──SmokeClear──► [Normal_Muted??]        │
│          Trigger: Smoke dissipates, sensor returns to normal                │
│          Action: SmokeState := Normal                                       │
│          ^^^ SPEC AMBIGUOUS: Does DeviceMuted persist? ^^^                  │
│                                                                             │
│  --- TIME PASSES: Hours/Days ---                                            │
│                                                                             │
│  Step 4: [State_Muted] ──ActualFire──► [SmokeAlarm_Warning_Muted]           │
│          Trigger: Real fire starts in another room                          │
│          Action: SmokeState := Warning                                      │
│                  ExpressedState := SmokeAlarm                               │
│                  SmokeAlarm event generated (to controllers)                │
│                  ^^^ AUDIBLE ALARM SUPPRESSED DUE TO MUTE ^^^               │
│                                                                             │
│  Step 5: [SmokeAlarm_Warning_Muted] ──FireWorsens──► [SmokeAlarm_Critical]  │
│          Trigger: Fire intensifies, smoke concentration increases           │
│          Action: SmokeState := Critical                                     │
│          Question: Does transition to Critical force unmute?                │
│          ^^^ SPEC SILENT ON THIS BEHAVIOR ^^^                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

TERMINAL STATE: User unaware of fire due to muted audible alarm
  └── Potential injury or death
```

### Mute Persistence State Matrix

| Initial State   | Trigger              | New State        | DeviceMuted    | Spec Clarity |
| --------------- | -------------------- | ---------------- | -------------- | ------------ |
| Warning + Muted | Smoke clears         | Normal           | **UNDEFINED**  | GAP          |
| Warning + Muted | Escalate to Critical | Critical         | **UNDEFINED**  | GAP          |
| Normal + Muted? | New Warning          | Warning + Muted? | **UNDEFINED**  | GAP          |
| Any + Muted     | Time passes          | Same             | **NO TIMEOUT** | GAP          |

### Cross-Reference: Door Lock Auto-Relock

```
Door Lock Cluster, Section 5.2.9.22, Page 426:
"This attribute SHALL indicate the number of seconds to wait after unlocking
a lock before it automatically locks again. 0=disabled."
```

This demonstrates Matter CAN specify automatic state reversal timers. The absence of auto-unmute in Smoke CO Alarm is a gap.

### Physical Safety Impact

1. **Primary Impact**: Occupants not audibly alerted to actual fire/CO
2. **Contributing Factor**: Human behavior (muting for convenience)
3. **Escalation Risk**: Users may not notice visual-only alerts during sleep
4. **Severity**: HIGH - Directly impacts primary safety function

---

## Attack 3: Self-Test State Lock via Fault Exploitation (TM-003)

### Attack Overview

**Vulnerability**: The specification assumes self-test always completes internally. No maximum duration or timeout is specified.

**Attack Goal**: Exploit hardware/software fault to leave device stuck in Testing state.

### Specification Evidence

```
Section 2.11.7.1, Page 217:
"Upon successful acceptance of SelfTestRequest, the TestInProgress attribute
SHALL be set to True and ExpressedState attribute SHALL be set to Testing."

"Upon completion of the self test procedure, the SelfTestComplete event SHALL
be generated, the TestInProgress attribute SHALL be set to False and
ExpressedState attribute SHALL be updated to reflect the current state."
```

**Gap Analysis**: "Upon completion" assumes completion always occurs. No timeout, no watchdog, no forced completion mechanism.

### FSM Attack Trace

```
INITIAL STATE: Normal
  ├── Trigger: Legitimate self-test request or automated maintenance
  └── Precondition: Rare internal fault condition exists

┌─────────────────────────────────────────────────────────────────────────────┐
│ FAULT SCENARIO                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: [Normal] ──SelfTestRequest──► [Testing]                            │
│          Guard: ExpressedState == Normal ✓                                  │
│          Action: TestInProgress := true                                     │
│                  ExpressedState := Testing                                  │
│                                                                             │
│  Step 2: [Testing] ──InternalFault──► [Testing_Stuck]                       │
│          Fault: Sensor check hangs, completion signal lost, firmware bug    │
│          ^^^ NO INTERNAL COMPLETION SIGNAL GENERATED ^^^                    │
│                                                                             │
│  Step 3: [Testing_Stuck] ──(no transition defined)──► [Testing_Stuck]       │
│          State: TestInProgress == true (indefinitely)                       │
│                 ExpressedState == Testing (indefinitely)                    │
│          ^^^ NO TIMEOUT - NO FORCED EXIT - DEVICE STUCK ^^^                 │
│                                                                             │
│  Step 4: [Testing_Stuck] ──SelfTestRequest──► BUSY                          │
│          New test requests rejected while stuck                             │
│                                                                             │
│  Step 5: [Testing_Stuck] ──RealSmokeDetected──► ???                         │
│          ^^^ BEHAVIOR UNDEFINED DURING STUCK TEST ^^^                       │
│          Question: Are sensors monitored during test?                       │
│          Question: Can alarm trigger during Testing state?                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

TERMINAL STATE: Device stuck in Testing state
  └── Safety function availability: UNKNOWN/DEGRADED
```

### Stuck State Impact Analysis

| Attribute            | Expected Behavior      | Stuck State Behavior           |
| -------------------- | ---------------------- | ------------------------------ |
| TestInProgress       | false after completion | **true indefinitely**          |
| ExpressedState       | Normal after test      | **Testing indefinitely**       |
| New SelfTestRequest  | Accepted               | BUSY                           |
| Real smoke detection | Generate alarm         | **UNDEFINED**                  |
| User awareness       | Normal operation       | May notice "testing" indicator |

### Physical Safety Impact

1. **Primary Impact**: Device status unknown, safety function may be impaired
2. **Probability**: Low (requires fault condition)
3. **Detection**: Users may notice persistent "testing" indicator
4. **Severity**: MEDIUM - Low probability but significant safety impact

---

## Attack 4: Interconnect Alarm Injection (GAP-CC-001) - RECLASSIFIED

### ⚠️ Deep Verification Result: WEAK_NORMATIVE

**Important Note**: After deep verification against `core_spec`, this gap has been **RECLASSIFIED** from VIOLATED to WEAK_NORMATIVE. Core specification Sections 4.16-4.17 (Group Key Management) DO provide authenticated group messaging infrastructure. The gap is that the Smoke CO Alarm cluster does not explicitly MANDATE its use for interconnect signals.

### Attack Overview

**Vulnerability**: The specification describes interconnect alarm reception but does not explicitly require cryptographic authentication of the source.

**Attack Goal**: Inject false interconnect alarms to cause alarm fatigue or evacuation disruption.

### Specification Evidence

```
Section 2.11.8.9, Page 219:
"This event SHALL be generated when the device hosting the server receives
a smoke alarm from an interconnected sensor."

Section 2.11.6.9, Page 216:
"This attribute SHALL indicate whether the interconnected smoke alarm is
currently triggering by branching devices."
```

**Gap Analysis**: Specifies event generation but NOT source authentication mechanism.

### Core Spec Protection Mechanism (EXISTS - Reclassification Justification)

```
Core Spec Section 4.17, Pages 197-199 (Group Key Management):
"Operational group keys are made available to applications for the purpose of
authenticating peers, securing group communications, and encrypting data.
These keys allow Nodes to prove to each other that they are members of the
associated group."

Core Spec Section 4.18, Page 208 (MCSP):
"Message counter synchronization... protects against replay attacks, where an
attacker replays older messages."
```

**Deep Verification Conclusion**: Core spec DOES PROVIDE group authentication mechanism. The gap is that Smoke CO Alarm cluster does NOT explicitly REQUIRE its use for interconnect signals, but well-designed implementations SHOULD use Group Key Management for interconnect messaging. This is a **WEAK_NORMATIVE** gap (implementation ambiguity) rather than a VIOLATED gap (missing mechanism).

### FSM Attack Trace

```
INITIAL STATE: All interconnected alarms in Normal state
  ├── Network Configuration: Multiple Smoke CO alarms in same fabric/group
  └── Attacker Capability: Network access, possibly compromised group key

┌─────────────────────────────────────────────────────────────────────────────┐
│ ATTACK SCENARIO                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: [All Devices: Normal]                                              │
│          Attacker: Observes or infers interconnect signal format            │
│          If proprietary: Reverse-engineer signal structure                  │
│          If Matter group: May need compromised device or key                │
│                                                                             │
│  Step 2: [Target: Normal] ──InjectedInterconnectSignal──►                   │
│                           [Target: InterconnectSmoke_Warning]               │
│          Trigger: Attacker sends crafted interconnect alarm signal          │
│          ^^^ NO AUTHENTICATION CHECK MANDATED BY CLUSTER SPEC ^^^           │
│          Action: InterconnectSmokeAlarm := Warning                          │
│                  ExpressedState := InterconnectSmoke                        │
│                  InterconnectSmokeAlarm event generated                     │
│                                                                             │
│  Step 3: [Target: InterconnectSmoke_Warning]                                │
│          Result: All connected controllers receive alarm notification       │
│                  Building evacuation may be triggered                       │
│                  False alarm recorded in logs                               │
│                                                                             │
│  Step 4: Repeat attack randomly over time                                   │
│          Effect: Users experience "alarm fatigue"                           │
│                  Users start ignoring or disabling alarms                   │
│                                                                             │
│  Step 5: [Later: Real fire occurs]                                          │
│          User Response: "Probably another false alarm, ignore it"           │
│          Consequence: Delayed or no evacuation                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

TERMINAL STATE: Users conditioned to ignore alarms (alarm fatigue)
  └── Real emergency response delayed or absent
```

### Mitigation Analysis

| Protection Mechanism     | Source         | Mandated for Interconnect?       |
| ------------------------ | -------------- | -------------------------------- |
| Group Key encryption     | Core Spec 4.17 | **NO** (not required by cluster) |
| Message authentication   | Core Spec 4.17 | **NO** (not required by cluster) |
| Replay protection (MCSP) | Core Spec 4.18 | **NO** (not required by cluster) |
| Source verification      | Cluster Spec   | **NOT SPECIFIED**                |

### Physical Safety Impact

1. **Primary Impact**: Alarm fatigue leads to ignored alerts (IF Group Key Mgmt not implemented)
2. **Attack Difficulty**: HIGH (requires network access AND bypassing Group Key Management)
3. **Indirect Nature**: Does not directly suppress alarms, affects user behavior
4. **Severity**: LOW - Core spec provides authentication mechanism; attack requires poor implementation
5. **Status**: WEAK_NORMATIVE - Implementation guidance gap, not specification violation

---

## Combined Attack Scenario

### Multi-Vector Attack Timeline

```
Day 0-7: Reconnaissance
  └── Attacker maps network, identifies Smoke CO alarms, obtains Operate privilege

Day 7-14: Battery Degradation Phase (AV-003)
  └── Continuous SelfTestRequest flooding during unoccupied hours
  └── Battery drops from 100% to 40%

Day 14: Interconnect Alarm Injection (CC-002)
  └── False alarms at 2am, 3am, 4am
  └── Users wake up, find no fire, become annoyed

Day 15-30: Continued false alarms + battery drain
  └── Users consider disabling or removing "faulty" alarm
  └── Battery critical, HardwareFault event generated
  └── Users delay battery replacement (device already "annoying")

Day 31: Actual fire occurs
  └── Primary detector has dead battery
  └── Interconnect alarm triggers, users assume false alarm
  └── Evacuation delayed, injuries result
```

---

## Conclusion

After deep verification against BOTH `application_spec` AND `core_spec`:

### Confirmed Violations (3)

- **GAP-AV-001**: No rate limiting on SelfTestRequest (MEDIUM severity)
- **GAP-TM-001**: No mute duration specification (HIGH severity)
- **GAP-TM-002**: No self-test timeout (MEDIUM severity)

### Reclassified to Weak Normative (1)

- **GAP-CC-001**: Interconnect authentication not mandated (LOW severity) - Core spec provides Group Key Management; gap is implementation guidance, not missing mechanism

These gaps create exploitable attack paths in the Smoke CO Alarm cluster. The attacks range from direct resource exhaustion (battery drain) to indirect human-factor exploitation (mute state persistence). The severity is moderated by:

1. **Network access requirements** - Attacker needs Matter fabric access
2. **Detectability** - Self-tests are audible, false alarms visible
3. **Reversibility** - Battery replacement, user awareness restores function

However, for a **life-safety device**, even moderate-severity vulnerabilities warrant immediate specification remediation.

---

## References

| Document                    | Section   | Pages   | Key Content                 |
| --------------------------- | --------- | ------- | --------------------------- |
| Matter 1.5 App Cluster Spec | 2.11      | 210-220 | Smoke CO Alarm Cluster      |
| Matter 1.5 App Cluster Spec | 6.2       | 536     | Account Login Rate Limiting |
| Matter 1.5 App Cluster Spec | 5.2.9.22  | 426     | Door Lock AutoRelockTime    |
| Matter 1.5 Core Spec        | 4.16-4.17 | 197-199 | Group Key Management        |
| Matter 1.5 Core Spec        | 4.18      | 208-213 | MCSP Replay Protection      |
