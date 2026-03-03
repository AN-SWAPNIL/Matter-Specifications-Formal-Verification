# Door Lock Cluster Attack Simulation & Violation Analysis

## Document Information

| Field         | Value                                        |
| ------------- | -------------------------------------------- |
| Cluster       | Door Lock (0x0101)                           |
| PICS Code     | DRLK                                         |
| Specification | Matter 1.5 Application Cluster Specification |
| Section       | 5.2 (Pages 397-476)                          |
| Analysis Date | 2026-03-03                                   |
| FSM Model     | door_lock_fsm.json                           |

---

## Executive Summary

This document presents detailed attack simulations for **6 confirmed vulnerabilities** identified through deep analysis of the Door Lock cluster against the Matter 1.5 specification. Each vulnerability was verified by:

1. **FSM State Tracing** - Mapping attack paths through the FSM model
2. **Specification Evidence** - Direct quotes with page citations
3. **Counterexample Construction** - Concrete attack scenarios
4. **Physical Impact Assessment** - Real-world safety implications
5. **Core Specification Cross-Verification** - Checked against Matter Core Spec for additional protections

### Vulnerability Overview

| ID       | Name                                    | Severity | Physical Impact                      |
| -------- | --------------------------------------- | -------- | ------------------------------------ |
| VULN-001 | PIN Brute Force Protection Insufficient | HIGH     | Unauthorized physical entry          |
| VULN-002 | RequirePIN Optional/No Default          | CRITICAL | Remote unlock without authentication |
| VULN-003 | UnlockWithTimeout No Maximum            | HIGH     | Extended unlocked window (18h)       |
| VULN-004 | Counter Reset MAY Clause                | MEDIUM   | Weakens brute force protection       |
| VULN-005 | Cross-Fabric User Status Modification   | HIGH     | DoS via user lockout                 |
| VULN-007 | ClearAliroReaderConfig No Enforcement   | HIGH     | Mass Aliro credential revocation     |

**Note:** VULN-006 (DisposableUser Re-enable) was determined to be **expected admin functionality** after deep analysis and is NOT a vulnerability.

---

## Core Specification Verification

All 6 vulnerabilities were cross-checked against the Matter 1.5 Core Specification to determine if any are protected at the protocol level. The following topics were searched using GraphRAG (Neo4j + Qdrant):

| Topic                       | Core Spec Finding                                                                        | Protection |
| --------------------------- | ---------------------------------------------------------------------------------------- | ---------- |
| Brute Force / Rate Limiting | Message-layer counters (Page 133) for replay detection only. No app-layer rate limiting. | **NONE**   |
| Remote Auth Requirements    | ACL provides fabric-level command access. No mandatory app-layer PIN verification.       | **NONE**   |
| Timeout Constraints         | Fail-safe timers (Page 857-859) for commissioning only. No operational command timeouts. | **NONE**   |
| Fabric Data Isolation       | ACL entries are fabric-scoped (FabricIndex). User data attributes NOT fabric-isolated.   | **NONE**   |
| Confirmation Mechanism      | SHOULD for consent on critical ops (RemoveFabric). Not mandatory. OTA consent unrelated. | **NONE**   |

**Result: All 6 vulnerabilities are NOT protected by the Matter Core Specification.** The vulnerabilities exist at the Application Cluster level and must be addressed through specification errata or implementation hardening.

---

## Attack Simulation 1: PIN Brute Force Enumeration

### VULN-001: PIN_Brute_Force_Protection_Insufficient

#### Vulnerability Description

The specification allows WrongCodeEntryLimit range of 1-255 attempts and UserCodeTemporaryDisableTime range of 1-255 seconds. Combined with the MAY clause allowing arbitrary counter reset, this creates practical brute force conditions.

#### Specification Evidence

```
Quote: "This attribute SHALL indicate the number of incorrect Pin codes or RFID
presentation attempts a user is allowed to enter before the lock will enter a
lockout state. [...] Valid range is 1-255 incorrect attempts."
Source: Section 5.2.9.32, Page 428
```

```
Quote: "This attribute SHALL indicate the number of seconds that the lock shuts
down following wrong code entry. Valid range is 1-255 seconds."
Source: Section 5.2.9.33, Page 428
```

