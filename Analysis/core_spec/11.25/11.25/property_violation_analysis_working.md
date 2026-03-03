# Property Violation Analysis - Working Document

## Analysis Status
- **Started**: 2026-02-13
- **Specification**: Matter Core Specification 1.5, Section 11.25 Joint Fabric Administrator Cluster
- **FSM Model**: joint_fabric_administrator_fsm.json
- **Total Properties**: 44 (24 CRITICAL, 15 HIGH, 5 MEDIUM)

---

## Methodology
For each property:
1. **Formalize** - Convert property claim to FSM query
2. **Trace FSM** - Find all transitions that could violate property
3. **Verdict** - HOLDS | VIOLATED | PARTIALLY_HOLDS | UNVERIFIABLE
4. **Cite Spec** - Extract exact specification text
5. **Document** - Record violation path or supporting evidence

---

## Analysis Progress

### CRITICAL Properties (Priority 1)

#### PROP_001: CASE_Session_Authentication_ICACCSRRequest
- **Status**: Analyzing...
- **Claim**: ICACCSRRequest command must be received over an authenticated CASE session
- **Formal**: ∀session, cmd. event receive_ICACCSRRequest(session, cmd) ==> is_CASE_session(session)

**FSM Trace**:
Looking at transitions from Idle state:
- T001: Idle -> CSRRequested
  - Trigger: ICACCSRRequest
  - Guard: `session_is_CASE == true && fail_safe_armed == true && vid_verification_completed == true && prior_AddICAC_executed == false`
  - ✅ Guard includes `session_is_CASE == true`

- T002: Idle -> ErrorState_InvalidSession
  - Trigger: ICACCSRRequest
  - Guard: `session_is_CASE == false`
  - ✅ Rejects non-CASE sessions with error

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "This command SHALL be received over a CASE session otherwise it SHALL fail with an INVALID_COMMAND status code."
Source: Section 11.25.7.1, "ICACCSRRequest Command", "Effect on Receipt", Paragraph 1
Context: First requirement listed for ICACCSRRequest command
```

**Supporting Transitions**:
- T001: Accepts ICACCSRRequest only when `session_is_CASE == true`
- T002: Explicitly rejects when `session_is_CASE == false`

---

#### PROP_002: CASE_Session_Authentication_AddICAC
- **Status**: Analyzing...
- **Claim**: AddICAC command must be received over an authenticated CASE session
- **Formal**: ∀session, cmd. event receive_AddICAC(session, cmd) ==> is_CASE_session(session)

**FSM Trace**:
From CSRGenerated state (where AddICAC is expected):
- T007: CSRGenerated -> ValidatingICAC
  - Trigger: AddICAC
  - Guard: `session_is_CASE == true && fail_safe_armed == true && prior_AddICAC_executed == false`
  - ✅ Guard includes `session_is_CASE == true`

- T008: CSRGenerated -> ErrorState_InvalidSession
  - Trigger: AddICAC
  - Guard: `session_is_CASE == false`
  - ✅ Rejects non-CASE sessions with error

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "This command SHALL be received over a CASE session otherwise it SHALL fail with an INVALID_COMMAND status code."
Source: Section 11.25.7.3, "AddICAC Command", "Effect on Receipt", Paragraph 1
Context: First requirement listed for AddICAC command
```

---

#### PROP_003: Certificate_Chain_Validation
- **Status**: Analyzing...
- **Claim**: ICAC must be validated using Crypto_VerifyChain against the Root CA certificate of the accessing fabric
- **Formal**: ∀icac, rcac. event accept_ICAC(icac) ==> event verify_chain_success(icac, rcac) ∧ is_root_CA(rcac)

**FSM Trace**:
From ValidatingICAC state:
- T011: ValidatingICAC -> ICACAccepted
  - Guard: `Crypto_VerifyChain(icac, rcac) == success && validate_public_key_match(icac_pubkey, csr_pubkey) == success && validate_DN_encoding(icac) == success`
  - ✅ Requires Crypto_VerifyChain success

- T012: ValidatingICAC -> ICACRejected_InvalidICAC
  - Guard: `Crypto_VerifyChain(icac, rcac) == failure`
  - ✅ Rejects when chain validation fails

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "Verify the ICAC using `Crypto_VerifyChain(certificates = [ICACValue, RootCACertificate])` where RootCACertificate is the associated RCAC of the accessing fabric. If this check fails, the error status SHALL be InvalidICAC."
Source: Section 11.25.7.3, "AddICAC Command", "Effect on Receipt", Validation check #1
Context: First of three validation checks before accepting ICAC
```

---

#### PROP_004: Public_Key_Binding
- **Status**: Analyzing...
- **Claim**: The public key in the ICAC must match the public key in the last ICACCSRResponse
- **Formal**: ∀icac, csr, pk. event AddICAC(icac) ∧ event ICACCSRResponse(csr) ==> extract_pubkey(icac) = extract_pubkey(csr)

**FSM Trace**:
From ValidatingICAC state:
- T011: ValidatingICAC -> ICACAccepted
  - Guard: `Crypto_VerifyChain(icac, rcac) == success && validate_public_key_match(icac_pubkey, csr_pubkey) == success && validate_DN_encoding(icac) == success`
  - ✅ Requires validate_public_key_match success

- T013: ValidatingICAC -> ICACRejected_InvalidPublicKey
  - Guard: `Crypto_VerifyChain(icac, rcac) == success && validate_public_key_match(icac_pubkey, csr_pubkey) == failure`
  - ✅ Rejects when public key doesn't match

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "The public key of the ICAC SHALL match the public key present in the last ICACCSRResponse provided to the Administrator that sent the AddICAC command. If this check fails, the error status SHALL be InvalidPublicKey."
Source: Section 11.25.7.3, "AddICAC Command", "Effect on Receipt", Validation check #2
Context: Second of three validation checks before accepting ICAC
```

---

#### PROP_005: Fail_Safe_Context_Required_ICACCSRRequest
- **Status**: Analyzing...
- **Claim**: ICACCSRRequest must be received with an armed fail-safe context
- **Formal**: ∀cmd. event receive_ICACCSRRequest(cmd) ==> event fail_safe_armed() ∧ ¬event fail_safe_expired()

**FSM Trace**:
From Idle state:
- T001: Idle -> CSRRequested
  - Guard: `session_is_CASE == true && fail_safe_armed == true && vid_verification_completed == true && prior_AddICAC_executed == false`
  - ✅ Guard includes `fail_safe_armed == true`

- T003: Idle -> ErrorState_NoFailSafe
  - Trigger: ICACCSRRequest
  - Guard: `fail_safe_armed == false`
  - ✅ Rejects when fail-safe not armed

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "If this command is received without an armed fail-safe context (see Section 11.10.7.2, "ArmFailSafe"), then this command SHALL fail with a FAILSAFE_REQUIRED status code sent back to the initiator."
Source: Section 11.25.7.1, "ICACCSRRequest Command", "Effect on Receipt", Paragraph 2
Context: Second requirement for ICACCSRRequest command
```

---

#### PROP_006: Fail_Safe_Context_Required_AddICAC
- **Status**: Analyzing...
- **Claim**: AddICAC must be received with an armed fail-safe context
- **Formal**: ∀cmd. event receive_AddICAC(cmd) ==> event fail_safe_armed() ∧ ¬event fail_safe_expired()

**FSM Trace**:
From CSRGenerated state:
- T007: CSRGenerated -> ValidatingICAC
  - Guard: `session_is_CASE == true && fail_safe_armed == true && prior_AddICAC_executed == false`
  - ✅ Guard includes `fail_safe_armed == true`

- T009: CSRGenerated -> ErrorState_NoFailSafe
  - Trigger: AddICAC
  - Guard: `fail_safe_armed == false`
  - ✅ Rejects when fail-safe not armed

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "If this command is received without an armed fail-safe context (see Section 11.10.7.2, "ArmFailSafe"), then this command SHALL fail with a FAILSAFE_REQUIRED status code sent back to the initiator."
Source: Section 11.25.7.3, "AddICAC Command", "Effect on Receipt", Paragraph 2
Context: Second requirement for AddICAC command
```

---

#### PROP_007: VID_Verification_Prerequisite
- **Status**: Analyzing...
- **Claim**: Fabric Table VID Verification Procedure must be executed before ICACCSRRequest is accepted
- **Formal**: ∀node, cmd. event accept_ICACCSRRequest(node, cmd) ==> event VID_verified(node)

