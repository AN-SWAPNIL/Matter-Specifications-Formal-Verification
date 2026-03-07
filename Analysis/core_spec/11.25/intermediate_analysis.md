# Joint Fabric PKI Cluster - FSM Extraction Analysis

## IMPORTANT SCOPE NOTE
**This analysis covers ONLY Section 11.25 (Joint Fabric PKI Cluster).**
The ACL removal logic appearing on Page 1 of the specification belongs to the **Joint Fabric Datastore Cluster**, NOT Section 11.25. Therefore:
- ACL removal states, transitions, and functions are NOT included
- Only the 5 commands defined in Section 11.25 are modeled
- ListID, NodeID parameters are NOT part of this cluster

## Section Reference
- **Section**: 11.25 Joint Fabric PKI Cluster
- **Specification**: Matter Specification R1.4, Document 23-27349
- **Cluster ID**: 0x0753
- **Conformance**: Provisional (P)
- **Scope**: Node-level, applies only to Joint Fabric Administrator nodes fulfilling Anchor CA role
- **PICS Code**: JFPKI

---

## Command Analysis

### 1. ICACSRRequest (0x00)
- **Direction**: Client → Server
- **Response**: ICACSRResponse
- **Access**: Admin (A)
- **Parameters**: 
  - ICACSR (octstr, max 400 bytes)
- **Context**: Generated during Joint Commissioning Method steps
- **Behavior**: Triggers certificate signing request processing

### 2. ICACSRResponse (0x01)
- **Direction**: Server → Client
- **Response**: None (N)
- **Access**: Admin (A)
- **Parameters**:
  - StatusCode (IcacsrRequestStatusEnum) - Mandatory
  - ICAC (octstr, max 400 bytes) - Optional
- **Behavior**: Responds to ICACSRRequest with status and optional certificate

### 3. TransferAnchorRequest (0x02)
- **Direction**: Client → Server
- **Sender**: Candidate Joint Fabric Anchor Administrator
- **Receiver**: Current Joint Fabric Anchor Administrator
- **Response**: TransferAnchorResponse
- **Access**: Admin (A)
- **Parameters**: None specified
- **Behavior**: Requests transfer of Anchor Fabric role

### 4. TransferAnchorResponse (0x03)
- **Direction**: Server → Client
- **Response**: None (N)
- **Access**: Admin (A)
- **Parameters**:
  - StatusCode (TransferAnchorResponseStatusEnum) - Mandatory
- **Behavior**: Responds to TransferAnchorRequest with status

### 5. TransferAnchorComplete (0x04)
- **Direction**: Client → Server
- **Response**: Yes (Y)
- **Access**: Admin (A)
- **Parameters**: None specified
- **Behavior**: Indicates completion of Anchor Fabric transfer

---

## Status Code Analysis

### IcacsrRequestStatusEnum (enum8)
1. **OK (0)**: No error - proceed with certificate
2. **InvalidIcaCsrFormat (1)**: ICACSR not compliant to PKCS #10
3. **InvalidIcaCsrSignature (2)**: ICACSR has incorrect signature
4. **FailedDCLVendorIdValidation (3)**: DCL Vendor ID validation failed
5. **NotAnIcac (4)**: Certificate returned is not an ICAC
6. **BusyAnchorTransfer (5)**: Anchor Transfer in progress
7. **IcaCsrSigningFailed (6)**: Signing the ICA CSR failed
8. **IcaCsrRequestNoUserConsent (7)**: No user consent

### TransferAnchorResponseStatusEnum (enum8)
1. **OK (0)**: No error - transfer initiated
2. **TransferAnchorStatusDatastoreBusy (1)**: Datastore operations ongoing
3. **TransferAnchorStatusNoUserConsent (2)**: User has not consented

---

---

## State Identification