```
Quote: "The lock MAY reset the counter used to track incorrect credential
presentations as required by internal logic, environmental events, or other reasons."
Source: Section 5.2.9.32, Page 428
```

#### FSM State Trace

```
Initial State: Locked_Normal
Variables: WrongCodeEntryLimit=255, UserCodeTemporaryDisableTime=1, WrongCodeCount=0

ATTACK CYCLE (repeat):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Enumeration (255 attempts)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ FOR i = 1 TO 255:                                                            │
│   State: Locked_Normal                                                       │
│   Trigger: UnlockDoor(PINCode=GUESS[i])                                      │
│   Guard: PINCode_invalid && WrongCodeCount < WrongCodeEntryLimit             │
│   Action: WrongCodeCount++, generate_event(LockOperationError)               │
│   Result: WrongCodeCount = i                                                 │
│                                                                              │
│ When i = 255:                                                                │
│   Trigger: UnlockDoor(PINCode=GUESS[255])                                    │
│   Guard: WrongCodeCount >= WrongCodeEntryLimit                               │
│   Transition: T009_WrongPIN_Lockout                                          │
│   State: Locked_Normal → UserCodeDisabled                                    │
│   Action: UserCodeTemporaryDisabled := true, lockout_timer := 1              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Wait 1 second                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ State: UserCodeDisabled                                                      │
│ Timer: lockout_timer countdown                                               │
│ When: lockout_timer == 0                                                     │
│   Transition: T010_LockoutExpiry                                             │
│   State: UserCodeDisabled → Locked_Normal                                    │
│   Action: UserCodeTemporaryDisabled := false, WrongCodeCount := 0            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Repeat with next 255 guesses                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Attack Metrics

| PIN Length | Combinations | Cycles Required | Total Time (worst case) |
| ---------- | ------------ | --------------- | ----------------------- |
| 4-digit    | 10,000       | 40              | 40 × 256s = 2.8 hours   |
| 5-digit    | 100,000      | 393             | 28 hours                |
| 6-digit    | 1,000,000    | 3,922           | 11.6 days               |

**Throughput**: 255 guesses / 256 seconds ≈ **1 PIN/second sustained**

#### Attack Script Pseudocode

```python
def bruteforce_door_lock(target_lock, pin_length=4):
    """
    Matter Door Lock PIN Brute Force Attack
    Requires: Operate privilege on target lock
    """
    # Read lock configuration
    limit = target_lock.read("WrongCodeEntryLimit")  # Assume 255
    disable_time = target_lock.read("UserCodeTemporaryDisableTime")  # Assume 1

    pin_space = 10 ** pin_length  # 10000 for 4-digit
    attempt = 0

    while attempt < pin_space:
        # Phase 1: Send limit attempts
        for i in range(limit):
            pin_guess = str(attempt).zfill(pin_length)
            response = target_lock.invoke("UnlockDoor", PINCode=pin_guess)

            if response.status == "SUCCESS":
                print(f"[+] PIN FOUND: {pin_guess}")
                return pin_guess

            attempt += 1
            if attempt >= pin_space:
                break

        # Phase 2: Wait for lockout to expire
        sleep(disable_time + 0.5)  # Add buffer

        # Phase 3: Counter automatically reset - continue

    print("[-] PIN not found")
    return None
```

#### Physical Safety Impact

**UNAUTHORIZED PHYSICAL ENTRY**

An attacker with network access (compromised controller, rogue commissioner) can:

1. Enumerate 4-digit PINs in ~3 hours
2. Gain physical access to protected premises
3. Conduct burglary, harm occupants, or plant surveillance

---

## Attack Simulation 2: Remote Unlock Without Authentication

### VULN-002: RequirePIN_Optional_Default_Unspecified

#### Vulnerability Description

The `RequirePINForRemoteOperation` attribute has conditional conformance "COTA & PIN", meaning it only exists when both features are present. When FALSE or absent, the UnlockDoor command succeeds with just Operate privilege - no PIN required.

#### Specification Evidence

```
Quote: "The door lock MAY require a code depending on the value of the
RequirePINForRemoteOperation attribute."
Source: Section 5.2.10.2, Page 433
Keyword: MAY (not SHALL)
```

```
Attribute Table:
RequirePINforRemoteOperation | bool | P | R[W] VA | COTA & PIN
Conformance: COTA & PIN (conditional, not mandatory)
Source: Section 5.2.9, Page 422
```

#### FSM State Trace

```
Precondition: RequirePINForRemoteOperation = FALSE (or attribute absent)

