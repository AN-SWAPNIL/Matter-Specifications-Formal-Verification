# Door Lock Cluster Defense Summary & Final Findings

## Document Information

| Field          | Value                                        |
| -------------- | -------------------------------------------- |
| Cluster        | Door Lock (0x0101)                           |
| PICS Code      | DRLK                                         |
| Specification  | Matter 1.5 Application Cluster Specification |
| Pages          | 397-476                                      |
| Analysis Date  | 2026-03-03                                   |
| Analysis Phase | Complete Property Violation Analysis         |

---

## Analysis Summary

### Work Completed

| Phase                           | Description                                     | Status      |
| ------------------------------- | ----------------------------------------------- | ----------- |
| 1. FSM Extraction               | 27 transitions, 16 states, 5 events, 4 timers   | ✅ Complete |
| 2. Security Property Extraction | 47 properties across 10 categories              | ✅ Complete |
| 3. Property Violation Analysis  | Deep verification against spec                  | ✅ Complete |
| 4. Attack Simulation            | 5 detailed attack scenarios                     | ✅ Complete |
| 5. Defense Summary              | This document                                   | ✅ Complete |
| 6. Core Spec Cross-Verification | Check if vulnerabilities protected by core spec | ✅ Complete |

### Artifacts Generated

| File                                    | Description                                       |
| --------------------------------------- | ------------------------------------------------- |
| `door_lock_fsm.json`                    | Formal FSM model with states, transitions, guards |
| `door_lock_security_properties.json`    | 47 security properties with severity              |
| `door_lock_vulnerability_analysis.json` | Verified analysis with spec citations + core_spec |
| `door_lock_attack_simulation.md`        | Attack traces and impact analysis                 |
| `door_lock_defense_summary.md`          | This document                                     |

---

## Core Specification Verification

All vulnerabilities were cross-checked against the Matter 1.5 Core Specification using GraphRAG hybrid search:

| Vulnerability                  | Core Spec Topic Searched   | Finding                               | Protected? |
| ------------------------------ | -------------------------- | ------------------------------------- | ---------- |
| VULN-001 (PIN Brute Force)     | Brute force, rate limiting | Message counters for replay only      | ❌ NO      |
| VULN-002 (RequirePIN Optional) | Remote auth requirements   | ACL = fabric-level, not app-layer PIN | ❌ NO      |
| VULN-003 (Timeout No Max)      | Timeout constraints        | Commissioning fail-safe only          | ❌ NO      |
| VULN-004 (Counter Reset)       | Rate limiting mechanisms   | None at protocol level                | ❌ NO      |
| VULN-005 (Cross-Fabric)        | Fabric isolation           | ACL scoped, user data NOT isolated    | ❌ NO      |
| VULN-007 (ClearAliro)          | Confirmation mechanism     | SHOULD consent (not SHALL)            | ❌ NO      |

**Conclusion:** All 6 vulnerabilities exist at the Application Cluster level. The Matter Core Specification provides transport-layer security and fabric-scoped ACL, but **no application-layer protections** for these specific gaps.

---

## Final Vulnerability Findings

### Confirmed Vulnerabilities (6)

| ID       | Name                                    | Severity | Status    |
| -------- | --------------------------------------- | -------- | --------- |
| VULN-001 | PIN Brute Force Protection Insufficient | HIGH     | CONFIRMED |
| VULN-002 | RequirePIN Optional/No Default          | CRITICAL | CONFIRMED |
| VULN-003 | UnlockWithTimeout No Maximum            | HIGH     | CONFIRMED |
| VULN-004 | Counter Reset MAY Clause                | MEDIUM   | CONFIRMED |
| VULN-005 | Cross-Fabric User Status Modification   | HIGH     | CONFIRMED |
| VULN-007 | ClearAliroReaderConfig DoS              | HIGH     | CONFIRMED |

### False Positive Removed (1)

| ID       | Name                     | Original Verdict | Final Verdict       | Reason                       |
| -------- | ------------------------ | ---------------- | ------------------- | ---------------------------- |
| VULN-006 | DisposableUser Re-enable | VIOLATED         | NOT_A_VULNERABILITY | Expected admin functionality |

---

## Detailed Vulnerability Analysis with Mitigations

### VULN-001: PIN Brute Force Protection Insufficient

#### Root Cause

- WrongCodeEntryLimit range: 1-255 (no minimum recommended)
- UserCodeTemporaryDisableTime range: 1-255 seconds (trivial)
- MAY clause allows arbitrary counter reset

#### Specification Gap Citations

- Page 428: "Valid range is 1-255 incorrect attempts"
- Page 428: "Valid range is 1-255 seconds"
- Page 428: "The lock MAY reset the counter"

#### Attack Impact

- 4-digit PIN cracked in ~3 hours
- 6-digit PIN cracked in ~12 days
- Unauthorized physical entry