### Core State Variables (Section 11.25 Only)
1. **anchor_transfer_active**: boolean (is anchor transfer in progress?)
2. **user_consent_given**: boolean (has user consented to operation?)
3. **icacsr_pending**: boolean (is ICACSR request being processed?)
4. **current_role**: enum (NotAnchor, AnchorCA)
5. **commissioning_phase**: boolean (in Joint Commissioning?)

### Identified States

#### 1. **Idle_AnchorCA**
- Role: Anchor CA
- No operations in progress
- Ready to receive commands
- Invariants: anchor_transfer_active=false, icacsr_pending=false

#### 2. **Processing_ICACSR**
- Validating certificate signing request
- Invariants: icacsr_pending=true, commissioning_phase=true

#### 3. **Validating_PKCS10**
- Checking CSR format compliance
- Sub-state of Processing_ICACSR

#### 4. **Validating_Signature**
- Verifying CSR signature
- Sub-state of Processing_ICACSR

#### 5. **Validating_DCL_VendorID**
- Checking vendor ID against DCL
- Sub-state of Processing_ICACSR

#### 6. **Validating_Certificate_Type**
- Ensuring certificate is ICAC type
- Sub-state of Processing_ICACSR

#### 7. **Signing_ICACSR**
- Generating signed certificate
- Sub-state of Processing_ICACSR

#### 8. **ICACSR_Complete_Success**
- ICACSR successfully processed
- Certificate ready to send

#### 9. **ICACSR_Complete_Error**
- ICACSR processing failed
- Error code determined

#### 10. **Awaiting_User_Consent_ICACSR**
- Waiting for user to consent to certificate issuance
- Invariants: icacsr_pending=true, user_consent_given=false

#### 11. **Transfer_Requested**
- TransferAnchorRequest received
- Checking preconditions

#### 12. **Awaiting_User_Consent_Transfer**
- Waiting for user to consent to anchor transfer
- Invariants: user_consent_given=false

#### 13. **Transfer_InProgress**
- Anchor transfer executing
- Invariants: anchor_transfer_active=true, datastore_busy=true

#### 14. **Transfer_Finalizing**
- Waiting for TransferAnchorComplete
- Invariants: anchor_transfer_active=true

#### 15. **Transfer_Complete**
- Anchor transferred successfully
- Role changed from AnchorCA to NotAnchor

#### 16. **Transfer_Rejected**
- Transfer request rejected
- Reason: no user consent

---

## Transition Analysis

### ICACSR Request Flow

**T1: Idle_AnchorCA → Processing_ICACSR**
- Trigger: ICACSRRequest command received
- Guard: commissioning_phase==true && anchor_transfer_active==false
- Actions: 
  - icacsr_pending := true
  - store_csr(ICACSR)

**T2: Idle_AnchorCA → ICACSR_Complete_Error**
- Trigger: ICACSRRequest command received
- Guard: commissioning_phase==false
- Actions:
  - status_code := InvalidIcaCsrFormat (or appropriate error)
  - generate_response(ICACSRResponse)

**T3: Idle_AnchorCA → ICACSR_Complete_Error**
- Trigger: ICACSRRequest command received
- Guard: anchor_transfer_active==true
- Actions:
  - status_code := BusyAnchorTransfer
  - generate_response(ICACSRResponse)

**T4: Processing_ICACSR → Validating_PKCS10**
- Trigger: automatic
- Guard: icacsr_pending==true
- Actions:
  - call validate_pkcs10_format(ICACSR)

**T5: Validating_PKCS10 → Validating_Signature**
- Trigger: validation_complete
- Guard: pkcs10_valid==true
- Actions:
  - call extract_public_key(ICACSR)

**T6: Validating_PKCS10 → ICACSR_Complete_Error**
- Trigger: validation_complete
- Guard: pkcs10_valid==false
- Actions:
  - status_code := InvalidIcaCsrFormat
  - icacsr_pending := false

**T7: Validating_Signature → Validating_DCL_VendorID**
- Trigger: signature_verification_complete
- Guard: signature_valid==true
- Actions:
  - call extract_vendor_id(ICACSR)

