# Network Recovery Protocol - Violations & Vulnerabilities

**Analysis Date**: February 13, 2026  
**Specification**: Matter Core Specification 1.5, Section 5.9 Network Recovery  
**FSM Model**: network_recovery_fsm.json  
**Properties Analyzed**: 42

---

## Executive Summary

**Total Violations Found**: 2  
**Severity Distribution**:
- 🔴 **CRITICAL**: 1 violation
- 🟡 **MEDIUM**: 1 violation

**Overall Assessment**: The FSM is generally well-designed and enforces most security properties correctly. However, two significant violations were identified where the FSM fails to fully implement specification requirements, including one critical denial-of-service vulnerability.

---

## 🔴 VIOLATION 1: Fail-Safe Timeout Gap (CRITICAL)

### Property Details
- **Property ID**: PROP_040
- **Property Name**: FailSafe_Timeout_Protects_Against_Incomplete_Recovery
- **Severity**: CRITICAL
- **Confidence**: 100%

### Vulnerability Description

The FSM does not implement fail-safe timeout protection after the Administrator successfully arms the fail-safe. If an Administrator arms the fail-safe but then abandons the recovery process without provisioning credentials, the Recovery Node becomes permanently locked in the `AdminFailSafeArmed` state with no automatic rollback mechanism.

### FSM Attack Path

```
1. NodeFailSafeArmed
   ↓ [admin_arm_failsafe_command received within 60s]
   
2. AdminFailSafeArmed
   ↓ [Administrator abandons recovery - no timeout transition exists]
   
3. AdminFailSafeArmed (STUCK INDEFINITELY)
   - No automatic timeout
   - No rollback mechanism
   - No way to accept new recovery attempts
   - Requires manual intervention (power cycle/reset)
```

### Missing FSM Transition

**Expected**: `AdminFailSafeArmed → FailSafeExpired` (when admin fail-safe timer expires)  
**Actual**: No such transition exists in FSM

The FSM only models fail-safe timeout from `NodeFailSafeArmed` state (before Administrator arms fail-safe), but not from `AdminFailSafeArmed` state (after Administrator arms fail-safe).

### Specification Evidence

> **Section 5.9.3, Step 10**: "Upon successful establishment of the CASE session, the Recovery Node SHALL autonomously arm the fail-safe timer for a timeout of 60 seconds. **This is to guard against the Administrator not proceeding with the rest of the flow in a timely fashion**, and is analogous to step 6 of the standard commissioning flow."

The specification explicitly states the fail-safe should "guard against the Administrator not proceeding with the rest of the flow" — this includes all steps after CASE session establishment, not just the Administrator arming the fail-safe.

### Attack Scenario

**Attacker Goal**: Cause persistent Denial of Service against target Recovery Node

**Attack Steps**:
1. Attacker triggers network credential change to disconnect victim node
2. Victim node enters recovery mode and announces via BLE/mDNS
3. Attacker (acting as Administrator with RecoveryIdentifier) receives announcement
4. Attacker establishes connection and CASE session with victim node
5. Node autonomously arms fail-safe (60s timeout)
6. Attacker sends `ArmFailSafe` command within 60s window ✅
7. Node transitions: `NodeFailSafeArmed → AdminFailSafeArmed`
8. **Attacker disconnects and abandons recovery**
9. **Node is stuck in `AdminFailSafeArmed` state indefinitely**
10. Node cannot timeout (no FSM transition)
11. Node cannot accept new recovery attempts (still in failed recovery state)
12. Legitimate Administrator cannot help — node is locked

**Result**: Persistent Denial of Service requiring manual intervention

### Security Impact

- **Availability**: Node becomes completely unreachable and cannot perform any functions
- **Recovery**: Requires manual intervention (power cycle or factory reset)
- **Persistence**: Attack effect is permanent until manual intervention
- **Scalability**: Attacker can execute against multiple nodes simultaneously
- **Mitigation**: No automatic recovery mechanism exists

### Recommendations

1. **Add Timeout Transition**: 
   ```
   AdminFailSafeArmed → FailSafeExpired
   Trigger: admin_failsafe_timer_expired
   Guard: admin_failsafe_timer == 0
   Actions: rollback_state(), resume_autonomous_reconnect()
   ```

2. **Add Timer Decrement**: Include stay transition in `AdminFailSafeArmed` to decrement `admin_failsafe_timer`

3. **Specification Clarification**: Update specification to explicitly state fail-safe timer continues through ALL recovery steps until `CommissioningComplete`, not just until Administrator arms fail-safe

4. **Alternative Design**: Consider single continuous fail-safe timer from CASE session establishment through recovery completion, rather than two-phase approach

---

## 🟡 VIOLATION 2: Incomplete Reconnection Coverage (MEDIUM)

### Property Details
- **Property ID**: PROP_021
- **Property Name**: Continuous_Reconnection_During_Recovery_State
- **Severity**: MEDIUM
- **Confidence**: 100%

### Vulnerability Description

The FSM does not model continuous autonomous reconnection attempts throughout all recovery states. While the specification requires Recovery Nodes to "SHALL attempt to reconnect to the existing operational network while in the recovery state," the FSM only implements reconnection attempts in `RecoveryAnnouncing` and `ExtendedAnnouncementEnded` states. Reconnection attempts stop when the node transitions to `AwaitingAdministrator` or `RecoveryConnectionEstablished` states.

### FSM Gap Analysis

**States WITH Reconnection Attempts** (✅):
- `RecoveryAnnouncing` - has stay transition with `attempt_reconnect`
- `ExtendedAnnouncementEnded` - has stay transition with `attempt_reconnect`

