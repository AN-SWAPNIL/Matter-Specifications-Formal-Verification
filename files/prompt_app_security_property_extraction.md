# Security Property Extraction for Application Cluster Verification

## Goal

Extract **all testable security properties** from Matter Application Cluster specifications with sufficient precision to:

1. **Formally verify** using ProVerif or reasoning-based verification
2. **Detect vulnerabilities** when properties are violated
3. **Enable FSM analysis** by identifying state-enforcing properties
4. **Identify attack vectors** for each potential violation
5. **Assess physical safety impact** for safety-critical clusters

---

## Application Cluster Security Categories

Unlike core protocol specifications (focused on cryptographic security), application clusters have unique security concerns:

| Category            | Core Protocol               | Application Cluster               |
| ------------------- | --------------------------- | --------------------------------- |
| **Primary Concern** | Key secrecy, authentication | Access control, authorization     |
| **Attack Surface**  | Network messages            | Commands, attribute writes        |
| **Impact**          | Data breach                 | Physical safety, privacy          |
| **Timing Attacks**  | Replay, MITM                | Race conditions, schedule bypass  |
| **DoS Vectors**     | Resource exhaustion         | Alarm suppression, remote disable |

---

## LLM Approach

### Step 1: Identify Requirements by Type

Search specification for:

**A. MANDATORY Requirements**:

- "SHALL", "MUST", "SHALL NOT", "MUST NOT"
- "is required", "needs to", "is necessary"

**B. RECOMMENDED Requirements** (apply filter in Step 2):

- "SHOULD", "SHOULD NOT"
- "is recommended", "ought to"

**C. SECURITY CLAIMS** (explicit or implicit):

- "only", "exclusively", "restricted to"
- "prevent", "protect", "secure", "authenticate"
- "access control", "privilege", "ACL"
- "authorized", "permitted", "allowed"

**D. SAFETY REQUIREMENTS**:

- "safe", "safety", "fail-safe"
- "physical", "emergency", "alarm"
- "obstruction", "detection", "interlock"

### Step 2: Filter SHOULD Statements

For each SHOULD requirement, ask:

1. **Security Question**: Can an attacker exploit if violated?
   - YES → Extract as MEDIUM importance property
2. **Safety Question**: Does violation create physical risk?
   - YES → Extract as HIGH/CRITICAL importance property
3. **Policy Question**: Is it pure administrative policy (no security/safety impact)?
   - YES → Skip, but document as operational guidance

### Step 3: Property Categories for Application Clusters

Extract properties from these **10 categories**:

#### 3.1 ACCESS CONTROL Properties

Who can execute what commands/modify which attributes?

| Pattern                              | Example                               | Formalization                             |
| ------------------------------------ | ------------------------------------- | ----------------------------------------- |
| Command requires privilege P         | "LockDoor requires Operate"           | `invoke(cmd) ⟹ has_privilege(invoker, O)` |
| Attribute write requires privilege P | "SetCredential is Admin-only"         | `write(attr) ⟹ has_privilege(writer, A)`  |
| Timed command required               | "SetUser SHALL use Timed Interaction" | `invoke(SetUser) ⟹ is_timed_invoke()`     |

#### 3.2 STATE INTEGRITY Properties

Can device reach invalid/dangerous states?

| Pattern           | Example                                        | Formalization                                |
| ----------------- | ---------------------------------------------- | -------------------------------------------- |
| State exclusivity | "Cannot be Locked and Unlocked simultaneously" | `¬(LockState==Locked ∧ LockState==Unlocked)` |
| Valid transitions | "Unlocking requires valid credential"          | `trans(Locked→Unlocked) ⟹ credential_valid`  |
| State bounds      | "SensitivityLevel ≤ MaxSupported"              | `∀t. SensitivityLevel(t) ≤ MaxSupported`     |

#### 3.3 PHYSICAL SAFETY Properties

Real-world safety implications

| Pattern               | Example                                | Formalization                         |
| --------------------- | -------------------------------------- | ------------------------------------- |
| Fail-safe default     | "Valve closes on fault"                | `ValveFault ⟹ ValveState==Closed`     |
| Obstruction detection | "Stop on PhysicallyBlocked"            | `PhysicallyBlocked ⟹ motion_stops()`  |
| Alarm integrity       | "Cannot suppress unacknowledged alarm" | `suppress(alarm) ⟹ user_acknowledged` |

#### 3.4 AUTHENTICATION Properties

Who can prove identity for access?