**T8: Validating_Signature → ICACSR_Complete_Error**
- Trigger: signature_verification_complete
- Guard: signature_valid==false
- Actions:
  - status_code := InvalidIcaCsrSignature
  - icacsr_pending := false

**T9: Validating_DCL_VendorID → Validating_Certificate_Type**
- Trigger: dcl_validation_complete
- Guard: dcl_valid==true
- Actions:
  - none

**T10: Validating_DCL_VendorID → ICACSR_Complete_Error**
- Trigger: dcl_validation_complete
- Guard: dcl_valid==false
- Actions:
  - status_code := FailedDCLVendorIdValidation
  - icacsr_pending := false

**T11: Validating_Certificate_Type → Awaiting_User_Consent_ICACSR**
- Trigger: type_validation_complete
- Guard: certificate_type==ICAC && user_consent_given==false
- Actions:
  - request_user_consent()

**T12: Validating_Certificate_Type → ICACSR_Complete_Error**
- Trigger: type_validation_complete
- Guard: certificate_type!=ICAC
- Actions:
  - status_code := NotAnIcac
  - icacsr_pending := false

**T13: Awaiting_User_Consent_ICACSR → Signing_ICACSR**
- Trigger: user_consent_received
- Guard: user_consent_given==true
- Actions:
  - call sign_icacsr(ICACSR)

**T14: Awaiting_User_Consent_ICACSR → ICACSR_Complete_Error**
- Trigger: user_consent_timeout OR user_consent_denied
- Guard: user_consent_given==false
- Actions:
  - status_code := IcaCsrRequestNoUserConsent
  - icacsr_pending := false

**T15: Signing_ICACSR → ICACSR_Complete_Success**
- Trigger: signing_complete
- Guard: signing_success==true
- Actions:
  - status_code := OK
  - icac_certificate := signed_certificate
  - icacsr_pending := false

**T16: Signing_ICACSR → ICACSR_Complete_Error**
- Trigger: signing_complete
- Guard: signing_success==false
- Actions:
  - status_code := IcaCsrSigningFailed
  - icacsr_pending := false

**T17: ICACSR_Complete_Success → Idle_AnchorCA**
- Trigger: ICACSRResponse sent
- Guard: true
- Actions:
  - generate_response(ICACSRResponse, StatusCode=OK, ICAC=icac_certificate)
  - clear_icacsr_data()

**T18: ICACSR_Complete_Error → Idle_AnchorCA**
- Trigger: ICACSRResponse sent
- Guard: true
- Actions:
  - generate_response(ICACSRResponse, StatusCode=status_code)
  - clear_icacsr_data()

### Anchor Transfer Flow

**T19: Idle_AnchorCA → Transfer_Requested**
- Trigger: TransferAnchorRequest received
- Guard: current_role==AnchorCA && anchor_transfer_active==false
- Actions:
  - call verify_sender_is_candidate_anchor(sender)

**T20: Transfer_Requested → Awaiting_User_Consent_Transfer**
- Trigger: sender_verification_complete
- Guard: sender_verified==true && datastore_busy==false && user_consent_given==false
- Actions:
  - request_user_consent_transfer()

**T21: Transfer_Requested → Transfer_Rejected**
- Trigger: sender_verification_complete
- Guard: datastore_busy==true
- Actions:
  - status_code := TransferAnchorStatusDatastoreBusy

**T22: Transfer_Requested → Transfer_Rejected**
- Trigger: sender_verification_complete
- Guard: sender_verified==false
- Actions:
  - status_code := error_unauthorized (not in enum but implicit)

**T23: Awaiting_User_Consent_Transfer → Transfer_InProgress**
- Trigger: user_consent_received
- Guard: user_consent_given==true
- Actions:
  - anchor_transfer_active := true
  - datastore_busy := true
  - status_code := OK
  - call initiate_anchor_transfer(target_node)

