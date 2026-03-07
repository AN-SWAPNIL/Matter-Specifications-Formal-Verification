# Violation Summary - Commissioner Control Cluster

## Quick Reference

**Analysis Date**: 2026-01-30  
**Properties Analyzed**: 30/30 (100%)  
**Violations Found**: 2

---

## 🔴 VIOLATION #1: PROP_003 - Always Return SUCCESS

### Issue
Spec: "Server SHALL **always** return SUCCESS to correctly formatted request"  
FSM: Returns FAILURE for duplicate RequestID and unsupported device category

### Attack Vector
```
1. Client sends correctly formatted request (valid schema)
2. Server detects duplicate RequestID
3. Server returns FAILURE (violates "always SUCCESS")
4. Client waits for CommissioningRequestResult event that never arrives
5. Protocol deadlock
```

### Evidence
**Spec Quote**:
> "The server SHALL always return SUCCESS to a correctly formatted RequestCommissioningApproval command, and then generate a CommissioningRequestResult event"
> 
> Source: Section 11.26.6.1, Page 4

**FSM Transition** (violates spec):
```json
{
  "from_state": "Idle",
  "to_state": "Duplicate_RequestID_Detected",
  "guard_condition": "check_duplicate_request(request) == true",
  "actions": ["generate_failure_response(FAILURE)"]
}
```

### Impact
- **Severity**: MEDIUM
- **Security**: LOW (no direct exploit)
- **Functional**: MEDIUM (protocol confusion, client hangs)

### Fix
Return SUCCESS for all format-valid requests, defer duplicate/category checks to event phase.

---

## 🔴 VIOLATION #2: PROP_023 - Approval Expiration

### Issue
Spec: Approvals should be temporally bounded (implicit requirement)  
FSM: Approvals remain valid **indefinitely** (no expiration timer)

### Attack Vector
```
1. T0: Victim receives approval (RequestID = R)
2. T0 + [WEEKS]: Approval still valid (no expiration)
3. Attacker uses stolen RequestID R to commission device weeks later
4. Server accepts stale approval (no time check)
5. Time-shifted commissioning attack succeeds
```

### Evidence
**FSM State** (no timer):
```json
{
  "name": "Approval_Granted",
  "invariants": ["approval_valid == true"],
  "state_variables": {"approval_timestamp": "timestamp"}
}
```

**Missing Transitions**:
- NO: `Approval_Granted -> Approval_Expired` on timer
- NO: `start_approval_timer()` function call
- NO: Time-based guard in CommissionNode acceptance

### Impact
- **Severity**: MEDIUM-HIGH
- **Security**: MEDIUM-HIGH (time-shifted attacks, stale consent)
- **Functional**: HIGH (policy violation, unexpected commissioning)

### Fix
Add approval timer with max validity period (recommend 300 seconds), generate TIMEOUT event on expiration.

---

## ✅ Properties Holding: 26/30

All other properties correctly enforced:
- ✅ CASE session authentication (PROP_001, PROP_010)
- ✅ Identity binding NodeID/Fabric (PROP_008)
- ✅ VendorID/ProductID verification (PROP_015, PROP_016)
- ✅ Request/Event correlation (PROP_004, PROP_006, PROP_018)
- ✅ PAKE parameter security (PROP_025, PROP_026)
- ✅ Timeout enforcement (PROP_013)
- ✅ Single-use approval (PROP_012)
- ✅ Response sequencing (PROP_027)
- ✅ State exclusivity (PROP_029)

---

## ⚠️ Caveats: 2

1. **PROP_002**: Client obligation (server enforces defensively) ✅
2. **PROP_007**: Deferred verification (checked at commissioning) ✅

---

## Recommended Actions

### High Priority
1. **Fix PROP_003**: Clarify spec definition of "correctly formatted" OR change FSM to return SUCCESS always
2. **Fix PROP_023**: Add approval expiration timer (300s max recommended)

### Medium Priority
3. Document deferred verification pattern (PROP_007)
4. Add explicit out-of-order message handling in FSM

### Low Priority
5. Clarify client vs server obligation boundaries (PROP_002)

---

## Detailed Analysis
See [VIOLATION_REPORT.md](VIOLATION_REPORT.md) for:
- Complete FSM path traces
- Exact specification citations
- Attack scenarios with step-by-step execution
- Counterexample scenarios
- Impact analysis per property

---

**Status**: Analysis Complete ✅  
**Confidence**: HIGH (all properties verified with FSM evidence)