| Pattern                 | Example                                 | Formalization                                          |
| ----------------------- | --------------------------------------- | ------------------------------------------------------ |
| PIN validation          | "Unlock requires valid PIN"             | `unlock() ⟹ PIN_matches_stored()`                      |
| Credential verification | "Face credential must match user"       | `access_via(FaceCredential) ⟹ face_matches_enrolled()` |
| Remote auth             | "RequirePINForRemoteOperation enforced" | `remote_cmd() ∧ RequirePIN==true ⟹ PIN_provided()`     |

#### 3.5 SECRET PROTECTION Properties

Sensitive data handling

| Pattern                    | Example                               | Formalization                                       |
| -------------------------- | ------------------------------------- | --------------------------------------------------- |
| PIN not leaked             | "SendPINOverTheAir controls exposure" | `SendPINOverTheAir==false ⟹ PIN_redacted_in_msgs()` |
| Credential data protection | "CredentialData not readable"         | `¬∃cmd. read(CredentialData)`                       |
| Key material isolation     | "Aliro keys fabric-scoped"            | `read(AliroKey, fabric_A) ⟹ key_from_fabric_A`      |

#### 3.6 AVAILABILITY Properties

Can service be denied?

| Pattern           | Example                                 | Formalization                      |
| ----------------- | --------------------------------------- | ---------------------------------- |
| No remote disable | "Cannot permanently lock out users"     | `¬∀u. disabled(u)`                 |
| Rate limiting     | "GetSetupPIN limited to N per interval" | `count(GetSetupPIN, interval) ≤ N` |
| Resource bounds   | "Scene table has capacity limit"        | `scenes_count() ≤ SceneTableSize`  |

#### 3.7 AUTHORIZATION Properties

Policy enforcement beyond authentication

| Pattern                    | Example                                           | Formalization                                                |
| -------------------------- | ------------------------------------------------- | ------------------------------------------------------------ |
| User type restrictions     | "YearDaySchedule only for ScheduleRestrictedUser" | `YearDaySchedule(user) ⟹ UserType(user)==ScheduleRestricted` |
| Operating mode enforcement | "Lock command rejected in PrivacyMode"            | `OperatingMode==Privacy ⟹ reject(LockFromRemote)`            |
| Time-based access          | "Access only within schedule window"              | `access() ⟹ within_schedule(current_time)`                   |

#### 3.8 TIMING Properties

Time-related security requirements

| Pattern                | Example                                 | Formalization                               |
| ---------------------- | --------------------------------------- | ------------------------------------------- |
| Auto-relock            | "Door relocks after AutoRelockTime"     | `unlocked(t) ⟹ locked(t + AutoRelockTime)`  |
| Timed command duration | "OnWithTimedOff respects OnTime"        | `on(t) ⟹ off(t + OnTime)`                   |
| Lockout duration       | "UserCodeTemporaryDisableTime enforced" | `lockout(t) ⟹ ¬accept_PIN(t + DisableTime)` |

#### 3.9 EVENT INTEGRITY Properties

Can events be suppressed or forged?

| Pattern          | Example                                  | Formalization                                       |
| ---------------- | ---------------------------------------- | --------------------------------------------------- |
| Event generation | "DoorLockOperationEvent on state change" | `∆LockState ⟹ gen_event(DoorLockOperationEvent)`    |
| Event delivery   | "Critical events SHALL be reported"      | `alarm_active ⟹ event_delivered(AlarmNotification)` |
| No suppression   | "Cannot mute CO alarm remotely"          | `COAlarm ⟹ ¬mutable_remotely`                       |

#### 3.10 CROSS-CLUSTER Properties

Security across multiple clusters on same endpoint

| Pattern                   | Example                                   | Formalization                                         |
| ------------------------- | ----------------------------------------- | ----------------------------------------------------- |
| Dependency enforcement    | "OffOnly implies Level Control disabled"  | `OnOff.OffOnly ⟹ ¬LevelControl.MoveToLevel_enabled`   |
| Dead Front behavior       | "DeadFront blocks other cluster commands" | `OnOff==Off ∧ DeadFront ⟹ reject(other_cluster_cmds)` |
| Operational state respect | "Cannot start if OperationalState==Error" | `OpState.Error ⟹ ¬start_operation()`                  |

### Step 4: Derive Implicit Properties

Combine explicit statements to find hidden constraints:

**A. Access Control Derivation**:

- Command X requires privilege A
- Command Y requires privilege O
- Derived: "Lower privilege (O) cannot achieve what higher privilege (A) can"

**B. State Safety Derivation**:

- State S is dangerous
- Transition T can reach S
- Derived: "Transition T must have safety guard"

**C. Timing Chain Derivation**:

- Timer A controls behavior B
- Behavior B affects safety
- Derived: "Timer A manipulation affects safety"

### Step 5: Identify Attack Vectors

For each property, document how it can be violated:

| Property Type     | Common Attack Vectors                    |
| ----------------- | ---------------------------------------- |
| Access Control    | Privilege escalation, ACL bypass         |
| State Integrity   | Invalid command sequence, race condition |
| Physical Safety   | Alarm suppression, sensor manipulation   |
| Authentication    | Brute force, replay, PIN extraction      |
| Secret Protection | Side channel, error oracle               |
| Availability      | Resource exhaustion, lockout             |
| Authorization     | Policy bypass, mode manipulation         |
| Timing            | Timer manipulation, schedule exploit     |
| Event Integrity   | Event suppression, fake events           |

---

## Output Schema (JSON) - Minimal Accurate Format

```json
{
  "cluster_properties": {
    "cluster_name": "string",
    "cluster_id": "hex",
    "pics_code": "string",
    "spec_reference": "Matter 1.5, Section X.Y, Pages P1-P2",

    "properties": [
      {
        "id": "PROP_001",
        "name": "Property_Name",
        "category": "AccessControl | StateIntegrity | PhysicalSafety | Authentication | SecretProtection | Availability | Authorization | Timing | EventIntegrity | CrossCluster",
        "importance": "CRITICAL | HIGH | MEDIUM",
        "claim": "Natural language: what must be true (1 sentence)",
        "formal": "∀x. P(x) → Q(x) OR state notation",
        "spec_source": "Section X.Y.Z, exact quote with SHALL/MUST",
        "violation": {
          "description": "What breaks if property fails (2-3 sentences)",
          "attack_vector": "How attacker achieves violation",
          "physical_impact": "Real-world consequence (or 'None' for non-safety)"
        },
        "proverifQuery": "event(x) ==> precondition(x)"
      }
    ],

    "assumptions": [
      {
        "id": "ASSUM_001",
        "statement": "Assumption text",
        "type": "Explicit | Implicit",
        "source": "Section X.Y or 'Derived'",
        "dependencies": ["PROP_001", "PROP_005"],
        "impact_if_violated": "Which properties fail"
      }
    ],

    "spec_gaps": [
      {
        "id": "GAP_001",
        "location": "Section X.Y.Z",
        "normative_weakness": "MAY | SHOULD | Unspecified",
        "description": "What is missing or ambiguous",
        "properties_affected": ["PROP_001"],
        "security_impact": "How gap enables attack"
      }
    ],

    "cross_cluster_properties": [
      {
        "id": "XPROP_001",
        "clusters_involved": ["Cluster_A", "Cluster_B"],
        "property": {
          "claim": "Cross-cluster property description",
          "formal": "Cluster_A.attr ∧ Cluster_B.attr ⟹ Q"
        },
        "violation_scenario": "How interaction creates vulnerability"
      }
    ],

    "safety_critical_properties": [
      {
        "property_id": "PROP_005",
        "safety_category": "FireSafety | PhysicalSecurity | FloodPrevention | ChildSafety | etc",
        "failure_mode": "What happens if property violated in physical world",
        "spec_mitigation": "How spec addresses (or 'UNSPECIFIED')"
      }
    ],

    "summary": {
      "total_properties": 25,
      "by_importance": { "CRITICAL": 5, "HIGH": 10, "MEDIUM": 10 },
      "by_category": {
        "AccessControl": 6,
        "StateIntegrity": 4,
        "PhysicalSafety": 3,
        "Authentication": 4,
        "Timing": 3,
        "Availability": 2,
        "EventIntegrity": 2,
        "Authorization": 1
      },
      "spec_gaps_found": 5,
      "safety_critical_count": 4
    }
  }
}
```

---

## Formalization Rules for ProVerif

Keep formal statements **short and verifiable**:

```proverif
(* Access Control: Only Admin can clear credentials *)
query x:principal, cred:credential ⊢
  event clear_credential(x, cred) ==> has_privilege(x, Admin)

(* State Integrity: Lock state transitions require authentication *)
query lock:device, from:state, to:state ⊢
  event state_change(lock, Locked, Unlocked) ==> event auth_success(lock)

(* Physical Safety: Valve closes on detected fault *)
query v:device, t:time ⊢
  event valve_fault(v, t) ==> event valve_closed(v, t')  // t' shortly after t

(* Timing: Auto-relock enforced within timeout *)
query d:device, t:time ⊢
  event door_unlocked(d, t) ==> event door_locked(d, t + AutoRelockTime)

(* Authentication: PIN required for remote operation when enabled *)
query d:device, cmd:command ⊢
  event remote_command(d, cmd) ∧ RequirePINForRemote(d) ==> event pin_validated(d)
```