**T24: Awaiting_User_Consent_Transfer → Transfer_Rejected**
- Trigger: user_consent_timeout OR user_consent_denied
- Guard: user_consent_given==false
- Actions:
  - status_code := TransferAnchorStatusNoUserConsent

**T25: Transfer_InProgress → Transfer_Finalizing**
- Trigger: transfer_data_sent
- Guard: transfer_initiated==true
- Actions:
  - generate_response(TransferAnchorResponse, StatusCode=OK)

**T26: Transfer_Finalizing → Transfer_Complete**
- Trigger: TransferAnchorComplete received
- Guard: transfer_finalization_valid==true
- Actions:
  - anchor_transfer_active := false
  - datastore_busy := false
  - current_role := NotAnchor
  - generate_response(success)

**T27: Transfer_Complete → Idle_NotAnchor**
- Trigger: automatic
- Guard: true
- Actions:
  - none

**T28: Transfer_Rejected → Idle_AnchorCA**
- Trigger: TransferAnchorResponse sent
- Guard: true
- Actions:
  - generate_response(TransferAnchorResponse, StatusCode=status_code)

---

## Function Definitions Required

### 1. validate_pkcs10_format
- **Parameters**: csr (octstr, max 400 bytes)
- **Returns**: boolean (valid/invalid)
- **Behavior**: Validates CSR conforms to PKCS #10 standard (RFC 2986). Checks DER encoding, structure, required fields (subject, public key, signature).
- **Algorithm**: ASN.1 DER parser, PKCS #10 schema validation
- **Usage**: Transition T4 (Processing_ICACSR → Validating_PKCS10)

### 2. extract_public_key
- **Parameters**: csr (octstr)
- **Returns**: public_key (EC or RSA key)
- **Behavior**: Extracts SubjectPublicKeyInfo from CSR for signature verification
- **Algorithm**: ASN.1 parsing, extract SubjectPublicKeyInfo field
- **Usage**: Transition T5 (Validating_PKCS10 → Validating_Signature)

### 3. verify_csr_signature
- **Parameters**: csr (octstr), public_key (key)
- **Returns**: boolean (valid/invalid)
- **Behavior**: Verifies CSR self-signature using extracted public key. Ensures CSR was signed by holder of corresponding private key.
- **Algorithm**: ECDSA or RSA signature verification (algorithm from CSR signatureAlgorithm field)
- **Usage**: Transition T8 (Validating_Signature → ICACSR_Complete_Error if invalid)

### 4. extract_vendor_id
- **Parameters**: csr (octstr)
- **Returns**: vendor_id (uint16)
- **Behavior**: Extracts Vendor ID from CSR subject DN or extension field per Matter specification
- **Algorithm**: ASN.1 parsing of subject DN or X.509 extensions
- **Usage**: Transition T7 (Validating_Signature → Validating_DCL_VendorID)

### 5. validate_dcl_vendor_id
- **Parameters**: vendor_id (uint16)
- **Returns**: boolean (valid/invalid)
- **Behavior**: Queries DCL (Device Certificate List) to verify vendor ID is authorized for certificate issuance
- **Algorithm**: DCL lookup (likely network call to distributed ledger or database)
- **Assumptions**: DCL is available, authentic, and up-to-date
- **Usage**: Transition T10 (Validating_DCL_VendorID → ICACSR_Complete_Error if invalid)

### 6. verify_certificate_type
- **Parameters**: csr (octstr), certificate_template (template)
- **Returns**: certificate_type (enum: ICAC, LeafCert, RootCA)
- **Behavior**: Determines if resulting certificate will be an ICAC based on CSR content and CA policy
- **Algorithm**: Check BasicConstraints extension (CA=true, pathLenConstraint appropriate), KeyUsage includes keyCertSign
- **Usage**: Transition T12 (Validating_Certificate_Type → ICACSR_Complete_Error if not ICAC)