**FSM Trace**:
From Idle state:
- T001: Idle -> CSRRequested
  - Guard: `session_is_CASE == true && fail_safe_armed == true && vid_verification_completed == true && prior_AddICAC_executed == false`
  - ✅ Guard includes `vid_verification_completed == true`

- T004: Idle -> ErrorState_VIDNotVerified
  - Trigger: ICACCSRRequest
  - Guard: `vid_verification_completed == false`
  - ✅ Rejects when VID not verified

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "If the Fabric Table Vendor ID Verification Procedure has not been executed against the initiator of this command, the command SHALL fail with a JfVidNotVerified status code SHALL be sent back to the initiator."
Source: Section 11.25.7.1, "ICACCSRRequest Command", "Effect on Receipt", Paragraph 3
Context: Third requirement for ICACCSRRequest command
```

---

#### PROP_008: Single_AddICAC_Per_Fail_Safe_Period
- **Status**: Analyzing...
- **Claim**: Only one AddICAC command may be successfully executed within a fail-safe timer period
- **Formal**: ∀cmd1, cmd2, t. event AddICAC_success(cmd1, t) ∧ event AddICAC_attempt(cmd2, t) ∧ cmd1 ≠ cmd2 ==> event fail_with_CONSTRAINT_ERROR(cmd2)

**FSM Trace**:

**Checking ICACCSRRequest**:
From Idle state:
- T001: Idle -> CSRRequested
  - Guard: `prior_AddICAC_executed == false`
  - ✅ Only accepts CSR request if AddICAC hasn't executed yet

- T005: Idle -> ErrorState_ConstraintViolation
  - Trigger: ICACCSRRequest
  - Guard: `prior_AddICAC_executed == true`
  - ✅ Rejects CSR request if AddICAC already executed

**Checking AddICAC**:
From CSRGenerated state:
- T007: CSRGenerated -> ValidatingICAC
  - Guard: `prior_AddICAC_executed == false`
  - ✅ Only accepts AddICAC if not already executed

- T010: CSRGenerated -> ErrorState_ConstraintViolation
  - Trigger: AddICAC
  - Guard: `prior_AddICAC_executed == true`
  - ✅ Rejects AddICAC if already executed

**Verdict**: **HOLDS**

**Specification Evidence**:

For ICACCSRRequest:
```
Quote: "If a prior AddICAC command was successfully executed within the fail-safe timer period, then this command SHALL fail with a CONSTRAINT_ERROR status code sent back to the initiator."
Source: Section 11.25.7.1, "ICACCSRRequest Command", "Effect on Receipt", Paragraph 4
Context: Fourth requirement for ICACCSRRequest command
```

For AddICAC:
```
Quote: "If a prior AddICAC command was successfully executed within the fail-safe timer period, then this command SHALL fail with a CONSTRAINT_ERROR status code sent back to the initiator."
Source: Section 11.25.7.3, "AddICAC Command", "Effect on Receipt", Paragraph 3
Context: Third requirement for AddICAC command
```

---

#### PROP_009: DN_Encoding_Validation
- **Status**: Analyzing...
- **Claim**: ICAC DN Encoding Rules must be validated
- **Formal**: ∀icac. event accept_ICAC(icac) ==> event DN_encoding_valid(icac)

**FSM Trace**:
From ValidatingICAC state:
- T011: ValidatingICAC -> ICACAccepted
  - Guard: `Crypto_VerifyChain(icac, rcac) == success && validate_public_key_match(icac_pubkey, csr_pubkey) == success && validate_DN_encoding(icac) == success`
  - ✅ Requires validate_DN_encoding success

- T014: ValidatingICAC -> ICACRejected_InvalidICAC
  - Guard: `Crypto_VerifyChain(icac, rcac) == success && validate_public_key_match(icac_pubkey, csr_pubkey) == success && validate_DN_encoding(icac) == failure`
  - ✅ Rejects when DN encoding validation fails

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "The DN Encoding Rules SHALL be validated for the ICAC. If this check fails, the error status SHALL be InvalidICAC."
Source: Section 11.25.7.3, "AddICAC Command", "Effect on Receipt", Validation check #3
Context: Third of three validation checks before accepting ICAC
```

---

#### PROP_010: ACL_Removal_Atomicity (TWO-PHASE COMMIT)
- **Status**: Analyzing...
- **Claim**: ACL removal follows two-phase commit: status updated to DeletePending, then either fully removed or CommitFailed
- **Formal**: ∀acl, n. event ACL_removal_started(acl, n) ==> eventually (event ACL_fully_removed(acl, n) ∧ event status_removed(acl)) ∨ (event ACL_removal_failed(acl, n) ∧ event status_commit_failed(acl))

**FSM Trace**:
From ACL_Active state:
- T024: ACL_Active -> ACL_DeletePending
  - Trigger: RemoveACLFromNode
  - Guard: `node_exists(NodeID) == true && acl_list_includes(ListID) == true`
  - Action: `update_acl_status(ListID, DeletePending); initiate_acl_removal_from_node(NodeID, ListID)`
  - ✅ Sets status to DeletePending and starts removal

From ACL_DeletePending state:
- T027: ACL_DeletePending -> ACL_Removed
  - Trigger: acl_removal_success
  - Action: `remove_acl_entry_from_list(ListID); update_acl_status(ListID, Removed)`
  - ✅ Success path: removes from list and updates status to Removed

- T028: ACL_DeletePending -> ACL_CommitFailed
  - Trigger: acl_removal_failure
  - Action: `update_acl_status(ListID, CommitFailed); set_failure_code(get_removal_error_code())`
  - ✅ Failure path: updates status to CommitFailed with error code

**Checking for violations**:
❓ **POTENTIAL ISSUE**: From ACL_DeletePending, are there any other exits besides T027 and T028?

Looking at all transitions from ACL_DeletePending:
- T027: -> ACL_Removed (success case)
- T028: -> ACL_CommitFailed (failure case)
- **No other transitions found** ✅

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "If it does:
    a. Update the status to `DeletePending` for the given ACLEntry in the ACL List.
    b. Remove this ACLEntry from the given Node ID.
        i. If this succeeds, remove the given ACLEntry from the Node ACL List.
        ii. If not successful, update the Status to `CommitFailed` and the FailureCode to the returned error. The error SHALL be handled in a subsequent Node Refresh."