---

## Application Cluster-Specific Patterns

### Door Lock Specific (DRLK)

- PIN brute force protection properties
- Credential management authorization
- Operating mode enforcement
- Auto-relock timing
- Remote operation authentication

### Smoke/CO Alarm Specific (SMOKECO)

- Alarm cannot be remotely suppressed during emergency
- Sensitivity changes generate audit events
- Interconnect alarms are authenticated
- Self-test manipulation detection

### Valve Control Specific (VALCC)

- Fail-safe on fault (close)
- No indefinite open duration
- Operate privilege required (not just View)

### EVSE Specific (EVSE)

- Charging enable requires proper authorization
- Grid safety properties (overcurrent prevention)
- V2X bidirectional flow controls

### Camera/AV Specific (CAMERA)

- Privacy mode enforced (no stream when disabled)
- WebRTC session authentication
- SFrame E2E encryption mandated
- No TURN server redirection

---

## Execution Checklist

- [ ] All "SHALL", "MUST" requirements extracted
- [ ] All "SHOULD" requirements filtered through security/safety criteria
- [ ] Access control for all commands documented (V/O/M/A)
- [ ] State machine transitions have security properties
- [ ] Physical safety properties identified for actuation clusters
- [ ] Authentication requirements extracted (PIN, credential, etc.)
- [ ] Timing properties formalized (timers, schedules, rates)
- [ ] Event generation requirements documented
- [ ] Cross-cluster dependencies analyzed
- [ ] Spec gaps identified with security impact
- [ ] Implicit assumptions documented
- [ ] ProVerif queries sketched for CRITICAL properties
- [ ] Attack vectors described for each property
- [ ] Safety-critical properties highlighted
- [ ] Summary statistics included

---

## Example Property (Complete)

```json
{
  "id": "PROP_DRLK_007",
  "name": "Remote_Unlock_PIN_Required",
  "category": "Authentication",
  "importance": "CRITICAL",
  "claim": "When RequirePINForRemoteOperation is TRUE and PINCredential feature is supported, remote Unlock commands SHALL include a valid PIN.",
  "formal": "∀remote_cmd. (RequirePINForRemoteOperation == true ∧ Feature_PIN == true) ∧ unlock(remote_cmd) ⟹ PIN_valid(remote_cmd.PIN)",
  "spec_source": "Section 5.2.10.1.1: 'If RequirePINforRemoteOperation attribute is True and the PINCredential feature is supported, a valid PINCode field SHALL be provided'",
  "violation": {
    "description": "Remote unlock command executes without valid PIN when PIN should be required. Attacker with network access and Operate privilege can unlock door without knowing any PIN.",
    "attack_vector": "Send UnlockDoor command with omitted or garbage PINCode field if implementation doesn't enforce validation",
    "physical_impact": "Unauthorized physical entry to secured space"
  },
  "proverifQuery": "query d:device, cmd:command ⊢ event unlock_success(d, cmd, Remote) ∧ RequirePINForRemote(d) ==> event pin_validated(d, cmd.PIN)"
}
```

---

## Property Extraction Priority Order

1. **CRITICAL First**: Physical safety, authentication bypass, privilege escalation
2. **HIGH Second**: State integrity, availability, timing
3. **MEDIUM Last**: Event integrity, cross-cluster, operational

For each cluster, aim to extract:

- At least 3-5 CRITICAL properties (safety/auth)
- At least 5-10 HIGH properties (state/access)
- All identifiable MEDIUM properties

---

## Key Differences from Core Protocol Properties

| Aspect                    | Core Protocol                | Application Cluster                      |
| ------------------------- | ---------------------------- | ---------------------------------------- |
| **Primary Property Type** | Secrecy, Authentication      | Access Control, Safety                   |
| **Adversary Model**       | Network attacker             | Malicious controller/device              |
| **Impact Measurement**    | Data confidentiality         | Physical world effect                    |
| **Timing Precision**      | Milliseconds (crypto timing) | Seconds/minutes (auto-relock, schedules) |
| **Failure Mode**          | Session compromise           | Fire, flood, unauthorized entry          |

---

## Notes

- **Physical Safety is Paramount**: Application clusters control the real world
- **Access Control Levels Matter**: V < O < M < A privilege hierarchy
- **MAY vs SHALL**: Weak normative language creates implementation variation
- **Feature Flags Complicate Properties**: Properties may only apply when features enabled
- **Spec Gaps are Attack Surface**: Document what spec doesn't specify