#### Recommended Mitigations

**Specification-Level (Requires CSA Action)**

```
CHANGE FROM: "Valid range is 1-255 incorrect attempts"
CHANGE TO:   "Valid range is 3-255 incorrect attempts. Implementations
              SHOULD NOT use values greater than 10."

CHANGE FROM: "Valid range is 1-255 seconds"
CHANGE TO:   "Valid range is 30-86400 seconds. Implementations SHOULD
              use at least 60 seconds."

ADD: "The lock SHALL implement exponential backoff, doubling the lockout
      duration after each consecutive lockout cycle."

CHANGE FROM: "The lock MAY reset the counter"
CHANGE TO:   "The lock SHALL NOT reset the counter except when a valid
              credential is presented."
```

**Implementation-Level (Immediate)**
| Attribute | Minimum Recommended | Maximum Recommended |
|-----------|--------------------|--------------------|
| WrongCodeEntryLimit | 5 | 10 |
| UserCodeTemporaryDisableTime | 60 | 300 |

```json
{
  "implementation_hardening": {
    "WrongCodeEntryLimit": 5,
    "UserCodeTemporaryDisableTime": 60,
    "exponential_backoff": true,
    "backoff_multiplier": 2.0,
    "max_lockout_duration": 3600,
    "permanent_lockout_threshold": 10
  }
}
```

---

### VULN-002: RequirePIN Optional/No Default

#### Root Cause

- RequirePINForRemoteOperation conformance: "COTA & PIN" (conditional)
- No default value specified
- "MAY require a code" language (not SHALL)

#### Specification Gap Citations

- Page 422: Conformance "COTA & PIN" (optional)
- Page 433: "The door lock MAY require a code"

#### Attack Impact

- Remote unlock without authentication
- Single compromised controller = all locks accessible

#### Recommended Mitigations

**Specification-Level (Requires CSA Action)**

```
CHANGE FROM: RequirePINForRemoteOperation Conformance: COTA & PIN
CHANGE TO:   RequirePINForRemoteOperation Conformance: M (when PIN supported)

ADD: "Default value: TRUE. Implementations SHALL NOT ship with
      RequirePINForRemoteOperation set to FALSE."

CHANGE FROM: "The door lock MAY require a code"
CHANGE TO:   "The door lock SHALL require a code for remote operations
              when the RequirePINForRemoteOperation attribute is TRUE."
```

**Implementation-Level (Immediate)**

```json
{
  "implementation_hardening": {
    "RequirePINForRemoteOperation_default": true,
    "RequirePINForRemoteOperation_writable": false,
    "admin_only_disable": true
  }
}
```

**Deployment Guidance**

- Always set RequirePINForRemoteOperation = TRUE during commissioning
- Audit all locks for this attribute weekly
- Alert on any change to FALSE

---

### VULN-003: UnlockWithTimeout No Maximum

#### Root Cause

- Timeout field type: uint16 (max 65535)
- No constraint specified
- "independent of AutoRelockTime"

#### Specification Gap Citations

- Page 433: Timeout constraint column EMPTY
- Page 434: "This value is independent of the AutoRelockTime attribute value"

#### Attack Impact

- 18+ hour unlock window
- Extended access for unauthorized entry

#### Recommended Mitigations

**Specification-Level (Requires CSA Action)**

```
CHANGE FROM: Timeout | uint16 | (no constraint)
CHANGE TO:   Timeout | uint16 | max 3600

ADD: "Implementations SHALL reject Timeout values greater than 3600
      seconds (1 hour) with CONSTRAINT_ERROR."

ADD: "If AutoRelockTime is supported and Timeout exceeds AutoRelockTime,
      implementations SHOULD use the minimum of Timeout and AutoRelockTime."
```

**Implementation-Level (Immediate)**

```json
{
  "implementation_hardening": {
    "max_unlock_timeout": 3600,
    "reject_excessive_timeout": true,
    "use_autorelock_minimum": true
  }
}
```

---

### VULN-004: Counter Reset MAY Clause

#### Root Cause

- MAY clause permits arbitrary implementation behavior
- Counter reset defeats brute force protection

#### Specification Gap Citation

- Page 428: "The lock MAY reset the counter used to track incorrect credential presentations as required by internal logic, environmental events, or other reasons"

#### Attack Impact

- Enables sustained brute force via VULN-001
- Implementation-dependent protection level

#### Recommended Mitigations

**Specification-Level (Requires CSA Action)**

```
CHANGE FROM: "The lock MAY reset the counter"
CHANGE TO:   "The lock SHALL NOT reset the counter except:
              a) When a valid credential is presented
              b) On explicit ClearCredentialAttempts command (new, Administer)
              c) After 24 hours of no attempts
              The counter SHALL persist across power cycles."
```

**Implementation-Level (Immediate)**