**States WITHOUT Reconnection Attempts** (❌):
- `AwaitingAdministrator` - no stay transition for reconnection
- `RecoveryConnectionEstablished` - no stay transition for reconnection

### FSM Attack Path

```
1. RecoveryAnnouncing
   - Autonomous reconnection attempts active ✅
   ↓ [administrator_received_announcement]
   
2. AwaitingAdministrator
   - Autonomous reconnection attempts STOPPED ❌
   - Network becomes available here → Node won't detect it
   ↓ [administrator_establish_connection with user_consent]
   
3. RecoveryConnectionEstablished
   - Autonomous reconnection attempts STILL STOPPED ❌
   - Old credentials could work now → Node won't try them
   ↓ [establish_case]
   
4. CASESessionEstablished
   - Reconnection explicitly suspended (correct per spec)
```

### Specification Evidence

> **Section 5.9.3, Step 3**: "Recovery Nodes **SHALL attempt to reconnect** to the existing operational network **while in the recovery state**."

The "recovery state" encompasses ALL states from entering recovery mode until either:
- Autonomous reconnection succeeds
- Recovery completes via Administrator assistance
- Recovery is aborted

> **Section 5.9.3, Step 9**: "once the secure connection is established, any **ongoing attempts** taken autonomously by the Recovery Node to re-establish connectivity to the previously configured operational network SHALL be suspended"

The use of "ongoing attempts" confirms reconnection should be ACTIVE until CASE session established, not just during announcement phase.

### Impact Scenario

**Scenario**: Network temporarily unavailable, then restored during recovery

**Timeline**:
1. **T=0s**: Credentials changed, network connectivity lost
2. **T=120s**: Recovery announcement begins with concurrent reconnection attempts
3. **T=130s**: Administrator receives announcement, begins preparing to connect
4. **T=135s**: Node transitions to `AwaitingAdministrator` (stops reconnection)
5. **T=140s**: Network credentials restored / old network becomes available again
6. **T=140s-180s**: Node in `AwaitingAdministrator` — could reconnect autonomously but doesn't try
7. **T=180s**: Administrator establishes recovery connection unnecessarily
8. **T=180s-300s**: Full Administrator-assisted recovery proceeds
9. **Result**: Wasted 180 seconds and unnecessary Administrator intervention when autonomous recovery would have succeeded at T=140s

### Security Impact

- **Efficiency**: Unnecessary Administrator intervention when autonomous recovery would succeed
- **Recovery Time**: Extended downtime during window when network is available
- **Resource Usage**: Wastes Administrator time and attention
- **Information Disclosure**: Unnecessarily exposes RecoveryIdentifier via BLE/mDNS
- **Fault Tolerance**: Reduces protocol's ability to recover from transient network issues

### Recommendations

1. **Add Reconnection in AwaitingAdministrator**:
   ```
   AwaitingAdministrator → AwaitingAdministrator (stay transition)
   Trigger: reconnect_attempt_tick
   Guard: true
   Actions: attempt_reconnect(old_credentials)
   ```

2. **Add Reconnection in RecoveryConnectionEstablished**:
   ```
   RecoveryConnectionEstablished → RecoveryConnectionEstablished (stay transition)
   Trigger: reconnect_attempt_tick
   Guard: true
   Actions: attempt_reconnect(old_credentials)
   ```

3. **Suspend Only at CASE Session**: Ensure `suspend_autonomous_reconnect()` is only called when transitioning to `CASESessionEstablished`, not earlier

4. **Add Success Transition**: If reconnection succeeds in any recovery state before CASE session, transition directly to abort recovery and return to normal operation

---

## Summary Statistics

### Properties Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ HOLDS | 28 | 67% |
| ❌ VIOLATED | 2 | 5% |
| 🔶 PARTIALLY HOLDS | 2 | 5% |
| ❓ UNVERIFIABLE | 10 | 24% |
| **Total** | **42** | **100%** |

### Violations by Severity

| Severity | Count | Properties |
|----------|-------|------------|
| 🔴 CRITICAL | 1 | PROP_040 |
| 🔵 HIGH | 0 | - |
| 🟡 MEDIUM | 1 | PROP_021 |

### Key Security Properties Status

All critical security properties hold correctly:
- ✅ CASE session required for recovery (PROP_001)
- ✅ User consent before credential provision (PROP_003, PROP_004)
- ✅ CommissioningComplete over operational network only (PROP_005)
- ✅ Fail-safe armed on CASE session (PROP_011)
- ✅ Recovery preempts autonomous reconnection (PROP_009)
- ✅ Administrator provides new credentials (PROP_014)
- ✅ Operational discovery before CommissioningComplete (PROP_019)

---

## Overall Assessment

The Matter Network Recovery protocol FSM demonstrates strong security design in core areas:
- Proper CASE session establishment and encryption
- Correct user consent enforcement
- Appropriate operational network validation
- Correct state transition ordering

However, two significant violations require attention:

1. **Critical fail-safe timeout gap** enables permanent DoS attack
2. **Incomplete reconnection coverage** reduces fault tolerance and efficiency

Both violations stem from incomplete implementation of specification requirements rather than fundamental security flaws. The recommended fixes are straightforward additions to existing FSM structure.

---

## References

- **Specification**: Matter Core Specification 1.5, Section 5.9 Network Recovery
- **FSM Model**: [network_recovery_fsm.json](network_recovery_fsm.json)
- **Properties**: [network_recovery_properties.json](network_recovery_properties.json)
- **Detailed Analysis**: [property_violation_analysis.json](property_violation_analysis.json)
