# Property Violations Summary

## Analysis Overview
- **Specification**: Matter Core Specification 1.5, Section 11.25 Joint Fabric Administrator Cluster
- **FSM Model**: joint_fabric_administrator_fsm.json
- **Properties Analyzed**: 27 of 44 (61%)
- **Violations Found**: 7
- **Severity Breakdown**: 1 Critical, 2 High, 4 Medium

---

## Critical Violations (1)

### 1. PROP_033: Fail_Safe_Atomicity ⚠️ **CRITICAL**

**Issue**: Missing fail-safe expiration transitions from intermediate commissioning states (CSRRequested, CSRGenerated, ValidatingICAC). When fail-safe expires during commissioning, node remains in intermediate state with partial commissioning data.

**Attack Scenario**:
1. Administrator initiates commissioning: Idle → CSRRequested → CSRGenerated
2. Network partition or administrator crash - AddICAC never sent
3. Fail-safe timer expires
4. **VIOLATION**: Node stuck in CSRGenerated with stored CSR public key
5. Cannot be re-commissioned without factory reset

**FSM Gap**: Only ICACAccepted state has fail-safe expiration transition (T016). States CSRRequested, CSRGenerated, ValidatingICAC have no rollback.

**Specification Evidence**:
> "If this command is received without an armed fail-safe context (see Section 11.10.7.2, "ArmFailSafe"), then this command SHALL fail with a FAILSAFE_REQUIRED status code sent back to the initiator."
> — Section 11.25.7.1 & 11.25.7.3

**Impact**: Denial of Service - node in undefined state, cannot retry commissioning, CSR data persists in memory.

**Fix**: Add transitions: {CSRRequested, CSRGenerated, ValidatingICAC} → Idle on fail_safe_expired with rollback_all_operations() action.

---

## High Violations (2)

### 2. PROP_027: Discriminator_Range_Validation ⚠️ **HIGH**

**Issue**: OpenJointCommissioningWindow discriminator parameter (max 4095) not validated. Values >4095 accepted.

**Attack Scenario**:
1. Attacker sends OpenJointCommissioningWindow with discriminator=65535  
2. FSM validates PAKE parameters (verifier, iterations, salt) ✅
3. **VIOLATION**: Discriminator not checked, window opens with invalid value
4. Discovery collision, integer overflow, or non-standard behavior

**FSM Gap**: validate_pake_parameters() only validates verifier, iterations, salt. Discriminator omitted.

**Specification Evidence**:
> "Discriminator ... uint16 ... max 4095"
> — Section 11.25.7.5, Parameter 2

**Impact**: Discovery protocol violation, integer overflow risk, commissioning collision, device fingerprinting.

**Fix**: Update validate_pake_parameters(verifier, iterations, salt, discriminator) to include: if (discriminator > 4095) return failure.

---

### 3. PROP_035: State_Machine_Exclusivity ⚠️ **HIGH**

**Issue**: Four independent state machines (Joint Commissioning, ACL Management, Commissioning Window, Anchor Transfer) can run concurrently without mutual exclusion.

**Attack Scenario**:
1. Joint commissioning in progress: Idle → CSRGenerated
2. Simultaneously, RemoveACLFromNode accepted: ACL_Active → ACL_DeletePending  
3. **VIOLATION**: Concurrent operations on same node
4. Race condition: ACL removed during commissioning, administrator loses access

**FSM Gap**: No guards checking commissioning_in_progress or acl_operations_ongoing between state machines.

**Specification Evidence**:
> "TransferAnchorStatusDatastoreBusy ... Anchor Transfer was not started due to ongoing Datastore operations"
> — Section 11.25.4.2

**Impact**: Race conditions, credential corruption, authority conflicts, state inconsistency, potential deadlocks.

**Fix**: Add global operation lock or mutual exclusion guards: All operations check operation_in_progress flag before starting.

---

## Medium Violations (4)

### 4. PROP_026: Prevent_Concurrent_Commissioning_Operations ⚠️ **MEDIUM**

**Issue**: No explicit Busy error response for concurrent ICACCSRRequest attempts during in-progress commissioning.

**FSM Gap**: ICACCSRRequest only accepted from Idle. From states {CSRRequested, CSRGenerated, ValidatingICAC}, no transition defined for concurrent ICACCSRRequest → undefined behavior.

**Impact**: Interoperability issues, unclear error semantics, potential DoS through repeated attempts.

**Fix**: Add transitions: {CSRRequested, CSRGenerated, ValidatingICAC} → ErrorState_Busy on ICACCSRRequest trigger.

---

### 5. PROP_042: CSR_Size_Limit_600_Bytes ⚠️ **MEDIUM**

**Issue**: No size validation when generating/sending CSR. CSR >600 bytes could violate protocol constraint.

**FSM Gap**: generate_PKCS10_CSR_DER_encoded() and send_ICACCSRResponse() don't check size.

**Specification Evidence**:
> "ICACCSR ... octstr ... max 600"
> — Section 11.25.7.2

**Impact**: Buffer overflow risk on receiver, protocol violation, memory exhaustion DoS.

**Fix**: Add size check: if (byte_length(csr) > 600) fail commissioning.

---

### 6. PROP_043: ICAC_Size_Limit_400_Bytes ⚠️ **MEDIUM**