Initial State: Locked_Normal
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: Attacker sends UnlockDoor command (no PINCode field)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ State: Locked_Normal                                                         │
│ Trigger: UnlockDoor (from remote, no PINCode)                                │
│ Transition: T003_UnlockDoor_Success                                          │
│ Guard Evaluation:                                                            │
│   OperatingMode IN [Normal, Vacation] → TRUE                                 │
│   ActuatorEnabled → TRUE                                                     │
│   (!RequirePINForRemoteOperation || PINCode_valid)                           │
│     → !FALSE || (not provided)                                               │
│     → TRUE || X                                                              │
│     → TRUE ✓                                                                 │
│                                                                              │
│ Result: Guard PASSES - no PIN required                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Step 2: Door unlocks                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ State: Locked_Normal → Unlocked_Normal                                       │
│ Action: LockState := Unlocked                                                │
│ Event: LockOperation(Unlock, Remote, null, FabricIndex, NodeID)              │
│                                                                              │
│ PHYSICAL ACCESS GRANTED WITHOUT CREDENTIAL VERIFICATION                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Attack Scenario

```
ATTACKER PROFILE: Network access with Operate privilege
- Compromised Matter controller
- Rogue commissioner who gained access to fabric
- Malicious app with controller privileges

ATTACK EXECUTION:
1. Attacker reads RequirePINForRemoteOperation attribute
   → Returns FALSE or NOT_FOUND

2. Attacker sends: UnlockDoor command (no PINCode field)
   → Lock evaluates guard: !FALSE = TRUE
   → Command succeeds
   → Door unlocks

3. Attacker walks through door
   → No physical credential required
   → Only network access needed
```

#### Physical Safety Impact

**COMPLETE BYPASS OF PHYSICAL ACCESS CONTROL**

This vulnerability transforms the door lock from "physical security + network security" to "network security only". A single compromised Matter controller grants physical access to ALL locks in that fabric that have this attribute FALSE.

**Severity**: CRITICAL

---

## Attack Simulation 3: Extended Unlock Window

### VULN-003: UnlockWithTimeout_No_Maximum_Duration

#### Vulnerability Description

The UnlockWithTimeout command accepts a uint16 Timeout field with no constraint specified. Maximum value 65535 seconds = **18.2 hours** of continuous unlock.

#### Specification Evidence

```
Command Schema:
| ID | Name    | Type   | Constraint | Quality | Fallback | Conformance |
|----|---------|--------|------------|---------|----------|-------------|
| 0  | Timeout | uint16 |            |         |          | M           |

Source: Section 5.2.10.3, Page 433
Note: Constraint column is EMPTY
```

```
Quote: "This value is independent of the AutoRelockTime attribute value."
Source: Section 5.2.10.3.1, Page 434
```

#### FSM State Trace