- Persist counter in non-volatile storage
- Only reset on valid credential
- Log all counter resets to event stream

---

### VULN-005: Cross-Fabric User Status Modification

#### Root Cause

- Fabric isolation applies to UserName and UserUniqueID only
- UserStatus and UserType can be modified by ANY admin fabric

#### Specification Gap Citations

- Page 453: "INVALID_COMMAND SHALL be returned if UserName is not null and the accessing fabric index doesn't match"
- Page 453: "UserStatus MAY be null... otherwise UserStatus SHALL be set to the value provided" (NO fabric check)

#### Attack Impact

- Rogue admin fabric can disable users from other fabrics
- Denial of access for legitimate users

#### Recommended Mitigations

**Specification-Level (Requires CSA Action)**

```
ADD: "SetUser command with OperationType=Modify SHALL return
      INVALID_COMMAND if UserStatus is not null AND the accessing
      fabric index doesn't match the CreatorFabricIndex in the
      user record."

ADD: "SetUser command with OperationType=Modify SHALL return
      INVALID_COMMAND if UserType is not null AND the accessing
      fabric index doesn't match the CreatorFabricIndex in the
      user record."
```

**Implementation-Level (Immediate)**

```json
{
  "implementation_hardening": {
    "fabric_isolation_user_status": true,
    "fabric_isolation_user_type": true,
    "cross_fabric_notification": true
  }
}
```

---

### VULN-007: ClearAliroReaderConfig DoS

#### Root Cause

- "SHALL NOT clear without explicit user permission" but NO enforcement
- Single command revokes ALL Aliro credentials across ALL fabrics
- No confirmation mechanism

#### Specification Gap Citations

- Page 470: "Administrators SHALL NOT clear an Aliro Reader configuration without explicit user permission"
- Page 470: "This effect is not restricted to a single fabric or otherwise scoped in any way"

#### Attack Impact

- Mass denial of service for all Aliro users
- Single command destroys all Aliro access

#### Recommended Mitigations

**Specification-Level (Requires CSA Action)**

```
ADD: "Upon receipt of ClearAliroReaderConfig:
      1. The lock SHALL enter a 60-second pending state
      2. The lock SHALL notify all fabrics via LockUserChange event
      3. Any fabric MAY cancel the pending clear via new
         CancelAliroReaderConfigClear command
      4. The lock SHALL require physical button press confirmation
      5. Only after confirmation shall the clear proceed"

ADD: "ClearAliroReaderConfig command SHALL require Administer
      privilege on the SAME fabric that performed SetAliroReaderConfig"
```

**Implementation-Level (Immediate)**

- Require physical button confirmation
- Add 60-second delay with notification
- Log to audit trail before clearing
- Backup credentials if possible

---

## Defense Architecture Recommendations

### Network Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEFENSE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Network Segmentation                                   │
│  - Isolate Matter Thread/WiFi network                           │
│  - Firewall rules for Matter ports                              │
│  - VPN for remote access                                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Access Control                                         │
│  - Minimize nodes with Operate privilege                        │
│  - Zero Administer privileges for untrusted devices             │
│  - Regular credential rotation                                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Monitoring                                             │
│  - Subscribe to all Door Lock events                            │
│  - Alert on LockOperationError patterns                         │
│  - Alert on cross-fabric modifications                          │
│  - Daily audit of RequirePINForRemoteOperation                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Physical                                               │
│  - Enable DoorPositionSensor (DPS feature)                      │
│  - Configure DoorForcedOpen alarms                              │
│  - Secondary authentication for high-security areas             │
└─────────────────────────────────────────────────────────────────┘
```

### Event Monitoring Rules

```yaml
# SIEM Rules for Door Lock Security
rules:
  - name: brute_force_detection
    condition: count(LockOperationError) > 10 in 10m
    severity: CRITICAL
    action: alert_security_team

  - name: unauthorized_remote_unlock
    condition: |
      LockOperation.type == "Unlock" AND
      LockOperation.source == "Remote" AND
      RequirePINForRemoteOperation == FALSE
    severity: HIGH
    action: alert_and_investigate

  - name: cross_fabric_modification
    condition: |
      LockUserChange.OperationSource == "Remote" AND
      LockUserChange.FabricIndex != User.CreatorFabricIndex
    severity: HIGH
    action: alert_admin

  - name: extended_unlock_window
    condition: |
      UnlockWithTimeout.Timeout > 3600
    severity: MEDIUM
    action: log_and_alert

  - name: aliro_config_cleared
    condition: |
      LockUserChange.LockDataType == "AliroCredentialIssuerKey" AND
      LockUserChange.DataOperationType == "Clear"
    severity: CRITICAL
    action: immediate_investigation