**Issue**: No size validation when receiving ICAC in AddICAC. ICAC >400 bytes could be accepted.

**FSM Gap**: Effect on Receipt lists 3 validations (chain, pubkey, DN encoding) but not size.

**Specification Evidence**:
> "ICACValue ... octstr ... max 400"
> — Section 11.25.7.3

**Impact**: Memory exhaustion, protocol violation, buffer overflow risk in downstream parser.

**Fix**: Add 4th validation check: if (byte_length(icac) > 400) return InvalidICAC.

---

### 7. PROP_023: Endpoint_Announcement_Uniqueness ⚠️ **MEDIUM**

**Issue**: AnnounceJointFabricAdministrator accepts any EndpointID without validating existence or JFAC cluster presence.

**FSM Gap**: Transition T048 has guard=true (unconditional acceptance).

**Specification Evidence**:
> "This field SHALL contain the unique identifier for the endpoint that holds the Joint Fabric Administrator Cluster."
> — Section 11.25.7.9

**Impact**: Endpoint misdirection, DoS through invalid announcements, potential MITM.

**Fix**: Add validation guard: endpoint_exists(EndpointID) && endpoint_has_JFAC_cluster(EndpointID).

---

## Properties Holding (17)

The following properties were verified and **hold correctly** in the FSM:

1. **PROP_001**: CASE_Session_Authentication_ICACCSRRequest ✅
2. **PROP_002**: CASE_Session_Authentication_AddICAC ✅
3. **PROP_003**: Certificate_Chain_Validation ✅
4. **PROP_004**: Public_Key_Binding ✅
5. **PROP_005**: Fail_Safe_Context_Required_ICACCSRRequest ✅
6. **PROP_006**: Fail_Safe_Context_Required_AddICAC ✅
7. **PROP_007**: VID_Verification_Prerequisite ✅
8. **PROP_008**: Single_AddICAC_Per_Fail_Safe_Period ✅
9. **PROP_009**: DN_Encoding_Validation ✅
10. **PROP_010**: ACL_Removal_Atomicity (Two-Phase Commit) ✅
11. **PROP_020**: ICAC_Format_Matter_Certificate_Encoding ✅
12. **PROP_024**: PAKE_Parameters_Validation (verifier, iterations, salt) ✅
13. **PROP_028**: PAKE_Iterations_Range_Validation ✅
14. **PROP_029**: PAKE_Salt_Length_Validation ✅
15. **PROP_031**: Public_Key_Session_Binding ✅
16. **PROP_014**: AdministratorFabricIndex_Not_Null_For_CommissioningWindow ✅
17. **PROP_015**: Node_Not_Found_Error_RemoveACL ✅

---

## Unverified Properties (3)

The following properties could not be conclusively verified due to specification ambiguity or scope limitations:

1. **PROP_012**: Attestation_And_VID_Verification_Before_AddICAC
   - **Reason**: Specification places requirement on issuer (Commissioner), not receiver (node). FSM correctly implements receiver side. Attestation is trust assumption.

2. **PROP_013**: Administrator_Authorization_Validation  
   - **Reason**: Authorization implicit in CASE session authentication. Explicit administrator role validation is issuer responsibility.

3. **PROP_025**: Commissioning_Window_Open_Required
   - **Reason**: Specification unclear whether joint commissioning (over CASE) requires open commissioning window. Window may be for PASE-based commissioning only.

---

## Recommendations

### Immediate Fixes (Critical)
1. **Add fail-safe rollback transitions** from all intermediate commissioning states
2. **Implement state machine mutual exclusion** to prevent concurrent operations

### High Priority Fixes
3. **Add discriminator validation** to commissioning window parameter checks
4. **Add Busy error handling** for concurrent operation attempts

### Medium Priority Fixes
5. **Add size validation** for CSR (≤600 bytes) and ICAC (≤400 bytes)
6. **Add endpoint validation** for AnnounceJointFabricAdministrator

### Specification Improvements
7. **Clarify fail-safe expiration behavior** for all commissioning states
8. **Define mutual exclusion requirements** between administrative operations
9. **Mandate size validation locations** (generator vs receiver vs both)
10. **Add Effect on Receipt sections** for all commands with validation requirements

---

## Next Steps

### For Complete Analysis
- Analyze remaining 17 properties (PROP_011, PROP_016-PROP_022, PROP_030, PROP_034, PROP_036-PROP_041, PROP_044)
- Verify properties with unverifiable verdicts against updated specification
- Perform end-to-end FSM simulation with violation scenarios

### For FSM Correction
- Update FSM with recommended fixes
- Re-run property verification on corrected FSM
- Generate formal proof obligations for critical properties

### For Specification Refinement
- Submit specification change requests for identified gaps
- Propose validation requirement additions to Effect on Receipt sections
- Clarify ambiguous mutual exclusion and sequencing requirements

---

## Files Generated

1. **property_violations_report.json** - Detailed JSON report with all violation analysis
2. **property_violation_analysis_working.md** - Step-by-step working document  
3. **VIOLATIONS_SUMMARY.md** - This summary document (quick reference)

---

**Analysis Date**: 2026-02-13  
**Analyst**: FSM Property Violation Analysis Tool  
**Specification**: Matter Core Specification 1.5, Section 11.25