```
Initial State: Locked_Normal

┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: Attacker sends UnlockWithTimeout(65535)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ State: Locked_Normal                                                         │
│ Trigger: UnlockWithTimeout(Timeout=65535)                                    │
│ Transition: T005_UnlockWithTimeout_Success                                   │
│ Guard: OperatingMode IN [Normal, Vacation] && ActuatorEnabled → TRUE        │
│ Action:                                                                      │
│   LockState := Unlocked                                                      │
│   timeout_timer := 65535  (18.2 hours)                                       │
│                                                                              │
│ Result: Door unlocks for 18+ hours                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Step 2: Extended window                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ State: Unlocked_Normal                                                       │
│ For next 65535 seconds:                                                      │
│   - Door remains unlocked                                                    │
│   - No manual intervention triggers relock                                   │
│   - AutoRelockTime is overridden                                             │
│                                                                              │
│ Attack window: ENTIRE BUSINESS DAY or OVERNIGHT                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Attack Use Cases

1. **Opportunistic Entry**: Unlock before leaving work, return overnight
2. **Accomplice Entry**: Unlock remotely, accomplice enters at leisure
3. **Surveillance Placement**: Extended access for installing devices
4. **Evidence Tampering**: Long window for document/device access

#### Physical Safety Impact

**EXTENDED UNAUTHORIZED ACCESS WINDOW**

Even if detected, 18 hours provides ample time for:

- Complete premises search
- Installation of surveillance equipment
- Theft of valuables
- Physical harm to occupants

---

## Attack Simulation 4: Cross-Fabric User Lockout

### VULN-005: FabricIndex_Cross_Fabric_User_Status_Modification

#### Vulnerability Description

While the specification protects UserName and UserUniqueID with fabric isolation (INVALID_COMMAND if cross-fabric modification attempted), it does NOT protect UserStatus and UserType fields. Any admin from any fabric can disable users created by other fabrics.

#### Specification Evidence

```
Quote (Page 453, SetUser Modify use case):
"UserName SHALL be null if modifying a user record that was not created by the
accessing fabric."
"INVALID_COMMAND SHALL be returned if UserName is not null and the accessing
fabric index doesn't match the CreatorFabricIndex"

BUT:

"UserStatus MAY be null causing no change to UserStatus in user record otherwise
UserStatus SHALL be set to the value provided in the user record."
"UserType MAY be null causing no change to UserType in user record otherwise
UserType SHALL be set to the value provided in the user record."

Note: NO fabric isolation check for UserStatus/UserType
```

#### FSM State Trace

```
Setup:
- Fabric A (legitimate admin) creates User at index 5:
    User[5] = {UserName: "Alice", UserStatus: OccupiedEnabled,
               CreatorFabricIndex: A, ...}
- User Alice has valid credentials and can access lock

Attack:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: Rogue admin on Fabric B reads user database                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Trigger: GetUser(UserIndex=5)                                                │
│ Response: {UserStatus: OccupiedEnabled, CreatorFabricIndex: A, ...}          │
│                                                                              │
│ Attacker identifies: User 5 was created by Fabric A, is enabled             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Step 2: Fabric B admin disables user                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Trigger: SetUser(OperationType=Modify, UserIndex=5,                          │
│                  UserName=null,  // Required null for cross-fabric           │
│                  UserUniqueID=null,  // Required null for cross-fabric       │
│                  UserStatus=OccupiedDisabled,  // NO PROTECTION              │
│                  UserType=NonAccessUser)  // NO PROTECTION                   │
│                                                                              │
│ Transition: T012_SetUser_Modify                                              │
│ Guard: UserStatus != null → TRUE                                             │
│ Action:                                                                      │
│   User[5].UserStatus := OccupiedDisabled                                     │
│   User[5].UserType := NonAccessUser                                          │
│   User[5].LastModifiedFabricIndex := B                                       │
│                                                                              │
│ Result: Command SUCCEEDS (no INVALID_COMMAND)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Step 3: Legitimate user Alice denied access                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Alice attempts: UnlockDoor(PINCode=valid)                                    │
│ Guard: User.UserStatus != OccupiedDisabled → FALSE                           │
│ Result: Access DENIED                                                        │
│ Event: LockOperationError(DisabledUserDenied)                                │
│                                                                              │
│ LEGITIMATE USER LOCKED OUT BY ROGUE ADMIN FROM DIFFERENT FABRIC             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Physical Safety Impact

**DENIAL OF ACCESS ATTACK**

- Legitimate users cannot enter their own premises
- Emergency situations become dangerous (fire, medical)
- Business operations disrupted
- Trust in multi-admin deployments compromised

---

## Attack Simulation 5: Mass Aliro Credential Revocation

### VULN-007: ClearAliroReaderConfig_DoS_No_Enforcement

#### Vulnerability Description

The specification states "Administrators SHALL NOT clear an Aliro Reader configuration without explicit user permission" but provides NO enforcement mechanism. A single command revokes ALL Aliro credentials across ALL fabrics.

#### Specification Evidence

```
Quote: "Administrators SHALL NOT clear an Aliro Reader configuration without
explicit user permission."
Source: Section 5.2.10.43, Page 470
Keyword: SHALL NOT (but no enforcement)
```