Source: Section 11.24.7.20, "RemoveACLFromNode Command", Paragraph 2
Context: Describes two-phase commit protocol for ACL removal
```

---

## Violations Found So Far: 0

---

#### PROP_011: Command_Sequencing_ICACCSRRequest_Before_AddICAC
- **Status**: Analyzing...
- **Claim**: AddICAC must be issued after receiving ICACCSRResponse (command sequencing)
- **Formal**: ∀add, csr. event issue_AddICAC(add) ==> event received_ICACCSRResponse(csr) ∧ event before(csr, add)

**FSM Trace**:

Looking at where AddICAC can be received:

From **Idle** state:
- ❌ **NO TRANSITION** for AddICAC trigger from Idle

From **CSRRequested** state:
- ❌ **NO TRANSITION** for AddICAC trigger from CSRRequested

From **CSRGenerated** state:
- T007: CSRGenerated -> ValidatingICAC (AddICAC accepted here)
- ✅ This is the **correct** state after ICACCSRResponse sent

**Checking if AddICAC can be received WITHOUT prior CSR flow**:
- Idle state: No AddICAC transitions → Cannot skip CSR
- AwaitingVIDVerification: No AddICAC transitions
- CSRRequested: No AddICAC transitions
- Only CSRGenerated accepts AddICAC

**❓ POTENTIAL VIOLATION**: Can an attacker send AddICAC directly from Idle if they craft the message?

Looking at FSM more carefully:
- The FSM shows transitions from specific states
- AddICAC is ONLY accepted from CSRGenerated state
- To reach CSRGenerated, must go through: Idle -> CSRRequested (T001) -> CSRGenerated (T006)
- T001 requires ICACCSRRequest
- T006 generates CSR and sends ICACCSRResponse

**Verdict**: **HOLDS**

The FSM enforces sequencing by only accepting AddICAC from CSRGenerated state, which is only reachable after ICACCSRResponse is sent.

**Specification Evidence**:
```
Quote: "A Commissioner or Administrator SHALL issue this command after issuing the ICACCSRRequest command and receiving its response."
Source: Section 11.25.7.3, "AddICAC Command", Paragraph 2
Context: Requirement for command sequencing before AddICAC
```

---

#### PROP_012: Attestation_And_VID_Verification_Before_AddICAC
- **Status**: Analyzing...
- **Claim**: Attestation Procedure and Fabric Table VID Verification must be completed before AddICAC
- **Formal**: ∀c, n. event issue_AddICAC(c, n) ==> event attestation_procedure_completed(n) ∧ event fabric_VID_verified(n)

**FSM Trace**:

Looking at AddICAC acceptance (T007):
- From: CSRGenerated
- To: ValidatingICAC
- Guard: `session_is_CASE == true && fail_safe_armed == true && prior_AddICAC_executed == false`

**❓ ISSUE**: The guard does NOT check for attestation completion!

The specification says:
"A Commissioner or Administrator SHALL issue this command after performing the Attestation Procedure, Fabric Table VID Verification..."

But the FSM only checks VID verification for **ICACCSRRequest** (T001 guard: `vid_verification_completed == true`).

For **AddICAC** (T007), the guard is:
`session_is_CASE == true && fail_safe_armed == true && prior_AddICAC_executed == false`

**Missing guards**:
- ❌ No `attestation_completed` check
- ❌ No `vid_verification_completed` check (this was checked earlier at ICACCSRRequest, but not re-verified at AddICAC)

**🚨 POTENTIAL VIOLATION**: 

**Attack Scenario**:
1. Attacker completes VID verification and ICACCSRRequest successfully
2. Node generates CSR and sends ICACCSRResponse
3. **Administrator should perform attestation** at this point (per spec requirement)
4. But FSM does NOT check if attestation was performed before accepting AddICAC
5. Attacker could send AddICAC immediately without waiting for attestation
6. Node would accept AddICAC (T007) because all guards pass

**Specification says (SHOULD)**:
```
Quote: "A Commissioner or Administrator SHALL issue this command after performing the Attestation Procedure, Fabric Table VID Verification and after validating that the peer is authorized to act as an Administrator in its own Fabric."
Source: Section 11.25.7.3, "AddICAC Command", Paragraph 3
Context: Requirements for issuing AddICAC
```

**But specification also says (EFFECT ON RECEIPT)**:
Section 11.25.7.3 "Effect on Receipt" does NOT list attestation as a validation check!

The validation checks listed are:
1. Verify ICAC using Crypto_VerifyChain
2. Public key match
3. DN Encoding Rules

**No mention of checking attestation on receipt!**

**Analysis**:

The specification has **TWO different perspectives**:
1. **Issuer requirement** (Paragraph 3): Commissioner SHALL perform attestation before issuing
2. **Receiver requirement** ("Effect on Receipt"): Node SHALL validate chain, pubkey, DN

The **receiver** (node being commissioned) is NOT required to verify that attestation was performed. This is a **client-side obligation** not enforced by the server.

**Verdict**: **HOLDS (with caveat)**

The FSM correctly implements the **receiver side** of the specification. The attestation requirement is on the **issuer** (Commissioner/Administrator), not the receiver (node).

However, this creates a **trust assumption**: The node trusts that the Commissioner followed the specification and performed attestation before issuing AddICAC. If the Commissioner is malicious or buggy, it could skip attestation.

**Supporting Assumption**:
- ASSUMPTION_008: "Administrator Authorization is Correctly Verified"
- If violated: Non-administrator nodes gain ability to perform cross-signing

---

#### PROP_013: Administrator_Authorization_Validation
- **Status**: Analyzing...
- **Claim**: Peer must be validated as authorized administrator before AddICAC
- **Formal**: ∀c, p. event issue_AddICAC(c, p) ==> event verified_administrator(p, own_fabric(p))

**FSM Trace**:
Same analysis as PROP_012. This is an **issuer-side requirement**, not enforced by receiver.

**Verdict**: **HOLDS (with trust assumption)**

The FSM enforces CASE session authentication, which provides cryptographic proof that the peer is authorized on the fabric. Administrator role is implicit in the ability to establish CASE session and issue commands to the cluster.

**Specification Evidence**:
```
Quote: "A Commissioner or Administrator SHALL issue this command after performing the Attestation Procedure, Fabric Table VID Verification and after validating that the peer is authorized to act as an Administrator in its own Fabric."
Source: Section 11.25.7.3, "AddICAC Command", Paragraph 3
```

---

#### PROP_014: AdministratorFabricIndex_Not_Null_For_CommissioningWindow
- **Status**: Analyzing...
- **Claim**: OpenJointCommissioningWindow must fail if AdministratorFabricIndex is null
- **Formal**: ∀c. event process_OpenJointCommissioningWindow(c) ∧ event attribute_value_null(AdministratorFabricIndex) ==> event command_failed(c, InvalidAdministratorFabricIndex)

**FSM Trace**:
From CommissioningWindow_Closed state:
- T031: CommissioningWindow_Closed -> CommissioningWindow_Open
  - Guard: `AdministratorFabricIndex != null && validate_pake_parameters(verifier, iterations, salt) == success && commissioning_not_in_progress == true`
  - ✅ Requires `AdministratorFabricIndex != null`

- T032: CommissioningWindow_Closed -> CommissioningWindow_Error_NullFabricIndex
  - Trigger: OpenJointCommissioningWindow
  - Guard: `AdministratorFabricIndex == null`
  - ✅ Fails with error when null

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "This command SHALL fail with a InvalidAdministratorFabricIndex status code sent back to the initiator if the AdministratorFabricIndex attribute has the value of null."
Source: Section 11.25.7.5, "OpenJointCommissioningWindow Command", Paragraph 1
```

---

#### PROP_015: Node_Not_Found_Error_RemoveACL
- **Status**: Analyzing...
- **Claim**: RemoveACLFromNode returns NOT_FOUND if NodeID doesn't exist
- **Formal**: ∀nid, lid. event process_RemoveACLFromNode(nid, lid) ∧ event node_not_exists(nid) ==> event return_error(NOT_FOUND)

**FSM Trace**:
From ACL_Active state:
- T024: ACL_Active -> ACL_DeletePending
  - Guard: `node_exists(NodeID) == true && acl_list_includes(ListID) == true`
  - ✅ Only proceeds if node exists

- T025: ACL_Active -> ACL_NodeNotFound
  - Trigger: RemoveACLFromNode
  - Guard: `node_exists(NodeID) == false`
  - Action: `send_error_response(NOT_FOUND, "Node not found")`
  - ✅ Returns NOT_FOUND when node doesn't exist

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "Confirm that a Node Information Entry exists for the given NodeID, and if not, return NOT_FOUND."
Source: Section 11.24.7.20, "RemoveACLFromNode Command", Step 1
```

---

#### PROP_016: ACL_Commit_Failed_Status_On_Removal_Failure
- **Status**: Analyzing...
- **Claim**: If ACL removal fails, status must be CommitFailed with error code
- **Formal**: ∀acl, n, err. event ACL_removal_operation_failed(acl, n, err) ==> event status_updated(acl, CommitFailed) ∧ event failure_code_set(acl, err)

**FSM Trace**:
From ACL_DeletePending state:
- T028: ACL_DeletePending -> ACL_CommitFailed
  - Trigger: acl_removal_failure
  - Guard: `acl_removal_from_node_failed == true`
  - Action: `update_acl_status(ListID, CommitFailed); set_failure_code(get_removal_error_code())`
  - ✅ Sets CommitFailed status with error code

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "If not successful, update the Status to `CommitFailed` and the FailureCode to the returned error."
Source: Section 11.24.7.20, "RemoveACLFromNode Command", Step 2.b.ii
```

---

#### PROP_017: Anchor_Transfer_Requires_User_Consent
- **Status**: Analyzing...
- **Claim**: Anchor transfer must fail if user consent not given
- **Formal**: ∀req. event process_TransferAnchorRequest(req) ∧ event user_consent_not_given() ==> event transfer_failed(req, NoUserConsent)

**FSM Trace**:
From AnchorTransfer_RequestReceived state:
- T041: AnchorTransfer_RequestReceived -> AnchorTransfer_InProgress
  - Guard: `user_consent_given == true && datastore_busy == false`
  - ✅ Requires user consent

- T042: AnchorTransfer_RequestReceived -> AnchorTransfer_Rejected_NoConsent
  - Trigger: preconditions_checked
  - Guard: `user_consent_given == false`
  - Action: `send_TransferAnchorResponse(NoUserConsent)`
  - ✅ Rejects with NoUserConsent error

**Verdict**: **HOLDS**

**Specification Evidence**:
The specification doesn't explicitly state the user consent requirement in Section 11.25, but the FSM models it. The TransferAnchorResponseStatusEnum includes "TransferAnchorStatusNoUserConsent" error code.

```
Quote: "TransferAnchorStatusNoUserConsent ... User has not consented for Anchor Transfer"
Source: Section 11.25.4.2, "TransferAnchorResponseStatusEnum Type", Value 2
```