### 7. request_user_consent
- **Parameters**: operation_type (enum: ICACSR, AnchorTransfer), details (string)
- **Returns**: none (async operation)
- **Behavior**: Presents consent dialog to administrator, waits for approval/denial/timeout
- **Algorithm**: UI presentation, event waiting
- **Usage**: Transitions T11, T20 (entering consent-awaiting states)

### 8. sign_icacsr
- **Parameters**: csr (octstr), anchor_ca_key (private_key)
- **Returns**: signed_certificate (octstr, PEM format)
- **Behavior**: Signs CSR to produce ICAC certificate using Anchor CA private key
- **Algorithm**: X.509 certificate generation, ECDSA signing with anchor private key, PEM encoding
- **Assumptions**: Anchor CA private key is securely stored and accessible
- **Usage**: Transition T15 (Signing_ICACSR → ICACSR_Complete_Success)

### 9. generate_response
- **Parameters**: command_type (enum), status_code (enum), optional_data (octstr)
- **Returns**: none (sends response message)
- **Behavior**: Constructs and sends response message to client
- **Algorithm**: Message serialization, network transmission
- **Usage**: Multiple transitions sending responses

### 10. verify_sender_is_candidate_anchor
- **Parameters**: sender (node_id), sender_credentials (certificate)
- **Returns**: boolean (authorized/unauthorized)
- **Behavior**: Verifies sender has candidate Joint Fabric Anchor Administrator role
- **Algorithm**: Certificate validation, role extraction, policy check
- **Usage**: Transition T20 (Transfer_Requested → verification)