```
Quote: "Using this command will revoke the ability of all existing Aliro user
devices that have the old verification key to interact with the lock. This
effect is not restricted to a single fabric or otherwise scoped in any way."
Source: Section 5.2.10.43 NOTE, Page 470
```

#### FSM State Trace

```
Precondition: Lock has Aliro configured with multiple users across fabrics

┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: Rogue admin sends ClearAliroReaderConfig                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ State: AliroConfigured                                                       │
│ Trigger: ClearAliroReaderConfig                                              │
│ Transition: T018_ClearAliroReaderConfig                                      │
│ Guard: Feature_ALIRO == true → TRUE                                          │
│ Access: Administer (rogue admin has this)                                    │
│                                                                              │
│ NO CONFIRMATION MECHANISM                                                    │
│ NO ENFORCEMENT OF "EXPLICIT USER PERMISSION"                                 │
│                                                                              │
│ Action:                                                                      │
│   SigningKey := CLEARED                                                      │
│   AliroReaderVerificationKey := null                                         │
│   AliroReaderGroupIdentifier := null                                         │
│   AliroGroupResolvingKey := null (if ALBU feature)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Step 2: ALL Aliro users lose access                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Impact:                                                                      │
│   - ALL phones with Aliro credentials → INVALID                              │
│   - ALL smartwatches with Aliro → INVALID                                    │
│   - ALL fabrics affected (not scoped to attacker's fabric)                   │
│   - Recovery requires re-provisioning ALL devices                            │
│                                                                              │
│ SINGLE COMMAND DESTROYS ALL ALIRO ACCESS                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Physical Safety Impact

**MASS DENIAL OF SERVICE**

- All Aliro-based access instantly revoked
- Users locked out of premises
- Recovery requires physical presence of admin
- Business/residential operations severely disrupted

---

## Verified Non-Vulnerabilities

### VULN-006: DisposableUser Re-enable (Reclassified)

After deep analysis, this was determined to be **expected administrative functionality**:

1. **Single-use semantic IS enforced**: Lock auto-disables after first use (Page 415)
2. **Admin re-enablement is intentional design**: Admins should control all user states
3. **Requires full Administer privilege**: Not accessible to regular users
4. **Legitimate use case exists**: Guest didn't use code, needs another attempt

**Verdict**: NOT A VULNERABILITY - Expected admin functionality

---

## Attack Summary Matrix

| Attack                    | Privilege Required | Complexity | Detection | Physical Impact |
| ------------------------- | ------------------ | ---------- | --------- | --------------- |
| PIN Brute Force           | Operate            | Low        | Medium    | Entry           |
| Remote Unlock (no PIN)    | Operate            | Very Low   | Low       | Entry           |
| Extended Unlock Window    | Operate            | Low        | Low       | Entry           |
| Cross-Fabric User Lockout | Administer         | Medium     | Medium    | Lockout         |
| Aliro Mass Revocation     | Administer         | Very Low   | Medium    | Lockout         |

---

## Detection Indicators

### Events to Monitor

| Event                                  | Indicates                      | Priority         |
| -------------------------------------- | ------------------------------ | ---------------- |
| LockOperationError (InvalidCredential) | Brute force attempt            | HIGH if repeated |
| DoorLockAlarm (WrongCodeEntryLimit)    | Lockout triggered              | HIGH             |
| LockUserChange (SourceRemote)          | Cross-fabric user modification | MEDIUM           |
| LockOperation (Unlock, long duration)  | Extended unlock                | MEDIUM           |

### Anomaly Patterns

1. **Brute Force**: > 10 LockOperationError events in 10 minutes
2. **Unauthorized Remote**: LockOperation(Unlock) without prior LockUserChange
3. **Cross-Fabric Attack**: SetUser from fabric != CreatorFabricIndex

---

## Conclusion

The Door Lock cluster contains **6 confirmed specification-level vulnerabilities** that enable:

- **Physical unauthorized entry** via PIN brute force or remote unlock
- **Extended access windows** via unbounded timeout
- **Denial of service** via cross-fabric user modification or Aliro revocation

All vulnerabilities stem from **specification gaps**, not implementation flaws. Mitigation requires either specification updates or implementation-level hardening beyond spec requirements.