```

---

## Security Posture Assessment

### Current Risk Level: MODERATE-HIGH

| Category        | Status      | Notes                                     |
| --------------- | ----------- | ----------------------------------------- |
| Authentication  | ⚠️ WEAK     | RequirePIN optional, brute force feasible |
| Authorization   | ✅ STRONG   | Access levels correctly enforced          |
| Integrity       | ⚠️ MODERATE | Cross-fabric modification possible        |
| Availability    | ⚠️ WEAK     | Aliro DoS, user lockout possible          |
| Physical Safety | ⚠️ AT RISK  | Unauthorized entry possible               |

### Risk Score

```
Risk = Likelihood × Impact

VULN-001: 0.7 × 0.9 = 0.63 (HIGH)
VULN-002: 0.6 × 1.0 = 0.60 (HIGH)
VULN-003: 0.4 × 0.7 = 0.28 (MEDIUM)
VULN-004: 0.5 × 0.5 = 0.25 (MEDIUM)
VULN-005: 0.3 × 0.8 = 0.24 (MEDIUM)
VULN-007: 0.3 × 0.9 = 0.27 (MEDIUM)

Overall Risk Score: 0.63 (HIGH - driven by brute force and RequirePIN)
```

---

## Compliance Mapping

### Properties That HOLD (Security Requirements Met)

| Property                                    | Specification Support | Notes                             |
| ------------------------------------------- | --------------------- | --------------------------------- |
| AC-001: OperateLevelLockCommands            | ✅                    | Access levels correctly defined   |
| AC-002: AdminLevelCredentialManagement      | ✅                    | SetCredential requires Administer |
| AC-006: TimedInteractionForCriticalCommands | ✅                    | 'T' required on critical commands |
| SI-003: OperatingModeConstraints            | ✅                    | Privacy mode blocks remote        |
| AU-001: RequirePIN When Set                 | ✅                    | SHALL when attribute TRUE         |
| AU-002: PINVerificationMandatory            | ✅                    | Always verified when provided     |
| PS-002: DoorForcedOpenDetection             | ✅                    | DPS conformance                   |
| AZ-008: ForcedUserSilentAlarm               | ✅                    | ForcedUser alarm mandatory        |
| EI-001: DoorLockAlarmGeneration             | ✅                    | CRITICAL priority enforced        |
| SP-002: AliroSigningKeyProtection           | ✅                    | Key stored internally only        |

---

## Recommended Actions by Priority

### P0 - CRITICAL (Immediate)

| Action                                               | Type       | Owner      | Timeline |
| ---------------------------------------------------- | ---------- | ---------- | -------- |
| Set RequirePINForRemoteOperation = TRUE on all locks | Config     | Operations | 24 hours |
| Audit WrongCodeEntryLimit/DisableTime values         | Config     | Operations | 24 hours |
| Enable event monitoring for brute force patterns     | Monitoring | Security   | 48 hours |

### P1 - HIGH (This Week)

| Action                                     | Type       | Owner       | Timeline |
| ------------------------------------------ | ---------- | ----------- | -------- |
| Implement client-side timeout cap (1 hour) | Code       | Development | 5 days   |
| Add exponential backoff to lock firmware   | Code       | Development | 5 days   |
| Deploy cross-fabric modification alerts    | Monitoring | Security    | 3 days   |

### P2 - MEDIUM (This Month)

| Action                                      | Type    | Owner       | Timeline |
| ------------------------------------------- | ------- | ----------- | -------- |
| Submit specification change requests to CSA | Process | Engineering | 30 days  |
| Implement fabric isolation for UserStatus   | Code    | Development | 30 days  |
| Add Aliro config clear confirmation         | Code    | Development | 30 days  |

---

## Conclusion

The Door Lock cluster (0x0101) in Matter 1.5 contains **6 confirmed specification-level vulnerabilities** that could enable:

1. **Unauthorized physical entry** via PIN brute force or remote unlock without PIN
2. **Extended attack windows** via unbounded timeout
3. **Denial of service** via cross-fabric user modification or Aliro credential revocation

All vulnerabilities are **specification gaps** that require either:

- CSA specification amendments for complete resolution
- Implementation-level hardening beyond spec requirements for immediate mitigation

The analysis correctly identified and removed **1 false positive** (DisposableUser re-enable) which is expected administrative functionality.

**Recommendation**: Prioritize VULN-001 and VULN-002 mitigations as they directly enable unauthorized physical entry with network access alone.

---

## Appendix: Files Generated

| File                                  | Lines     | Purpose                     |
| ------------------------------------- | --------- | --------------------------- |
| door_lock_fsm.json                    | 1360      | Formal FSM model            |
| door_lock_security_properties.json    | 772       | 47 security properties      |
| door_lock_vulnerability_analysis.json | 836       | Verified violation analysis |
| door_lock_attack_simulation.md        | 500+      | Attack traces               |
| door_lock_defense_summary.md          | This file | Defense guidance            |