---

#### PROP_018: Anchor_Transfer_Requires_Datastore_Idle
- **Status**: Analyzing...
- **Claim**: Anchor transfer must fail if datastore operations ongoing
- **Formal**: ∀req. event process_TransferAnchorRequest(req) ∧ event datastore_operations_ongoing() ==> event transfer_failed(req, DatastoreBusy)

**FSM Trace**:
From AnchorTransfer_RequestReceived state:
- T041: AnchorTransfer_RequestReceived -> AnchorTransfer_InProgress
  - Guard: `user_consent_given == true && datastore_busy == false`
  - ✅ Requires datastore not busy

- T043: AnchorTransfer_RequestReceived -> AnchorTransfer_Rejected_DatastoreBusy
  - Trigger: preconditions_checked
  - Guard: `datastore_busy == true`
  - Action: `send_TransferAnchorResponse(DatastoreBusy)`
  - ✅ Rejects with DatastoreBusy error

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "TransferAnchorStatusDatastoreBusy ... Anchor Transfer was not started due to ongoing Datastore operations"
Source: Section 11.25.4.2, "TransferAnchorResponseStatusEnum Type", Value 1
```

---

## Checking for Violations in Remaining Properties

Let me continue more systematically, looking specifically for **violations** rather than confirmations...

#### PROP_033: Fail_Safe_Atomicity
- **Status**: Analyzing...
- **Claim**: All operations must be rolled back atomically when fail-safe expires
- **Formal**: ∀ops, t. event fail_safe_expired(t) ==> ∀op. op ∈ ops ⟹ event operation_rolled_back(op)

**FSM Trace**:
From ICACAccepted state:
- T016: ICACAccepted -> Idle
  - Trigger: fail_safe_expired
  - Guard: `fail_safe_timer_expired == true`
  - Action: `rollback_all_operations(); reset_commissioning_state()`
  - ✅ Rolls back all operations

**But checking other states for fail-safe expiration**:

From CSRRequested state:
- ❌ **NO TRANSITION** for fail_safe_expired trigger

From CSRGenerated state:
- ❌ **NO TRANSITION** for fail_safe_expired trigger

From ValidatingICAC state:
- ❌ **NO TRANSITION** for fail_safe_expired trigger

**🚨 VIOLATION FOUND!**

**Attack Path**:
1. Node in CSRGenerated state (after ICACCSRResponse sent, waiting for AddICAC)
2. Fail-safe timer expires
3. **No rollback transition exists!**
4. Node stuck in CSRGenerated state with CSR public key stored
5. Partial state persists beyond fail-safe period

**Specification Claims**:
```
Quote: "If this command is received without an armed fail-safe context (see Section 11.10.7.2, "ArmFailSafe"), then this command SHALL fail with a FAILSAFE_REQUIRED status code sent back to the initiator."
Source: Section 11.25.7.1 and 11.25.7.3
Context: Implies fail-safe protection for entire commissioning flow
```

**Specification Gap**:
The specification requires fail-safe context but doesn't explicitly state what happens when fail-safe expires in intermediate states (CSRRequested, CSRGenerated, ValidatingICAC). Only ICACAccepted state has rollback transition.

**Verdict**: **VIOLATED**

**Severity**: **CRITICAL**

---

#### PROP_036: ACL_Removal_State_Determinism
- **Status**: Analyzing...
- **Claim**: ACL removal must transition exclusively to either Removed or CommitFailed (no other outcomes)
- **Formal**: ∀acl. event ACL_removal_initiated(acl) ==> eventually (event status_transition(acl, removed) ∨ event status_transition(acl, CommitFailed))

**FSM Trace**:
From ACL_DeletePending state:
- T027: ACL_DeletePending -> ACL_Removed ✅
- T028: ACL_DeletePending -> ACL_CommitFailed ✅

**Checking for other exits**:
- ❌ **NO OTHER TRANSITIONS** from ACL_DeletePending

**But what if fail-safe expires? Or system crashes?**

Looking for fail-safe, error, or reset transitions from ACL_DeletePending:
- ❌ **NO TRANSITION** for fail_safe_expired
- ❌ **NO TRANSITION** for system_reset
- ❌ **NO TRANSITION** for timeout

**🚨 POTENTIAL ISSUE**: What happens if:
1. ACL removal initiated (state = ACL_DeletePending)
2. System crashes or power loss before completion
3. On restart, what is the ACL state?

The FSM doesn't model recovery from system failures. However, the specification says:

```
Quote: "The error SHALL be handled in a subsequent Node Refresh."
Source: Section 11.24.7.20, "RemoveACLFromNode Command", Step 2.b.ii
```

This implies there's a recovery mechanism (Node Refresh) outside this FSM.

**Verdict**: **HOLDS (with recovery mechanism assumption)**

The FSM correctly models the two-phase commit for the happy path and error path. Recovery from crashes is handled by external Node Refresh mechanism.

---

#### PROP_024: PAKE_Parameters_Validation
- **Status**: Analyzing...
- **Claim**: PAKE parameters must be validated (verifier 97 bytes, iterations 1000-100000, salt 16-32 bytes)
- **Formal**: ∀p. event open_commissioning_window(p) ==> event PAKE_verifier_valid(p.verifier) ∧ event PAKE_iterations_valid(p.iterations) ∧ event PAKE_salt_valid(p.salt)

**FSM Trace**:
From CommissioningWindow_Closed state:
- T031: CommissioningWindow_Closed -> CommissioningWindow_Open
  - Guard: `AdministratorFabricIndex != null && validate_pake_parameters(verifier, iterations, salt) == success && commissioning_not_in_progress == true`
  - ✅ Validates PAKE parameters

- T033: CommissioningWindow_Closed -> CommissioningWindow_Error_PAKEParams
  - Trigger: OpenJointCommissioningWindow
  - Guard: `validate_pake_parameters(verifier, iterations, salt) == failure`
  - ✅ Fails if parameters invalid

**Checking function definition**:
```json
{
  "name": "validate_pake_parameters",
  "parameters": ["verifier:octstr(97)", "iterations:uint32(1000-100000)", "salt:octstr(16-32)"],
  "returns": "boolean",
  "algorithm": "1. Verify verifier is exactly 97 bytes\n2. Verify iterations in range [1000, 100000]\n3. Verify salt in range [16, 32] bytes\n4. Return true if all checks pass, false otherwise"
}
```

✅ Function correctly validates all three parameters

**Verdict**: **HOLDS**

**Specification Evidence**:
```
Quote: "PAKEPasscodeVerifier ... octstr ... 97"
Source: Section 11.25.7.5, "OpenJointCommissioningWindow Command", Parameter 1

Quote: "Iterations ... uint32 ... 1000 to 100000"
Source: Section 11.25.7.5, "OpenJointCommissioningWindow Command", Parameter 3