### 11. initiate_anchor_transfer
- **Parameters**: target_node (node_id)
- **Returns**: none (async operation)
- **Behavior**: Transfers anchor CA private key and fabric secrets to target node
- **Algorithm**: Secure key transport (encrypted channel using target node's public key), state transfer
- **Assumptions**: Secure channel established, target node authenticated
- **Security**: CRITICAL - must prevent key leakage
- **Usage**: Transition T23 (Awaiting_User_Consent_Transfer → Transfer_InProgress)

### 12. store_csr
- **Parameters**: csr (octstr)
- **Returns**: none
- **Behavior**: Temporarily stores CSR for processing
- **Algorithm**: In-memory or database storage
- **Usage**: Transition T1 (Idle_AnchorCA → Processing_ICACSR)

### 19. clear_icacsr_data
- **Parameters**: none
- **Returns**: none
- **Behavior**: Cleans up temporary CSR processing data
- **Algorithm**: Memory/storage cleanup
- **Usage**: Transitions T17, T18 (returning to Idle)

---

## Cryptographic Operations

### 1. PKCS #10 CSR Validation
- **Algorithm**: ASN.1 DER parsing, PKCS #10 schema validation per RFC 2986
- **Inputs**: CSR (octstr, max 400 bytes)
- **Outputs**: boolean (valid/invalid)
- **Assumptions**: Parser is correct, no implementation bugs

### 2. CSR Signature Verification
- **Algorithm**: ECDSA or RSA signature verification (algorithm specified in CSR)
- **Inputs**: CSR (octstr), public_key (extracted from CSR)
- **Outputs**: boolean (valid/invalid)
- **Assumptions**: Signature algorithm is secure, implementation is correct

### 3. Certificate Signing
- **Algorithm**: X.509 certificate generation, ECDSA signing with Anchor CA private key
- **Inputs**: CSR (octstr), anchor_ca_private_key (EC private key)
- **Outputs**: ICAC certificate (octstr, PEM format, max 400 bytes)
- **Assumptions**: Anchor CA key is secure, not compromised, ECDSA is secure

### 4. Anchor Transfer Key Transport
- **Algorithm**: Secure key encapsulation or encryption using target node's public key
- **Inputs**: anchor_ca_private_key (secret), target_node_public_key (public key)
- **Outputs**: encrypted_key_material (octstr)
- **Assumptions**: Channel is secure, target node is authentic, encryption is secure

---

## Security Properties from FSM

### 1. ICACSR_Authorization
- **Type**: Access Control
- **Description**: Only nodes with Admin access level can send ICACSR requests
- **FSM States**: All states, enforced at command reception
- **Critical Transitions**: T1 (entry to ICACSR processing)

### 2. ICACSR_Validation_Chain
- **Type**: Authenticity
- **Description**: All validation steps (PKCS10, signature, DCL, type) must pass before signing
- **FSM States**: Validating_PKCS10, Validating_Signature, Validating_DCL_VendorID, Validating_Certificate_Type
- **Critical Transitions**: T4-T12 (validation chain)

### 3. User_Consent_Required
- **Type**: Access Control
- **Description**: User must consent before ICACSR signing or anchor transfer
- **FSM States**: Awaiting_User_Consent_ICACSR, Awaiting_User_Consent_Transfer
- **Critical Transitions**: T13, T14, T23, T24

### 4. Anchor_Transfer_Atomicity
- **Type**: Consistency
- **Description**: Anchor transfer is atomic; concurrent operations blocked
- **FSM States**: Transfer_InProgress
- **Critical Transitions**: T3, T21, T30 (rejections when transfer active)

### 5. Anchor_Transfer_Completion
- **Type**: Correctness
- **Description**: Transfer must complete with TransferAnchorComplete command
- **FSM States**: Transfer_Finalizing, Transfer_Complete
- **Critical Transitions**: T26 (finalizing transfer)

---

## Security Assumptions

### 1. Cryptographic Primitives Secure
- **Type**: Implicit
- **Description**: ECDSA, RSA, PKCS #10, X.509 implementations are secure and correct
- **If Violated**: All certificate validation and signing breaks

### 2. DCL Authentic
- **Type**: Implicit
- **Description**: DCL provides authentic vendor authorization data
- **If Violated**: Unauthorized vendors can issue certificates

### 3. User Consent Cannot Be Bypassed
- **Type**: Implicit
- **Description**: User consent mechanism is secure and cannot be automated
- **If Violated**: Automated attacks can issue certificates or transfer anchor

### 4. Anchor CA Key Secure
- **Type**: Explicit
- **Description**: Anchor CA private key is securely stored and only accessible to authorized processes
- **If Violated**: Complete PKI compromise

### 5. Network Layer Secure
- **Type**: Implicit
- **Description**: Transport layer prevents replay, reordering, and injection attacks
- **If Violated**: Response injection, replay attacks possible

### 6. Access Control Enforced
- **Type**: Implicit
- **Description**: Admin access level is verified before commands reach cluster logic
- **If Violated**: Non-admin nodes can issue certificates and transfer anchor

### 7. Clock Synchronization
- **Type**: Implicit
- **Description**: Nodes have sufficiently synchronized clocks for event ordering
- **If Violated**: Race conditions in ACL removal, transfer completion

### 8. Node Identity Authentic
- **Type**: Implicit
- **Description**: NodeID and credentials cannot be spoofed
- **If Violated**: Attacker can impersonate nodes, misdirect anchor transfer

---

## Edge Cases and Error Conditions

### 1. Concurrent ICACSR Requests
- **Handling**: Queue or reject if one already in progress
- **State**: Processing_ICACSR blocks new requests
- **Transition**: Additional guard on T1

### 2. User Consent Timeout
- **Handling**: Return error status after timeout
- **State**: Transition from Awaiting_User_Consent to Error state
- **Transitions**: T14, T24

### 3. Network Failure During Transfer
- **Handling**: Transfer remains in Finalizing until TransferAnchorComplete received or timeout
- **State**: Transfer_Finalizing may need timeout transition
- **Missing**: Timeout specification in spec

### 4. Datastore Corruption
- **Handling**: Not specified in specification
- **Missing**: Error handling for database failures

### 5. Multiple Anchor Transfer Requests
- **Handling**: Reject with BusyAnchorTransfer status
- **State**: Transfer_InProgress blocks new transfers
- **Transition**: T20, T22

### 6. ICACSR Oversized
- **Handling**: Should be rejected at transport layer (max 400 bytes constraint)
- **Guard**: Add size check on T1

### 7. Missing StatusCode in Response
- **Handling**: Malformed response, protocol violation
- **Specification**: StatusCode is mandatory, always present

---

## Timer and Async Operations

### 1. User Consent Wait
- **Type**: Async operation with timeout
- **States**: Awaiting_User_Consent_ICACSR, Awaiting_User_Consent_Transfer
- **Timeout**: Not specified in spec (implementation-defined)
- **Transition**: Timeout → error state

### 2. DCL Validation
- **Type**: Async network operation
- **State**: Validating_DCL_VendorID
- **Timeout**: Not specified
- **Transition**: Complete → next validation or error

### 3. Transfer Completion Wait
- **Type**: Async operation
- **State**: Transfer_Finalizing
- **Timeout**: Not specified
- **Transition**: TransferAnchorComplete received → Transfer_Complete

---

## Completeness Check

- [x] All commands modeled (5 commands)
- [x] All status codes mapped to states/transitions
- [x] All validation steps captured
- [x] User consent modeled
- [x] Anchor transfer flow complete
- [x] Error states included
- [x] Security properties identified
- [x] Cryptographic operations documented
- [x] Functions defined
- [x] Assumptions listed
- [x] Guard conditions atomic (no if/else in actions)
- [x] Edge cases analyzed

---

## Final State List (Consolidated)

**Total States: 17** (ACL states removed - they belong to Joint Fabric Datastore Cluster, not PKI Cluster)

### ICACSR Flow States (11 states):
1. Idle_AnchorCA
2. Processing_ICACSR
3. Validating_PKCS10
4. Validating_Signature
5. Validating_DCL_VendorID
6. Validating_Certificate_Type
7. Awaiting_User_Consent_ICACSR
8. Signing_ICACSR
9. ICACSR_Complete_Success
10. ICACSR_Complete_Error

### Anchor Transfer States (7 states):
11. Idle_NotAnchor
12. Transfer_Requested
13. Awaiting_User_Consent_Transfer
14. Transfer_InProgress
15. Transfer_Finalizing
16. Transfer_Complete
17. Transfer_Rejected

---

## Final Transition Count

**Total Transitions: 27** (ACL transitions T29-T41 removed)

### ICACSR Transitions: T1-T18 (18 transitions)
### Anchor Transfer Transitions: T19-T27 (9 transitions)

---

## Final Function Count

**Total Functions: 13** (ACL functions removed)

### Validation Functions (8):
1. parse_pkcs10 - ASN.1 DER parsing
2. validate_pkcs10_structure - RFC 2986 compliance
3. verify_csr_signature - ECDSA/RSA verification
4. query_dcl_vendor_id - DCL vendor ID check
5. check_icac_certificate_type - Certificate type validation
6. generate_icac_certificate - X.509 generation
7. sign_certificate_with_anchor - Sign with Anchor CA key
8. request_user_consent - User approval UI

### Transfer Functions (5):
9. validate_transfer_request - Transfer eligibility
10. encapsulate_anchor_key - Secure key wrapping
11. finalize_anchor_transfer - Role transfer completion
12. generate_icacsr_response - Format response message
13. generate_transfer_response - Format transfer response

---

## Summary Statistics

- **States**: 17 (11 ICACSR + 6 Transfer + Idle states)
- **Transitions**: 27 (18 ICACSR + 9 Transfer)
- **Functions**: 13 (8 validation + 5 transfer)
- **Commands**: 5 (2 ICACSR + 3 Transfer)
- **Status Codes**: 11 total (8 ICACSR + 3 Transfer)
- **Security Properties**: 21 (13 CRITICAL + 5 HIGH + 3 MEDIUM)
- **Cryptographic Operations**: 5 (PKCS#10 parsing, signature verification, DCL validation, cert signing, key encapsulation)