Quote: "Salt ... octstr ... 16 to 32"
Source: Section 11.25.7.5, "OpenJointCommissioningWindow Command", Parameter 4
```

---

#### PROP_030: Command_Sequence_Completeness_Joint_Commissioning
- **Status**: Analyzing...
- **Claim**: Complete command sequence must be followed: ICACCSRRequest → ICACCSRResponse → AddICAC → ICACResponse
- **Formal**: ∀s. event certificate_cross_signing_complete(s) ==> event command_sequence_valid(ICACCSRRequest, ICACCSRResponse, AddICAC, ICACResponse, s)

**FSM Trace**:
Complete path through joint commissioning:
1. **Idle** --(ICACCSRRequest, T001)--> **CSRRequested**
2. **CSRRequested** --(generate_csr_success, T006)--> **CSRGenerated** [ICACCSRResponse sent here]
3. **CSRGenerated** --(AddICAC, T007)--> **ValidatingICAC**
4. **ValidatingICAC** --(validation_complete, T011)--> **ICACAccepted** [ICACResponse sent here]
5. **ICACAccepted** --(fail_safe_complete, T015)--> **CommissioningComplete**

✅ The FSM enforces this sequence through state transitions

**But checking**: Can we skip any steps?

❓ **Can we go directly from Idle to ValidatingICAC?**
- No, because ValidatingICAC only has incoming transitions from CSRGenerated (T007)

❓ **Can we send AddICAC before ICACCSRResponse?**
- No, because AddICAC only accepted in CSRGenerated state
- CSRGenerated only reachable after ICACCSRResponse sent (T006)

**Verdict**: **HOLDS**

---

#### PROP_019: CSR_Format_PKCS10_DER
- **Status**: Analyzing...
- **Claim**: CSR must be DER-encoded PKCS#10 format
- **Formal**: ∀csr. event process_ICACCSR(csr) ==> event is_DER_encoded(csr) ∧ event is_PKCS10_CSR(csr)

**FSM Trace**:
From CSRRequested state:
- T006: CSRRequested -> CSRGenerated
  - Action: `csr := generate_PKCS10_CSR_DER_encoded(...)`

**Checking function definition**:
```json
{
  "name": "generate_PKCS10_CSR_DER_encoded",
  "algorithm": "1. Generate ECDSA-SHA256 key pair\n2. Create PKCS#10 CSR structure with key\n3. DER-encode the CSR\n4. Sign CSR with private key\n5. Return DER-encoded CSR"
}
```

✅ Function generates DER-encoded PKCS#10 CSR

**But wait - what about RECEIVING CSR?**

The property asks about **processing** CSR, which could mean:
1. **Generating** CSR (node side) ✅ Correct format
2. **Receiving/Validating** CSR (administrator side) ❓ Not modeled in FSM

The FSM only models the **node side** (server), not the administrator side (client) that receives and validates the CSR.

**Verdict**: **HOLDS (for node-side generation)**

The FSM correctly generates DER-encoded PKCS#10 CSR. Validation on administrator side is outside FSM scope.

---

#### PROP_042: CSR_Size_Limit_600_Bytes
- **Status**: Analyzing...
- **Claim**: CSR must not exceed 600 bytes
- **Formal**: ∀csr. event send_ICACCSR(csr) ==> byte_length(csr) <= 600

**FSM Trace**:
Looking at CSR generation and sending:
- T006: CSRRequested -> CSRGenerated
  - Action: `csr := generate_PKCS10_CSR_DER_encoded(node_id, fabric_id); csr_public_key := extract_public_key_from_csr(csr); send_ICACCSRResponse(csr)`

**Checking function definition for send_ICACCSRResponse**:
```json
{
  "name": "send_ICACCSRResponse",
  "algorithm": "1. Package CSR in ICACCSRResponse structure\n2. Send response to initiator"
}
```

❌ **NO SIZE VALIDATION** in the send function

**Checking generate_PKCS10_CSR_DER_encoded**:
```json
{
  "algorithm": "1. Generate ECDSA-SHA256 key pair\n2. Create PKCS#10 CSR structure with key\n3. DER-encode the CSR\n4. Sign CSR with private key\n5. Return DER-encoded CSR"
}
```

❌ **NO SIZE CHECK** - function doesn't verify output is ≤600 bytes

**🚨 POTENTIAL VIOLATION**:

The FSM generates CSR but doesn't validate its size before sending. If the CSR generation produces >600 bytes (e.g., due to large Distinguished Name fields), it would violate the constraint.

**However**: 
- PKCS#10 CSR with ECDSA-SHA256 and typical DN fields is ~300-400 bytes
- Exceeding 600 bytes would require extremely long DN fields or extensions
- Specification constraint exists on the **protocol level** (octstr max 600)

**Attack Scenario**:
1. Malicious implementation generates CSR with very long DN fields (>600 bytes)
2. Function generates and sends CSR without size check
3. Receiving administrator may reject (if it validates), or may accept oversized CSR
4. Protocol violation

**Specification Evidence**:
```
Quote: "ICACCSR ... octstr ... max 600"
Source: Section 11.25.7.2, "ICACCSRResponse Command", ICACCSR field
```

**Verdict**: **VIOLATED**

**Specification Gap**: 
The specification defines the constraint but doesn't specify WHERE the validation should occur:
- Should the generator enforce ≤600 bytes?
- Should the receiver reject >600 bytes?
- Current FSM has no size validation

**Severity**: **MEDIUM** (Implementation-dependent; unlikely in practice but possible)

---

#### PROP_043: ICAC_Size_Limit_400_Bytes
- **Status**: Analyzing...
- **Claim**: ICAC must not exceed 400 bytes
- **Formal**: ∀icac. event send_ICACValue(icac) ==> byte_length(icac) <= 400

**FSM Trace**:
Looking at ICAC reception (AddICAC command):
- T007: CSRGenerated -> ValidatingICAC
  - Trigger: AddICAC
  - Action: `icac := extract_icac_from_command(AddICAC)`

❌ **NO SIZE VALIDATION** when receiving ICAC

The FSM extracts ICAC and proceeds to validation (chain, pubkey, DN) but never checks size.

**Validation checks in T011-T014**:
1. Crypto_VerifyChain ✅
2. validate_public_key_match ✅
3. validate_DN_encoding ✅
4. **Size check** ❌ MISSING

**🚨 VIOLATION FOUND!**

**Attack Path**:
1. Administrator generates ICAC >400 bytes (e.g., with long DN fields or extensions)
2. Sends AddICAC command with oversized ICAC
3. Node receives and extracts ICAC (T007)
4. Node validates chain, pubkey, DN (T011-T014)
5. **No size check occurs**
6. If all validations pass, node accepts oversized ICAC (T011)
7. Protocol constraint violated

**Specification Evidence**:
```
Quote: "ICACValue ... octstr ... max 400"
Source: Section 11.25.7.3, "AddICAC Command", ICACValue Field
```

**Specification Gap**:
The validation checks listed in "Effect on Receipt" are:
1. Verify chain
2. Public key match
3. DN encoding

**Size validation is NOT listed** as a required check, even though the field has "max 400" constraint.

**Verdict**: **VIOLATED**

**Severity**: **MEDIUM** (Similar to PROP_042 - implementation-dependent)

---

## VIOLATIONS SUMMARY SO FAR

### Violation 1: PROP_033 - Fail_Safe_Atomicity
- **Issue**: No fail-safe expiration transitions from CSRRequested, CSRGenerated, ValidatingICAC states
- **Impact**: Partial commissioning state persists beyond fail-safe period
- **Severity**: CRITICAL

### Violation 2: PROP_042 - CSR_Size_Limit_600_Bytes  
- **Issue**: No size validation when generating/sending CSR
- **Impact**: CSR >600 bytes could be sent, violating protocol constraint
- **Severity**: MEDIUM

### Violation 3: PROP_043 - ICAC_Size_Limit_400_Bytes
- **Issue**: No size validation when receiving ICAC
- **Impact**: ICAC >400 bytes could be accepted, violating protocol constraint
- **Severity**: MEDIUM

---

### HIGH Priority Properties

#### PROP_020: ICAC_Format_Matter_Certificate_Encoding
- **Status**: Analyzing...
- **Claim**: ICAC must use Matter Certificate Encoding
- **Formal**: ∀icac. event send_ICACValue(icac) ==> event is_matter_certificate_encoding(icac)

**FSM Trace**:
From ValidatingICAC state:
- T011: ValidatingICAC -> ICACAccepted
  - Guard includes: `validate_DN_encoding(icac) == success`

**Checking validate_DN_encoding function**:
```json
{
  "name": "validate_DN_encoding",
  "algorithm": "1. Parse ICAC certificate\n2. Extract DN fields\n3. Validate DN encoding follows Matter Certificate Encoding rules\n4. Verify required fields present and correctly formatted\n5. Return success if valid, failure otherwise"
}
```

✅ Function validates Matter Certificate Encoding for DN fields

**Specification Evidence**:
```
Quote: "This field SHALL contain an ICAC encoded using Matter Certificate Encoding."
Source: Section 11.25.7.3, "AddICAC Command", ICACValue Field
```

**Verdict**: **HOLDS**

---

#### PROP_022: Immediate_Error_Response_On_Validation_Failure
- **Status**: Analyzing...
- **Claim**: Server must immediately respond with error status on validation failure
- **Formal**: ∀icac, err. event validate_ICAC_failed(icac, err) ==> event send_ICACResponse_immediately(err)

**FSM Trace**:
From ValidatingICAC state:
- T012: ValidatingICAC -> ICACRejected_InvalidICAC
  - Trigger: validation_complete
  - Guard: `Crypto_VerifyChain(icac, rcac) == failure`
  - Action: `send_ICACResponse(InvalidICAC, "Chain validation failed")`

- T013: ValidatingICAC -> ICACRejected_InvalidPublicKey
  - Trigger: validation_complete
  - Guard: `validate_public_key_match(icac_pubkey, csr_pubkey) == failure`
  - Action: `send_ICACResponse(InvalidPublicKey, "Public key mismatch")`

- T014: ValidatingICAC -> ICACRejected_InvalidICAC
  - Trigger: validation_complete
  - Guard: `validate_DN_encoding(icac) == failure`
  - Action: `send_ICACResponse(InvalidICAC, "DN encoding invalid")`

✅ All validation failures send immediate error response

**But checking timing**:

The transitions all require `validation_complete` trigger. This means:
1. AddICAC received (T007)
2. Enter ValidatingICAC state
3. **Wait for validation_complete trigger**
4. Then send response (T012/T013/T014)

❓ **Is this "immediate"?**

The specification says:
```
Quote: "If any of the above validation checks fail, the server SHALL immediately respond to the client with an ICACResponse."
Source: Section 11.25.7.3, "AddICAC Command", "Effect on Receipt"
```

The FSM models validation as:
- T007: Receive AddICAC → Enter ValidatingICAC
- Actions in T007: `icac := extract_icac_from_command(AddICAC); start_validation_sequence(icac, csr_public_key)` 
- Then wait for `validation_complete` trigger
- Then send response (T012/T013/T014)

**Issue**: The FSM introduces a **delay** between receiving AddICAC and sending response. The `validation_complete` trigger impliesan asynchronous validation process, not immediate synchronous response.

**However**: This might be acceptable if "immediate" means "right after validation completes" rather than "synchronously in the command handler."

**Verdict**: **HOLDS (with timing caveat)**

The FSM sends response immediately after validation completes. The validation itself may take time (chain verification, public key comparison), so some delay is necessary. "Immediately" likely means "without unnecessary delay" rather than "synchronously."

---

#### PROP_025: Commissioning_Window_Open_Required
- **Status**: Analyzing...
- **Claim**: Commissioning operations require open commissioning window
- **Formal**: ∀op. event process_commissioning_operation(op) ==> event commissioning_window_is_open() ∨ event operation_rejected(op, WindowNotOpen)

**FSM Trace**:

**Issue**: The FSM doesn't model the relationship between commissioning window and commissioning operations!

Looking at joint commissioning flow:
- ICACCSRRequest accepted from **Idle** state (T001)
- No check for commissioning window state

Looking at commissioning window states:
- CommissioningWindow_Closed (initial)
- CommissioningWindow_Open
- CommissioningWindow_Expired

There are **NO TRANSITIONS** between commissioning states and joint commissioning states.

**🚨 VIOLATION FOUND!**

**Attack Path**:
1. Commissioning window is **closed** (CommissioningWindow_Closed state)
2. Attacker sends ICACCSRRequest
3. FSM accepts it if CASE session authenticated, fail-safe armed, VID verified (T001)
4. **No check** for commissioning window being open
5. Joint commissioning proceeds even though window closed

**Specification Gap**:

The specification for OpenJointCommissioningWindow says:
```
Quote: "This is an alias onto the OpenCommissioningWindow command within the Joint Fabric Administrator Cluster."
Source: Section 11.25.7.5
```

But the Effect on Receipt sections for ICACCSRRequest and AddICAC don't mention requiring an open commissioning window!

**Cross-reference**: In standard commissioning (Section 11.10), OpenCommissioningWindow opens a window for PASE-based commissioning. But ICACCSRRequest uses CASE, not PASE.

**Analysis**:

CASE-based joint commissioning may not require an open commissioning window because:
- It's over an already-established CASE session (authenticated)
- It's for cross-fabric commissioning, not initial device commissioning

However, the property claims commissioning operations require open window. If this is meant to apply to joint commissioning, then it's violated.

**Verdict**: **UNVERIFIABLE (specification ambiguous)**

The specification doesn't clearly state whether joint commissioning (over CASE) requires an open commissioning window. The window seems to be for PASE-based commissioning only.

**Alternative interpretation**: PROP_025 may not apply to joint commissioning at all, only to initial commissioning.

---

#### PROP_026: Prevent_Concurrent_Commissioning_Operations
- **Status**: Analyzing...
- **Claim**: Only one commissioning operation at a time (reject concurrent attempts with Busy)
- **Formal**: ∀op1, op2. event commissioning_in_progress(op1) ∧ event attempt_commissioning(op2) ∧ op1 ≠ op2 ==> event commissioning_rejected(op2, Busy)

**FSM Trace**:

Looking for concurrent operation prevention:

From Idle state:
- T001: Idle -> CSRRequested (first commissioning starts)

Now, can a second ICACCSRRequest arrive while in CSRRequested state?
- ❌ **NO TRANSITION** for ICACCSRRequest from CSRRequested

Can ICACCSRRequest arrive while in CSRGenerated?
- ❌ **NO TRANSITION** for ICACCSRRequest from CSRGenerated

Can ICACCSRRequest arrive while in ValidatingICAC?
- ❌ **NO TRANSITION** for ICACCSRRequest from ValidatingICAC

**Good!** The FSM implicitly prevents concurrent commissioning by:
1. Only accepting ICACCSRRequest from Idle state
2. Once commissioning starts (leaves Idle), no new ICACCSRRequest accepted
3. Must return to Idle (via T015, T017, T018, etc.) before new commissioning

**But**: Does it send Busy error?

Looking for Busy error response:
- ErrorState_Busy exists in FSM
- T034: CommissioningWindow_Closed -> ErrorState_Busy
  - Trigger: OpenJointCommissioningWindow
  - Guard: `commissioning_not_in_progress == false`
  - Action: `send_error_response(Busy, "Commissioning in progress")`

✅ OpenJointCommissioningWindow can fail with Busy

**But what about ICACCSRRequest while commissioning in progress?**

Looking at ICACCSRRequest transitions:
- T001: Idle -> CSRRequested (accepts)
- T002: Idle -> ErrorState_InvalidSession (non-CASE)
- T003: Idle -> ErrorState_NoFailSafe (no fail-safe)
- T004: Idle -> ErrorState_VIDNotVerified (no VID)
- T005: Idle -> ErrorState_ConstraintViolation (prior AddICAC)

❌ **NO TRANSITION** from non-Idle states for ICACCSRRequest

**🚨 POTENTIAL VIOLATION**:

If ICACCSRRequest arrives while in CSRRequested, CSRGenerated, or ValidatingICAC:
- No transition exists in FSM
- Should return Busy error
- But FSM has no such transition

**However**: This could be a **protocol-level enforcement** outside FSM scope:
- Node in commissioning ignores/drops packets for new ICACCSRRequest
- Or transport layer rejects
- Or application layer returns Busy before FSM processing

**Checking if this is modeled elsewhere**:

The guard `commissioning_not_in_progress == false` appears in T034 (OpenJointCommissioningWindow).

But there's no similar guard or transition for ICACCSRRequest during commissioning.

**Verdict**: **VIOLATED (Incomplete Busy handling)**

**Severity**: **MEDIUM**

The FSM doesn't handle concurrent ICACCSRRequest attempts with explicit Busy rejection. While the FSM implicitly prevents concurrent commissioning by state design, it doesn't model the Busy error response for attempts during in-progress commissioning.

---

#### PROP_027: Discriminator_Range_Validation
- **Status**: Analyzing...  
- **Claim**: Discriminator must be ≤4095
- **Formal**: ∀p. event validate_commissioning_params(p) ==> p.discriminator <= 4095

**FSM Trace**:

Looking at OpenJointCommissioningWindow:
- T031: CommissioningWindow_Closed -> CommissioningWindow_Open
  - Guard: `validate_pake_parameters(verifier, iterations, salt) == success`

**But discriminator is NOT in validate_pake_parameters function!**

Checking the function definition:
```json
{
  "name": "validate_pake_parameters",
  "parameters": ["verifier:octstr(97)", "iterations:uint32(1000-100000)", "salt:octstr(16-32)"]
}
```

❌ **Discriminator is NOT validated!**

OpenJointCommissioningWindow has parameters:
1. CommissioningTimeout
2. PAKEPasscodeVerifier
3. **Discriminator** (max 4095)
4. Iterations
5. Salt

But the FSM only validates: verifier, iterations, salt

**🚨 VIOLATION FOUND!**

**Attack Path**:
1. Attacker sends OpenJointCommissioningWindow with discriminator > 4095 (e.g., 65535)
2. FSM validates PAKE parameters (verifier, iterations, salt) ✅
3. **No discriminator validation**
4. Window opens with invalid discriminator (T031)
5. Constraint violated

**Specification Evidence**:
```
Quote: "Discriminator ... uint16 ... max 4095"
Source: Section 11.25.7.5, "OpenJointCommissioningWindow Command", Parameter 2
```

**Verdict**: **VIOLATED**

**Severity**: **HIGH** (Security parameter validation missing)

---

#### PROP_028: PAKE_Iterations_Range_Validation
- **Status**: Analyzing...
- **Claim**: PAKE iterations must be in range [1000, 100000]
- **Formal**: ∀p. event validate_PAKE_params(p) ==> p.iterations >= 1000 ∧ p.iterations <= 100000

**FSM Trace**:
Already checked in PROP_024 ✅

validate_pake_parameters function includes iterations validation.

**Verdict**: **HOLDS**

---

#### PROP_029: PAKE_Salt_Length_Validation
- **Status**: Analyzing...
- **Claim**: PAKE salt must be 16-32 bytes
- **Formal**: ∀p. event validate_PAKE_params(p) ==> byte_length(p.salt) >= 16 ∧ byte_length(p.salt) <= 32

**FSM Trace**:
Already checked in PROP_024 ✅

validate_pake_parameters function includes salt length validation.

**Verdict**: **HOLDS**

---

## UPDATED VIOLATIONS SUMMARY

### Violation 1: PROP_033 - Fail_Safe_Atomicity
- **Issue**: No fail-safe expiration transitions from CSRRequested, CSRGenerated, ValidatingICAC states
- **Impact**: Partial commissioning state persists beyond fail-safe period
- **Severity**: **CRITICAL**

### Violation 2: PROP_026 - Prevent_Concurrent_Commissioning_Operations
- **Issue**: No Busy error response for concurrent ICACCSRRequest during in-progress commissioning
- **Impact**: Concurrent commissioning attempts not explicitly rejected
- **Severity**: **MEDIUM**

### Violation 3: PROP_027 - Discriminator_Range_Validation  
- **Issue**: Discriminator parameter (max 4095) not validated in OpenJointCommissioningWindow
- **Impact**: Invalid discriminator values accepted
- **Severity**: **HIGH**

### Violation 4: PROP_042 - CSR_Size_Limit_600_Bytes
- **Issue**: No size validation when generating/sending CSR
- **Impact**: CSR >600 bytes could be sent
- **Severity**: **MEDIUM**

### Violation 5: PROP_043 - ICAC_Size_Limit_400_Bytes
- **Issue**: No size validation when receiving ICAC
- **Impact**: ICAC >400 bytes could be accepted
- **Severity**: **MEDIUM**

---

#### PROP_035: State_Machine_Exclusivity
- **Status**: Analyzing...
- **Claim**: Only one state machine should be active at a time per node
- **Formal**: ∀n, s1, s2. event state_machine_active(n, s1) ∧ event state_machine_active(n, s2) ==> s1 = s2

**FSM Trace**:

The FSM model shows **4 separate state machines**:
1. **Joint Commissioning** (Idle, CSRRequested, CSRGenerated, ValidatingICAC, ICACAccepted, CommissioningComplete, + error states)
2. **ACL Management** (ACL_Active, ACL_DeletePending, ACL_Removed, ACL_CommitFailed, ACL_NodeNotFound)
3. **Commissioning Window** (CommissioningWindow_Closed, CommissioningWindow_Open, CommissioningWindow_Expired, + error states)
4. **Anchor Transfer** (AnchorTransfer_Idle, AnchorTransfer_RequestReceived, AnchorTransfer_InProgress, AnchorTransfer_Complete, + error states)

**Checking for concurrent execution**:

Can Joint Commissioning and ACL Management run simultaneously?
- Joint Commissioning: Idle -> CSRRequested -> ...
- ACL Management: ACL_Active is initial state
- ❌ **NO GUARDS** checking if ACL operations ongoing before allowing commissioning
- ❌ **NO GUARDS** checking if commissioning ongoing before allowing ACL operations

**🚨 VIOLATION FOUND!**

**Attack Path**:
1. Node in **CSRGenerated** state (joint commissioning in progress)
2. Simultaneously, ACL is in **ACL_Active** state
3. Administrator sends **RemoveACLFromNode** command
4. FSM accepts and processes (T024: ACL_Active -> ACL_DeletePending)
5. **Concurrent state machines active**: Joint Commissioning AND ACL Management
6. Potential race conditions or resource conflicts

Similarly:
- Joint Commissioning can run while Commissioning Window operations in progress
- Anchor Transfer can run while ACL Management in progress
- All 4 state machines operate **independently** with no mutual exclusion

**Specification Evidence**:

The specification doesn't explicitly state mutual exclusion for these operations. However, some operations should logically be mutually exclusive:

For Anchor Transfer:
```
Quote: "TransferAnchorStatusDatastoreBusy ... Anchor Transfer was not started due to ongoing Datastore operations"
Source: Section 11.25.4.2
```

This implies Anchor Transfer should check for other operations, but the FSM only checks `datastore_busy` flag, not specific operation state.

**Verdict**: **VIOLATED (No mutual exclusion enforcement)**

**Severity**: **HIGH** (Can lead to race conditions and inconsistent state)

---

#### PROP_031: Public_Key_Session_Binding
- **Status**: Analyzing...
- **Claim**: Public key in CSR remains bound to session through AddICAC
- **Formal**: ∀s, pk, icac. event CSR_generated(s, pk) ∧ event ICAC_accepted(s, icac) ==> extract_public_key(icac) = pk

**FSM Trace**:

From CSRRequested to CSRGenerated (T006):
- Action: `csr := generate_PKCS10_CSR_DER_encoded(...); csr_public_key := extract_public_key_from_csr(csr)`
- Stores public key in state variable: `csr_public_key`

From CSRGenerated to ValidatingICAC (T007):
- Guard: `session_is_CASE == true && fail_safe_armed == true && prior_AddICAC_executed == false`
- Action: `icac := extract_icac_from_command(AddICAC)`

From ValidatingICAC to ICACAccepted (T011):
- Guard: `validate_public_key_match(icac_pubkey, csr_pubkey) == success`
- ✅ Validates public key match

**Checking for session binding**:

The FSM validates that icac_pubkey == csr_pubkey, but:
❓ **Is this bound to the same session?**

Issue: The FSM allows multiple sessions to interleave:
1. Session A: ICACCSRRequest -> CSRRequested -> CSRGenerated (stores csr_pubkey_A)
2. Session B: ICACCSRRequest -> ❌ **Rejected** (not from Idle)
3. Session B: AddICAC -> **But which session's CSR is used?**

Actually, looking at the FSM:
- Only ONE CSR can be active at a time (single-threaded state machine)
- CSRGenerated state stores ONE csr_public_key
- AddICAC compares against THIS stored key

**But what if Session A generates CSR, then Session B sends AddICAC?**

From CSRGenerated:
- T007: AddICAC from ANY session (as long as session_is_CASE == true)
- No guard checking: `session_id_matches_CSR_session`

**🚨 POTENTIAL VIOLATION**:

**Attack Path**:
1. Legitimate Admin A sends ICACCSRRequest via Session A
2. Node generates CSR_A, stores pubkey_A, sends ICACCSRResponse to Admin A
3. **Malicious Admin B** (different session) sends AddICAC with ICAC_B (signed for different key)
4. FSM checks: session_is_CASE == true ✅ (Session B is also CASE)
5. FSM compares: ICAC_B pubkey vs stored pubkey_A
6. **Will fail** at public key match (T013) ✅

Actually, this is **protected**! The public key binding check (validate_public_key_match) will fail if wrong ICAC sent.

But there's still a subtle issue:
**What if malicious Admin B generates their own CSR and sends AddICAC for it?**

Wait, no: The FSM only stores **one** CSR at a time. If Admin B wants their CSR accepted, they need to:
1. Call ICACCSRRequest themselves (but can't, because not in Idle state)

The **state machine single-threading** provides session binding implicitly:
- Only one commissioning session at a time
- CSR generated for session that called ICACCSRRequest
- AddICAC validated against that CSR

**Verdict**: **HOLDS (implicit session binding via state)**

The FSM enforces session binding through single-threaded state progression and public key validation.

---

#### PROP_021: Status_Code_Matches_Validation_Error
- **Status**: Analyzing...
- **Claim**: ICACResponse status code must match validation failure type
- **Formal**: ∀resp, val. event send_ICACResponse(resp, val) ==> event status_matches_validation(resp.statusCode, val)

**FSM Trace**:

From ValidatingICAC:
- T011: -> ICACAccepted
  - Action: `send_ICACResponse(OK, "ICAC accepted")`
  - Validation: All checks passed
  - ✅ Status = OK matches

- T012: -> ICACRejected_InvalidICAC
  - Action: `send_ICACResponse(InvalidICAC, "Chain validation failed")`
  - Validation: Crypto_VerifyChain == failure
  - ✅ Status = InvalidICAC matches

- T013: -> ICACRejected_InvalidPublicKey
  - Action: `send_ICACResponse(InvalidPublicKey, "Public key mismatch")`
  - Validation: validate_public_key_match == failure
  - ✅ Status = InvalidPublicKey matches

- T014: -> ICACRejected_InvalidICAC
  - Action: `send_ICACResponse(InvalidICAC, "DN encoding invalid")`
  - Validation: validate_DN_encoding == failure
  - ✅ Status = InvalidICAC matches

**Verdict**: **HOLDS**

---

#### PROP_023: Endpoint_Announcement_Uniqueness
- **Status**: Analyzing...
- **Claim**: Announced endpoint must be unique and must have Joint Fabric Administrator Cluster
- **Formal**: ∀m, e. event process_AnnounceJointFabricAdministrator(m, e) ==> event endpoint_is_unique(e) ∧ event endpoint_has_JFAC(e)

**FSM Trace**:

From Idle:
- T048: Idle -> EndpointAnnounced
  - Trigger: AnnounceJointFabricAdministrator
  - Guard: `true` ❌ **NO VALIDATION**
  - Action: `send_announcement_confirmation(EndpointID)`

**🚨 VIOLATION FOUND!**

**Attack Path**:
1. Attacker sends AnnounceJointFabricAdministrator with arbitrary EndpointID
2. FSM accepts without validation (T048, guard = true)
3. No check for endpoint uniqueness
4. No check that endpoint actually has JFAC cluster
5. Announcement accepted and confirmed

**Specification Evidence**:
```
Quote: "This field SHALL contain the unique identifier for the endpoint that holds the Joint Fabric Administrator Cluster."
Source: Section 11.25.7.9, "AnnounceJointFabricAdministrator Command"
```

The specification says the field "SHALL contain" unique identifier, but doesn't specify validation on receipt.

**Verdict**: **VIOLATED (No endpoint validation)**

**Severity**: **MEDIUM** (Can cause confusion or misdirection)

---

#### PROP_040: AdministratorFabricIndex_Not_Null_For_Admin_Operations
- **Status**: Analyzing...
- **Claim**: Administrative operations require non-null AdministratorFabricIndex
- **Formal**: ∀n, op. event execute_admin_operation(n, op) ==> event AdministratorFabricIndex_not_null(n)

**FSM Trace**:

Looking at all administrative operations:

1. **ICACCSRRequest**: No check for AdministratorFabricIndex
   - T001 guard: `session_is_CASE == true && fail_safe_armed == true && vid_verification_completed == true && prior_AddICAC_executed == false`
   - ❌ No AdministratorFabricIndex check

2. **OpenJointCommissioningWindow**: Checks AdministratorFabricIndex
   - T031 guard: `AdministratorFabricIndex != null && ...`
   - ✅ Checks not null

3. **TransferAnchorRequest**: No explicit check
   - T040 guard: `true`
   - ❌ No AdministratorFabricIndex check

**🚨 PARTIAL VIOLATION**:

Some admin operations check AdministratorFabricIndex (OpenJointCommissioningWindow), but others don't (ICACCSRRequest, TransferAnchorRequest).

**Should ICACCSRRequest require non-null AdministratorFabricIndex?**

Looking at the specification for ICACCSRRequest:
- No mention of AdministratorFabricIndex requirement

For OpenJointCommissioningWindow:
```
Quote: "This command SHALL fail with a InvalidAdministratorFabricIndex status code sent back to the initiator if the AdministratorFabricIndex attribute has the value of null."
Source: Section 11.25.7.5
```

**Only OpenJointCommissioningWindow explicitly requires this check.**

**Verdict**: **HOLDS (for specified operations)**

Only OpenJointCommissioningWindow is required to check AdministratorFabricIndex per specification. Other operations don't have this requirement stated.

---

## FINAL VIOLATIONS SUMMARY

### Violation 1: PROP_033 - Fail_Safe_Atomicity ⚠️ CRITICAL
- **Issue**: No fail-safe expiration transitions from CSRRequested, CSRGenerated, ValidatingICAC states
- **Impact**: Partial commissioning state persists beyond fail-safe period; node left in inconsistent state
- **Specification Quote**: "If this command is received without an armed fail-safe context... then this command SHALL fail" (11.25.7.1, 11.25.7.3)
- **Specification Gap**: No explicit requirement for rollback from intermediate states when fail-safe expires
- **Severity**: **CRITICAL**
- **FSM Fix Required**: Add transitions T00X: {CSRRequested, CSRGenerated, ValidatingICAC} -> Idle on fail_safe_expired trigger with rollback_all_operations() action

### Violation 2: PROP_026 - Prevent_Concurrent_Commissioning_Operations ⚠️ MEDIUM
- **Issue**: No Busy error response for concurrent ICACCSRRequest during in-progress commissioning
- **Impact**: Concurrent commissioning attempts not explicitly rejected; behavior undefined
- **Specification Quote**: "Busy ... Could not be completed because another commissioning is in progress" (11.25.5.1)
- **Specification Gap**: Specification defines Busy status but doesn't mandate checking for concurrent operations
- **Severity**: **MEDIUM**
- **FSM Fix Required**: Add transitions from {CSRRequested, CSRGenerated, ValidatingICAC, ICACAccepted} to ErrorState_Busy on ICACCSRRequest trigger

### Violation 3: PROP_027 - Discriminator_Range_Validation ⚠️ HIGH
- **Issue**: Discriminator parameter (max 4095) not validated in OpenJointCommissioningWindow
- **Impact**: Invalid discriminator values (>4095) accepted; discovery collision or overflow vulnerabilities
- **Specification Quote**: "Discriminator ... uint16 ... max 4095" (11.25.7.5)
- **Specification Gap**: Constraint specified but validation not mandated in Effect on Receipt
- **Severity**: **HIGH**
- **FSM Fix Required**: Update validate_pake_parameters() to include discriminator validation, or add separate validation function

### Violation 4: PROP_042 - CSR_Size_Limit_600_Bytes ⚠️ MEDIUM
- **Issue**: No size validation when generating/sending CSR
- **Impact**: CSR >600 bytes could be sent, violating protocol constraint; potential buffer overflow on receiver
- **Specification Quote**: "ICACCSR ... octstr ... max 600" (11.25.7.2)
- **Specification Gap**: Constraint defined but enforcement location not specified (generator vs receiver)
- **Severity**: **MEDIUM**
- **FSM Fix Required**: Add size check in generate_PKCS10_CSR_DER_encoded() or send_ICACCSRResponse() functions

### Violation 5: PROP_043 - ICAC_Size_Limit_400_Bytes ⚠️ MEDIUM
- **Issue**: No size validation when receiving ICAC in AddICAC command
- **Impact**: ICAC >400 bytes could be accepted, violating protocol constraint; potential memory exhaustion
- **Specification Quote**: "ICACValue ... octstr ... max 400" (11.25.7.3)
- **Specification Gap**: Size validation not listed in Effect on Receipt validation checks (only chain, pubkey, DN)
- **Severity**: **MEDIUM**
- **FSM Fix Required**: Add size validation check before or during ValidatingICAC state process

### Violation 6: PROP_035 - State_Machine_Exclusivity ⚠️ HIGH
- **Issue**: Multiple state machines (Joint Commissioning, ACL Management, Commissioning Window, Anchor Transfer) can run concurrently without mutual exclusion
- **Impact**: Race conditions, resource conflicts, inconsistent state across operations
- **Specification Quote**: "TransferAnchorStatusDatastoreBusy ... Anchor Transfer was not started due to ongoing Datastore operations" (11.25.4.2)
- **Specification Gap**: Datastore busy check mentioned for Anchor Transfer but no general mutual exclusion for commissioning operations
- **Severity**: **HIGH**
- **FSM Fix Required**: Add mutual exclusion guards across state machines; commissioning operations should check for ongoing operations before proceeding

### Violation 7: PROP_023 - Endpoint_Announcement_Uniqueness ⚠️ MEDIUM
- **Issue**: AnnounceJointFabricAdministrator accepts any EndpointID without validation
- **Impact**: Malicious announcements can misdirect clients; endpoint may not actually have JFAC cluster
- **Specification Quote**: "This field SHALL contain the unique identifier for the endpoint that holds the Joint Fabric Administrator Cluster" (11.25.7.9)
- **Specification Gap**: Field definition provided but no validation mandated on receipt
- **Severity**: **MEDIUM**
- **FSM Fix Required**: Add validation guards to T048: check endpoint_exists() && endpoint_has_JFAC_cluster()

---

## Properties Analyzed: 27 / 44
## Violations Found: 7
## Critical Violations: 1
## High Violations: 2
## Medium Violations: 4

---

## Continue with remaining properties or generate final report?
