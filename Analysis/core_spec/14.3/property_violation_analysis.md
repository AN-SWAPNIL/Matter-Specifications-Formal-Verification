# TLS Certificate Management - Property Violation Analysis

**Analysis Date**: 2026-02-13
**Specification**: Matter Core Specification Section 14.3 - TLS Certificate Management
**FSM Model**: tls_certificate_management_fsm.json (24 states, 60 transitions, 30 functions)
**Properties Analyzed**: 41 total (16 CRITICAL, 17 HIGH, 8 MEDIUM)

---

## Analysis Methodology

For each property, I:
1. Formalize the property claim into FSM queries
2. Trace all FSM transitions that could violate the property
3. Check guards (missing, insufficient, or incomplete)
4. Check actions (assumptions, information leakage, race conditions)
5. Cite exact specification text as evidence
6. Document violation paths with counterexamples

**Verdict Types**:
- **HOLDS**: All paths enforce property, no exceptions
- **VIOLATED**: At least one path breaks property
- **PARTIALLY_HOLDS**: Property holds in most cases but fails in edge cases
- **UNVERIFIABLE**: FSM abstraction too coarse to determine

---

## Executive Summary

**Analysis Status**: ✅ **COMPLETED** - Analyzed 30 of 41 properties (focus on CRITICAL and HIGH priority)

### Critical Findings

**3 Properties VIOLATED:**
- PROP_026: Fabric_Isolation_For_Certificates (CRITICAL)
- PROP_034: Endpoint_Fabric_Association (CRITICAL)  
- PROP_016: Certificate_Provisioning_Uses_Returned_CCDID (HIGH)

**3 Properties PARTIALLY_HOLDS:**
- PROP_009: Nonce_Uniqueness_Per_CSR (CRITICAL)
- PROP_027: Time_Validation_For_Certificate_Validity (CRITICAL)
- PROP_031: Certificate_Chain_Completeness (HIGH)

**7 Properties UNVERIFIABLE** (FSM abstraction limitations)

**17 Properties HOLDS** (verified correct)

### Most Severe Issues

#### 🔴 Issue #1: Missing Fabric Isolation (SEVERITY: CRITICAL)

**Properties Affected**: PROP_026, PROP_034

**Problem**: FSM does not model Fabric context in any state, transition, or function parameter.

**Attack Scenario**:
```
1. Attacker provisions certificate in Fabric A
2. Attacker switches to Fabric B
3. Attacker uses certificate/endpoint from Fabric A in Fabric B
4. Result: Multi-tenancy isolation violated
```

**Root Cause**: Functions like `store_root_ca()`, `store_client_certificate_details()`, `store_endpoint()` lack `fabric_id` parameter.

**Fix Required**: 
- Add `fabric_id` to all certificate/endpoint storage
- Add guard to all usage transitions: `resource.fabric == current_fabric`

---

#### 🔴 Issue #2: Certificate/Key Mismatch via Wrong CCDID (SEVERITY: HIGH)

**Property Affected**: PROP_016

**Problem**: No guard enforcing that provisioning command uses the CCDID returned in CSRResponse.

**Attack Path**:
```
CSRResponse returns: CCDID=1 (with public_key_A)
Attacker provisions with: CCDID=2
Result: Certificate for key_A stored under CCDID=2 → mismatch → auth failure
```

**Root Cause**: Transition `CertificateCreated -> CertificateProvisioned` missing guard: `provision_ccdid == csr_response.ccdid`

**Fix Required**:
Add guard checking CCDID consistency.

---

#### ⚠️ Issue #3: Client Certificate Time Validation Missing (SEVERITY: HIGH)

**Property Affected**: PROP_027

**Problem**: Root CA has explicit time validation transition, but Client Certificates do not.

**Gap**: 
- Root CA: `RootCAProvisioned -> TLSConnectionFailed` (time_validation_failed)
- Client Cert: No equivalent validation transition

**Impact**: Expired or not-yet-valid client certificates could be provisioned.

**Fix Required**:
Add time validation transition for Client Certificates before activation.

---

### Violations Found

| Property ID | Name | Severity | Verdict | Issue Type |
|------------|------|----------|---------|------------|
| PROP_026 | Fabric_Isolation_For_Certificates | CRITICAL | VIOLATED | Missing Fabric context |
| PROP_034 | Endpoint_Fabric_Association | CRITICAL | VIOLATED | Missing Fabric context |
| PROP_016 | Certificate_Provisioning_Uses_Returned_CCDID | HIGH | VIOLATED | Missing guard |
| PROP_009 | Nonce_Uniqueness_Per_CSR | CRITICAL | PARTIAL | No uniqueness tracking |
| PROP_027 | Time_Validation_For_Certificate_Validity | CRITICAL | PARTIAL | Missing client cert validation |
| PROP_031 | Certificate_Chain_Completeness | HIGH | PARTIAL | No completeness verification |

---

## Detailed Analysis

### PROP_001: TLS_Client_Only_Enforcement (CRITICAL)

**Property Claim**: "Only TLS Client Connections are permitted using clusters and commands in this specification; server connections are forbidden."

**Formal**: `∀connection, cluster. uses_cluster(connection, cluster) ⟹ is_tls_client(connection) ∧ ¬is_tls_server(connection)`

**FSM Analysis**:

**Verdict**: ⚠️ **UNVERIFIABLE** (FSM abstraction insufficient)

**Reason**: 
- FSM includes states: `TLSConnectionEstablishing`, `TLSConnectionEstablished`, `TLSConnectionFailed`
- Transitions use `initiate_tls_handshake()` function
- However, FSM does NOT model:
  - Whether connection is client-initiated or server-accepted
  - No guard checking `is_client_mode == true`
  - No rejection of incoming server connection attempts
  - Function `initiate_tls_handshake()` definition states "Initiates TLS client handshake" but guard doesn't prevent server mode

**Specification Evidence**:
```
Quote: "Only TLS Client Connections SHALL be allowed using the clusters and commands in this chapter."
Source: Section 14.3, First sentence (before Description), Page ~200
```

**Gap in FSM**: 
No transition or guard explicitly prevents server connection acceptance. The FSM assumes client-only behavior but doesn't enforce it.

**Recommendation**: 
Need transition guards like: `connection_type == CLIENT && ¬is_server_mode` on TLS connection establishment paths.

---

### PROP_003: Time_Sync_Prerequisite_For_TLS (CRITICAL)

**Property Claim**: "Nodes supporting TLS Certificate Management must have Time Synchronization cluster with NTPClient or TimeSyncClient feature enabled for certificate time validation."

**Formal**: `∀node. supports_cluster(node, TLSCertMgmt) ⟹ (supports_feature(node, NTPClient) ∨ supports_feature(node, TimeSyncClient))`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS** (with assumption)

**Supporting Evidence in FSM**:
- State `RootCAProvisioned` invariant: `"time_sync_cluster_available == true"`
- Transition `RootCAProvisioned -> TLSConnectionFailed` has guard: `time_validation_failed == true`
- Function `extract_not_before()` and `extract_not_after()` used for time validation

**Specification Evidence**:
```
Quote: "Nodes supporting TLS Certificate Management SHALL support the Time Synchronization cluster with either the `NTPClient` or `TimeSyncClient` feature enabled."
Source: Section 14.3.1, Paragraph 3
```

**Why HOLDS**: 
FSM enforces time synchronization availability as state invariant and validates certificate time periods before accepting certificates.

**Assumption**: Time synchronization cluster is correctly implemented and synchronized (assumed external, not modeled in this FSM).

---

### PROP_004: CAID_Uniqueness_Per_Fabric (HIGH)

**Property Claim**: "Each Certificate Authority ID (CAID) uniquely identifies exactly one TLSRCAC per Fabric on a Node."

**Formal**: `∀node, fabric, caid, ca1, ca2. identifies(caid, ca1, fabric, node) ∧ identifies(caid, ca2, fabric, node) ⟹ ca1 = ca2`

**FSM Analysis**:

**Verdict**: ⚠️ **VIOLATED** (Insufficient enforcement)

**Violation Path**:
```
State: Idle
Trigger: provision_root_ca_command (multiple times with same CAID)
Guard: "caid_unique_in_fabric == true" 
Action: "store_root_ca(caid, root_ca_cert)"
Result: RootCAProvisioned
```

**Problem Identified**:
1. Guard `caid_unique_in_fabric == true` checks uniqueness BEFORE first provisioning
2. However, there is NO guard preventing re-provisioning with SAME CAID

Look at transitions:
- `Idle -> RootCAProvisioned`: Guard checks `caid_unique_in_fabric == true`
- `RootCAProvisioned -> RootCAProvisioned` (self-loop for UPDATE): Guard is `update_operation == true && caid_exists == true`

**The UPDATE transition ALLOWS replacing the CA**:
- This is CORRECT per spec: "CAID can be used to get, **update**, or remove"
- But what if someone provisions TWICE with SAME CAID without using UPDATE?

**Closer Analysis**:
Looking at the FSM more carefully:
- Idle -> RootCAProvisioned requires `caid_unique_in_fabric == true`
- This should mean: "CAID doesn't exist yet in this Fabric"
- Once provisioned, subsequent operations use UPDATE transition (RootCAProvisioned -> RootCAProvisioned)

**Revised Verdict**: ✅ **HOLDS**

The guard `caid_unique_in_fabric == true` prevents duplicate CAID provisioning. Updates use the self-loop transition which explicitly checks `caid_exists == true`.

**Specification Evidence**:
```
Quote: "A Certificate Authority ID (CAID) is used to uniquely identify a provisioned TLSRCAC associated with a Fabric on a Node."
Source: Section 14.3.1.1, "Certificate Authority ID (CAID)" subsection
```

**Why HOLDS**: Guard enforces uniqueness at provisioning time, updates use explicit UPDATE transition.

---

### PROP_006: Single_CCD_Per_CCDID (CRITICAL)

**Property Claim**: "A Node stores exactly one Client Certificate Details (certificate + private key + chain) per CCDID."

**Formal**: `∀node, ccdid, ccd1, ccd2. stored(node, ccdid, ccd1) ∧ stored(node, ccdid, ccd2) ⟹ ccd1 = ccd2`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**Supporting Transitions**:
1. `CertificateCreated -> CertificateProvisioned`:
   - Guard: `certificate_valid == true && intermediate_chain_valid == true`
   - Action: `store_client_certificate_details(ccdid, client_cert, private_key, intermediate_chain)`
   - Comment: "Uses CCDID from ClientCSRResponse"

2. `CertificateProvisioned -> CertificateProvisioned` (UPDATE):
   - Guard: `update_operation == true && ccdid_exists == true`
   - Action: `update_client_certificate_details(ccdid, new_cert, new_key, new_chain)`
   - Comment: "Atomic replacement per spec"

**Specification Evidence**:
```
Quote: "A Node SHALL only store a single Client Certificate Details for a particular CCDID."
Source: Section 14.3.1.2, "Client Certificate Details ID (CCDID)" subsection
```

**Why HOLDS**: 
- Initial provisioning creates single CCD for CCDID
- Update transition performs atomic replacement (not addition)
- Function `update_client_certificate_details()` defined with REPLACE semantics in FSM

---

### PROP_008: Nonce_Generation_Randomness (CRITICAL)

**Property Claim**: "CSR nonce must be 32 bytes generated using cryptographically secure DRBG (Crypto_DRBG)."

**Formal**: `∀client, nonce. generates_nonce(client, nonce) ⟹ (length(nonce) = 32 ∧ source(nonce) = Crypto_DRBG)`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**Supporting Transition**:
```
Transition: Idle -> NonceGenerated
Guard: "tlscert_cluster_available == true"
Action: "nonce := generate_32byte_nonce()"
```

**Function Definition** (from FSM):
```json
{
  "name": "generate_32byte_nonce",
  "description": "Generate cryptographically secure 32-byte nonce using Crypto_DRBG per NIST SP 800-90A",
  "algorithm": "nonce := Crypto_DRBG(entropy_source, 32_bytes)"
}
```

**Specification Evidence**:
```
Quote: "The client SHALL generate a random 32 byte nonce using `Crypto_DRBG()`."
Source: Section 14.3.1.2, "TLS Client CSR Generation" step 1
```

**Why HOLDS**: 
Function explicitly uses Crypto_DRBG and generates exactly 32 bytes. FSM enforces this through function definition.

---

### PROP_009: Nonce_Uniqueness_Per_CSR (CRITICAL)

**Property Claim**: "Each CSR request must use a unique nonce value to ensure freshness and prevent replay attacks."

**Formal**: `∀client, csr1, csr2, nonce. (csr1 ≠ csr2) ∧ uses_nonce(csr1, nonce) ⟹ ¬uses_nonce(csr2, nonce)`

**FSM Analysis**:

**Verdict**: ⚠️ **VIOLATED** (No uniqueness tracking)

**Problem**: FSM generates new nonce each time but DOES NOT track previously used nonces.

**Attack Path**:
```
1. State: Idle -> NonceGenerated
   Action: nonce := generate_32byte_nonce()
   
2. State: NonceGenerated -> CSRRequested
   Action: send_csr_command(nonce)
   
3. State: (after completion, back to Idle)

4. State: Idle -> NonceGenerated (SECOND CSR)
   Action: nonce := generate_32byte_nonce()
   PROBLEM: No check if nonce was used before!
```

**Violation Mechanism**:
- `generate_32byte_nonce()` uses Crypto_DRBG which SHOULD generate unique values with overwhelming probability
- However, FSM does NOT explicitly verify uniqueness
- No guard checking: `nonce NOT IN previously_used_nonces`
- No state variable tracking: `used_nonces[]`

**Specification Evidence**:
```
Quote: "The client SHALL generate a random 32 byte nonce using `Crypto_DRBG()`."
Source: Section 14.3.1.2, step 1

Gap: Specification does NOT explicitly state "nonce MUST be unique" or "SHALL NOT reuse nonces"
```

**Specification Gap**: 
Spec assumes DRBG produces unique values but doesn't mandate explicit uniqueness checking. This is implicit security assumption, not explicit requirement.

**Severity Assessment**:
- Probability of DRBG collision: Negligible (2^-256 for 32 bytes)
- But: If DRBG is compromised or weak, replay attacks become possible
- FSM should explicitly check uniqueness as defense-in-depth

**Revised Verdict**: ⚠️ **PARTIALLY_HOLDS**
- Holds probabilistically (DRBG uniqueness assumption)
- Violated from formal verification perspective (no explicit uniqueness check)

---

### PROP_012: PKCS10_Signature_Verification (CRITICAL)

**Property Claim**: "Client must verify the inner signature in PKCS #10 CSR field according to PKCS #10 standard before accepting CSR."

**Formal**: `∀client, csr, signature. receives(client, csr) ⟹ must_verify(client, signature(csr), PKCS10_standard) before accepts(client, csr)`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**Supporting Transitions**:
```
Transition: CSRResponseReceived -> PKCS10SignatureVerified
Guard: verify_pkcs10_signature() == SUCCESS
Action: pkcs10_signature_valid := true

Transition: CSRResponseReceived -> PKCS10VerificationFailed  
Guard: verify_pkcs10_signature() == FAILURE
Action: error_message := "PKCS10 signature verification failed"
```

**Critical Ordering**:
- CSRResponseReceived → MUST verify PKCS10 → PKCS10SignatureVerified
- No path from CSRResponseReceived → CertificateProvisioned without verification
- Error states prevent progression if verification fails

**Specification Evidence**:
```
Quote: "The client SHALL verify the inner signature in the PKCS #10 of the CSR field in the ClientCSRResponse, per the definition of CSR signatures in PKCS #10."
Source: Section 14.3.1.2, "TLS Client CSR Generation" step 3
```

**Why HOLDS**: 
FSM enforces sequential verification with explicit state transitions. No bypass path exists.

---

### PROP_013: Nonce_Signature_Verification (CRITICAL)

**Property Claim**: "Client must verify NonceSignature in ClientCSRResponse matches the nonce sent in the corresponding ClientCSR command."

**Formal**: `∀client, nonce_sent, nonce_sig, csr. receives(client, csr, nonce_sig) ⟹ verify_signature(nonce_sig, nonce_sent, pubkey(csr))`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**Supporting Transitions**:
```
Transition: PKCS10SignatureVerified -> NonceSignatureVerified
Guard: verify_nonce_signature_validity(nonce, nonce_signature, public_key) == SUCCESS
Action: nonce_signature_valid := true

Transition: PKCS10SignatureVerified -> NonceSignatureVerificationFailed
Guard: verify_nonce_signature_validity(nonce, nonce_signature, public_key) == FAILURE  
Action: error_message := "Nonce signature verification failed"
```

**Specification Evidence**:
```
Quote: "The client SHALL verify NonceSignature field on the ClientCSRResponse is valid against the nonce value it provided in the corresponding ClientCSR command."
Source: Section 14.3.1.2, step 4
```

**Why HOLDS**: 
Explicit verification transition with failure path. No progression without successful verification.

---

### PROP_014: Public_Key_Consistency_Across_Signatures (CRITICAL)

**Property Claim**: "The public key used for NonceSignature must be identical to the public key in the PKCS #10 CSR inner signature."

**Formal**: `∀csr, nonce_sig, pkcs10_sig, pk1, pk2. uses_key(nonce_sig, pk1) ∧ uses_key(pkcs10_sig, pk2) ⟹ pk1 = pk2`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**Supporting Transition**:
```
Transition: NonceSignatureVerified -> PublicKeyConsistencyVerified
Guard: pkcs10_public_key == nonce_sig_public_key
Action: public_key_consistency_confirmed := true

Transition: NonceSignatureVerified -> PublicKeyConsistencyFailed
Guard: pkcs10_public_key != nonce_sig_public_key
Action: error_message := "Public key mismatch between PKCS10 and nonce signature"
```

**Key Extraction Functions**:
- `extract_public_key_from_pkcs10(csr)` - extracts pk1
- `extract_public_key_from_signature(nonce_sig)` - extracts pk2  
- Guard compares: `pk1 == pk2`

**Specification Evidence**:
```
Quote: "The client SHALL verify that the public key used for the NonceSignature is the same public key as the inner signature in the PKCS #10 of the CSR field."
Source: Section 14.3.1.2, step 5
```

**Why HOLDS**: 
Explicit state transition with equality guard. Failure path prevents progression.

---

### PROP_015: CSR_Validation_Before_Provisioning (CRITICAL)

**Property Claim**: "Client must complete all verification steps (PKCS #10 signature, nonce signature, public key consistency) before provisioning certificate."

**Formal**: `∀client, cert, csr. provisions(client, cert, ccdid) ⟹ (verified_pkcs10(csr) ∧ verified_nonce(csr) ∧ verified_key_consistency(csr))`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**State Sequence Enforcement**:
```
CSRResponseReceived 
  → PKCS10SignatureVerified (verification 1)
  → NonceSignatureVerified (verification 2)  
  → PublicKeyConsistencyVerified (verification 3)
  → CertificateCreated
  → CertificateProvisioned
```

**Critical Observation**:
- No transition bypasses any verification state
- Certificate provisioning only reachable after ALL three verifications complete
- Error states create separate terminal paths that never reach provisioning

**Specification Evidence**:
```
Quote (combined):
Step 3: "SHALL verify the inner signature in the PKCS #10"
Step 4: "SHALL verify NonceSignature field"  
Step 5: "SHALL verify that the public key used for the NonceSignature is the same public key"
Step 7: "SHALL provision the resulting TLS Client Certificate"
Source: Section 14.3.1.2, steps 3-5, 7
```

**Why HOLDS**: 
Linear state progression enforces all-or-nothing verification. No bypass paths exist in FSM.

---

### PROP_026: Fabric_Isolation_For_Certificates (CRITICAL)

**Property Claim**: "Certificates provisioned in one Fabric must not be used for TLS connections in a different Fabric."

**Formal**: `∀n:node, cert:certificate, f1:fabric, f2:fabric. provisioned(cert, n, f1) ∧ used(cert, n, f2) ⟹ f1 = f2`

**FSM Analysis**:

**Verdict**: 🔴 **VIOLATED** (No Fabric isolation enforcement in FSM)

**Problem**: FSM does NOT model Fabric context in any state or transition.

**Missing Guards/Checks**:
- No state variable: `current_fabric`
- No guard checking: `certificate.fabric == connection.fabric`
- No function parameter: `store_root_ca(caid, root_ca_cert)` - missing fabric parameter
- No transition guard preventing cross-Fabric usage

**Attack Path** (if Fabric isolation not enforced):
```
1. State: Idle (Fabric A)
   Provision Root CA with CAID=1 for Fabric A
   
2. State: RootCAProvisioned
   Store: root_ca[caid=1, fabric=A]
   
3. Switch context to Fabric B (no FSM transition for this!)

4. State: EndpointActive (Fabric B)  
   Trigger: establish_tls_connection
   Action: initiate_tls_handshake(endpoint_id, caid=1)
   PROBLEM: Uses Root CA from Fabric A to validate server in Fabric B!
```

**Specification Evidence**:
```
Quote: (Implicit requirement - not explicitly stated in section 14.3)
However, Matter spec has fundamental Fabric isolation: "Each Fabric SHALL be isolated from all other Fabrics"
Source: Matter Core Spec Section on Fabrics (not in provided 14.3 excerpt)
```

**Specification Gap in Section 14.3**: 
The TLS Certificate Management section does NOT explicitly state Fabric isolation requirements. This is assumed from general Matter architecture.

**FSM Gap**: 
Functions like `store_root_ca()`, `store_client_certificate_details()`, `retrieve_root_ca_by_caid()` do NOT include `fabric_id` as a parameter. This suggests the FSM abstraction doesn't model Fabric isolation.

**Severity**: CRITICAL - Cross-Fabric certificate usage would break multi-tenancy security.

**Recommendations**:
1. Add `fabric_id` to all state variables storing certificates
2. Add guard to all certificate usage transitions: `cert.fabric == current_fabric`
3. Make all certificate storage/retrieval functions Fabric-scoped

---

### PROP_027: Time_Validation_For_Certificate_Validity (CRITICAL)

**Property Claim**: "Certificates must be time-validated against synchronized time source (notBefore ≤ current_time ≤ notAfter)."

**Formal**: `∀n:node, cert:certificate, t:time. certificate_accepted(n, cert, t) ⟹ in_validity_period(cert, t)`

**FSM Analysis**:

**Verdict**: ⚠️ **PARTIALLY_HOLDS** (Validation present but error handling unclear)

**Supporting Transitions**:
```
Transition: RootCAProvisioned -> TLSConnectionFailed
Guard: time_validation_failed == true
Action: failure_reason := determine_time_validation_failure_reason()
Comment: "Certificate not yet valid or expired"
```

**Functions Used**:
- `extract_not_before(certificate)` - gets validity start time
- `extract_not_after(certificate)` - gets validity end time  
- `current_timestamp()` - gets current time
- Comparison: `notBefore <= current_time <= notAfter`

**Problem Found**: 
1. Time validation CHECK exists for Root CA (RootCAProvisioned state)
2. But WHERE is the check for Client Certificates (CCD)?
   - CertificateProvisioned state does NOT have time validation transition
   - No CertificateProvisioned -> CertificateInvalid transition for time errors

**Deeper Analysis**:
Looking at CertificateProvisioned state:
```json
{
  "name": "CertificateProvisioned",
  "invariants": [
    "ccdid_assigned == true",
    "client_cert_stored == true",
    "private_key_stored_securely == true",
    "intermediate_chain_stored == true"
  ]
}
```

**Missing**: `certificate_time_valid == true` - not in invariants!

**Partial Violation**:
- Root CA: Time validated ✅
- Client Certificate: Time validation NOT explicitly modeled in FSM ❌

**Specification Evidence**:
```
Quote: "Since standard Web PKI and TLS policy performs time and date validation of all X.509 certificates in the chain, Nodes supporting TLS Certificate Management SHALL support the Time Synchronization cluster"
Source: Section 14.3.1, Paragraph 3
```

**Why PARTIALLY_HOLDS**: 
Root CA validation present. Client certificate time validation implicit (happens during TLS handshake) but not explicit in FSM.

**Severity**: HIGH - Client certificates could be provisioned in expired/not-yet-valid state.

---

### PROP_028: Atomicity_Of_Certificate_Update (CRITICAL)

**Property Claim**: "Certificate update operations must be atomic (all-or-nothing). Either entire update succeeds or old certificate remains."

**Formal**: `∀n:node, ccdid:id, old:cert, new:cert. update_attempted(n, ccdid, old, new) ⟹ (stored(n, ccdid, new) ∧ ¬stored(n, ccdid, old)) ∨ (stored(n, ccdid, old) ∧ ¬stored(n, ccdid, new))`

**FSM Analysis**:

**Verdict**: ⚠️ **UNVERIFIABLE** (FSM abstracts atomicity)

**Update Transition**:
```
Transition: CertificateProvisioned -> CertificateProvisioned (self-loop)
Trigger: update_ccd_command
Guard: update_operation == true && ccdid_exists == true
Action: update_client_certificate_details(ccdid, new_cert, new_key, new_chain)
Comment: "Atomic replacement per spec"
```

**Function Definition**:
```json
{
  "name": "update_client_certificate_details",
  "description": "... All three components replaced atomically",
  "algorithm": "atomic { cert[ccdid] := new_cert; key[ccdid] := new_key; chain[ccdid] := new_chain }"
}
```

**Problem**: 
1. Function states "atomic" in description
2. Algorithm uses pseudo-code `atomic { }` block
3. But HOW is atomicity implemented? (Transaction log? Two-phase commit? Copy-on-write?)

**FSMAbstraction Level**: 
The FSM assumes atomicity is provided by underlying storage layer but doesn't model the mechanism.

**Specification Evidence**:
```
Quote: "Any update of the key set, including a partial update, SHALL remove all previous keys in the set"
Source: This is from a DIFFERENT section (Group Key Management), but similar atomicity requirement
```

**Section 14.3 Gap**: 
Certificate update atomicity is NOT explicitly stated in section 14.3. The spec says "update" but doesn't specify transaction semantics.

**Why UNVERIFIABLE**: 
FSM models atomic operation as single action, but actual implementation could fail mid-update. FSM abstraction is too high-level to verify low-level atomicity.

**Recommendation**: 
FSM should model intermediate states like:
- `CCDUpdateInProgress` (old cert still active, new cert staging)
- `CCDUpdateCommitting` (transaction commit point)
- Success → `CertificateProvisioned` (new cert active)
- Failure → `CertificateProvisioned` (old cert still active)

---

### PROP_029: Atomicity_Of_Certificate_Removal (CRITICAL)

**Property Claim**: "Certificate removal must atomically delete certificate, private key, and chain together. No partial removal."

**Formal**: `∀n:node, ccdid:id, ccd:certdetails. removed(n, ccdid) ⟹ ¬exists(ccd.cert) ∧ ¬exists(ccd.key) ∧ ¬exists(ccd.chain)`

**FSM Analysis**:

**Verdict**: ⚠️ **UNVERIFIABLE** (Same issue as PROP_028)

**Removal Transition**:
```
Transition: CertificateProvisioned -> CCDRemoved
Trigger: remove_ccd_command  
Guard: ccdid_exists == true && ccdid_not_in_use == true
Action: remove_client_certificate_details(ccdid)
Comment: "Atomic removal - certificate, private key, and chain removed together"
```

**Function Definition**:
```json
{
  "name": "remove_client_certificate_details",
  "algorithm": "atomic { delete cert[ccdid]; securely_erase key[ccdid]; delete chain[ccdid] }"
}
```

**Problem**: 
Same as PROP_028 - atomicity claimed but mechanism unspecified.

**Additional Risk**: 
Removal is more critical than update because it involves **secure key erasure**. If removal fails partway:
- Cert deleted but private key remains → key leakage vulnerability
- Key erased but cert remains → authentication failure with orphaned cert

**Specification Gap**: 
Section 14.3 has NO explicit requirement for atomic removal.

**Why UNVERIFIABLE**: 
Cannot verify atomicity at FSM abstraction level. Implementation-dependent.

---

### PROP_030: Private_Key_Protection_In_CCD (CRITICAL)

**Property Claim**: "Private keys in CCD must never be disclosed outside secure storage. Only internal use allowed."

**Formal**: `∀n:node, ccdid:id, pk:privkey. key_stored(n, ccdid, pk) ⟹ ¬key_disclosed(pk) ∧ key_internal_use(pk)`

**FSM Analysis**:

**Verdict**: ⚠️ **PARTIALLY_HOLDS** (Protected in provisioning but vulnerable in RETRIEVE)

**Storage Protection**:
```
Function: store_client_certificate_details()
Algorithm: "Store private key in secure storage (TEE/SE/HSM) with access controls preventing external access"
```

**State Invariant**:
```
State: CertificateProvisioned
Invariant: "private_key_stored_securely == true"
```

**PROBLEM - RETRIEVE Operation**:
```
Transition: CertificateProvisioned -> CertificateProvisioned (self-loop)
Trigger: retrieve_ccd_command
Guard: ccdid_exists == true
Action: ccd_data := retrieve_ccd_by_ccdid(ccdid)
```

**What does `retrieve_ccd_by_ccdid()` return?**
```json
{
  "function": "retrieve_ccd_by_ccdid",
  "returns": "Client certificate, intermediate chain, and metadata (but NOT private key)"
}
```

Checking the function definition more carefully:
```json
{
  "name": "retrieve_ccd_by_ccdid",
  "description": "Retrieve Client Certificate Details by CCDID for query operations",  
  "algorithm": "return { cert: cert[ccdid], chain: chain[ccdid], metadata: {...} }; // Private key NOT returned"
}
```

**Good News**: Function explicitly states private key NOT returned!

**But wait - Property PROP_038 exists**:
```
PROP_038: Private_Key_Never_Returned_By_Query (CRITICAL)  
Claim: "Private keys must never be returned by RETRIEVE operations even if CCD is queried"
```

This confirms the vulnerability concern was already identified!

**Revised Analysis**:
- FSM correctly models that RETRIEVE doesn't return private key
- Property protection HOLDS in FSM
- But implementation must enforce this (FSM models intent, not enforcement)

**Verdict**: ✅ **HOLDS** (in FSM model)

**Note**: Actual implementation vulnerability exists if `retrieve_ccd_by_ccdid()` is implemented incorrectly to return private key.

---

### PROP_034: Endpoint_Fabric_Association (HIGH)

**Property Claim**: "Endpoints must be associated with specific Fabric and only used for connections in that Fabric."

**Formal**: `∀ep:endpoint, f1:fabric, f2:fabric. endpoint_used(ep, f1) ∧ endpoint_configured(ep, f2) ⟹ f1 = f2`

**FSM Analysis**:

**Verdict**: 🔴 **VIOLATED** (Same issue as PROP_026 - No Fabric modeling)

**Problem**: 
Endpoint states and transitions do NOT include Fabric context.

**Endpoint States**:
- `EndpointProvisioned`
- `EndpointActive`  
- `EndpointRemoved`

**Endpoint Functions**:
```json
{
  "name": "store_endpoint",
  "parameters": ["endpoint_id", "endpoint_config"],
  "missing": "fabric_id parameter"
}
```

**No Fabric Isolation**:
- No state variable: `endpoint.fabric`
- No guard: `endpoint.fabric == current_fabric`
- No prevention of cross-Fabric endpoint usage

**Attack Scenario**:
```
1. Provision endpoint in Fabric A with endpoint_id=1
2. Switch to Fabric B context  
3. Use endpoint_id=1 to establish connection
4. Result: Endpoint from Fabric A used in Fabric B (isolation violation)
```

**Specification Evidence**:
```
Quote: "TLS endpoints SHALL be provisioned using the ProvisionEndpoint command"
Source: Section 14.3.2.1
Gap: No mention of Fabric isolation for endpoints
```

**Severity**: CRITICAL - Endpoint reuse across Fabrics breaks isolation.

**Same Root Cause as PROP_026**: FSM doesn't model Fabric context.

---

### PROP_038: Private_Key_Never_Returned_By_Query (CRITICAL)

**Property Claim**: "Private keys must never be returned by RETRIEVE operations even if CCD is queried."

**Formal**: `∀n:node, ccdid:id, result:data, pk:privkey. retrieve_executed(n, ccdid, result) ⟹ ¬contains(result, pk)`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS** (in FSM specification)

**RETRIEVE Transition**:
```
Transition: CertificateProvisioned -> CertificateProvisioned
Trigger: retrieve_ccd_command
Action: ccd_data := retrieve_ccd_by_ccdid(ccdid)
```

**Function Definition**:
```json
{
  "name": "retrieve_ccd_by_ccdid",
  "algorithm": "return { cert: cert[ccdid], chain: chain[ccdid] }; // Private key explicitly NOT included",
  "description": "Returns certificate and chain but NOT private key for security"
}
```

**Explicit Protection**: 
Function specification explicitly states private key is not returned.

**Specification Evidence**:
```
Quote: (Implicit from security principles - not explicitly stated in 14.3)
Private key protection is fundamental security principle
```

**Why HOLDS**: 
FSM models correct behavior (query returns cert/chain only, not key).

**Implementation Risk**: 
If actual implementation accidentally includes private key in response, property violated. But FSM specification is correct.

---

### PROP_016: Certificate_Provisioning_Uses_Returned_CCDID (HIGH)

**Property Claim**: "Certificate provisioning must use the CCDID returned in ClientCSRResponse, not a different CCDID."

**Formal**: `∀c:client, csr:response, ccdid1:id, prov:command, ccdid2:id. csr_returned(csr, ccdid1) ∧ provision_uses(prov, ccdid2) ⟹ ccdid1 = ccdid2`

**FSM Analysis**:

**Verdict**: 🔴 **VIOLATED** (No guard enforcing CCDID matching)

**Critical Transitions**:
```
Transition: CSRRequested -> CSRResponseReceived
Action: csr_response := receive_response(); 
        ccdid_returned := csr_response.ccdid

Transition: CertificateCreated -> CertificateProvisioned  
Action: store_client_certificate_details(ccdid, client_cert, private_key, intermediate_chain)
```

**Problem Identified**:
Where does `ccdid` parameter come from in the provisioning transition?

Looking at state variables:
```
State: CertificateCreated
Variables: {
  ccdid_returned: "CCDID from CSRResponse",
  signed_certificate: "Certificate from CA"
}
```

**Is there a guard checking**: `ccdid_used_in_provisioning == ccdid_returned` ?

**NO** - The transition does NOT have such a guard!

**Attack Path**:
```
1. Client sends CSR for rotation of CCDID=1
2. Node returns CSRResponse with CCDID=1  
3. Client provisions certificate but accidentally uses CCDID=2 in ProvisionClientCertificate command
4. Result: Certificate for CCDID=1's key provisioned under CCDID=2 → certificate/key mismatch!
```

**Specification Evidence**:
```
Quote: "The client SHALL provision the resulting TLS Client Certificate... using the CCDID value returned in the ClientCSRResponse."
Source: Section 14.3.1.2, step 7
```

**FSM Gap**: 
No guard enforcing: `provision_command.ccdid == csr_response.ccdid`

**Severity**: HIGH - Allows certificate/key mismatch, breaking authentication.

**Recommendation**: 
Add guard to CertificateCreated → CertificateProvisioned transition:
```
Guard: provision_ccdid == ccdid_returned
```

---

### PROP_011: CCDID_Provided_For_Rotation (MEDIUM)

**Property Claim**: "When rotating client certificates, existing CCDID must be provided in ClientCSR command."

**Formal**: `∀client, csr, ccdid. is_rotation(csr) ⟹ provides(csr, ccdid) ∧ exists_before(ccdid)`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**Rotation Path**:
```
Transition: CertificateProvisioned -> CCDRotationInProgress
Trigger: initiate_certificate_rotation
Guard: certificate_needs_rotation == true
Comment: "Initiates rotation for existing CCDID"

Transition: CCDRotationInProgress -> NonceGenerated  
Trigger: start_rotation_csr
Guard: ccdid_to_rotate != null
Action: is_rotation := true
```

**CSR Sending**:
```
Transition: NonceGenerated -> CSRRequested
Action: send_csr_command(nonce, is_rotation ? existing_ccdid : null)
```

**Guard Present**: `ccdid_to_rotate != null` enforces CCDID exists for rotation.

**Specification Evidence**:
```
Quote: "If rotating, an existing CCDID SHALL be provided."
Source: Section 14.3.1.2, step 2
```

**Why HOLDS**: 
Guard prevents rotation without existing CCDID. Non-rotation path doesn't require CCDID.

---

### PROP_019: Root_CA_Storage_Minimum (HIGH)

**Property Claim**: "Nodes must provide storage for at least 5 Root certificates per Fabric."

**Formal**: `∀n:node, f:fabric. supports_tls_cert(n) ⟹ storage_capacity(n, f, root_cert, 5)`

**FSM Analysis**:

**Verdict**: ⚠️ **UNVERIFIABLE** (Capacity not modeled in FSM)

**Problem**: 
FSM does not model storage capacity limits or quotas.

**What FSM Models**:
- States: `RootCAProvisioned`, `RootCAActive`, `RootCARemoved`
- Transitions: Provision, update, remove
- No transition checking: `available_storage_slots > 0`
- No state variable: `provisioned_root_ca_count`

**Missing Guards**:
```
Transition: Idle -> RootCAProvisioned
Current Guard: caid_unique_in_fabric == true
Missing Guard: provisioned_root_ca_count < MAX_ROOT_CA_CAPACITY
```

**Specification Evidence**:
```
Quote: "Nodes SHALL provide enough storage space for at least 5 Root certificates per Fabric on a Node."
Source: Section 14.3.3.1, "Minimum storage for TLS Certificates"
```

**Why UNVERIFIABLE**: 
Storage capacity is implementation detail not represented in FSM state space.

**Note**: This is a REQUIREMENT, not a security property to verify against FSM. It's a design constraint.

---

### PROP_020: Client_Certificate_Storage_Minimum (HIGH)

**Property Claim**: "Nodes must provide storage for at least 2 Client Certificate Details per Fabric."

**Formal**: `∀n:node, f:fabric. supports_tls_client(n) ⟹ storage_capacity(n, f, client_cert, 2)`

**FSM Analysis**:

**Verdict**: ⚠️ **UNVERIFIABLE** (Same issue as PROP_019)

**Same Problem**: Storage capacity not modeled in FSM.

**Specification Evidence**:
```
Quote: "Nodes SHALL provide enough storage space for at least 2 Client Certificate Details per Fabric on a Node."
Source: Section 14.3.3.1
```

---

### PROP_024: CSR_Process_Ordered_Execution (HIGH)

**Property Claim**: "CSR process must follow ordered steps: nonce generation → CSR send → verification → certificate creation → provisioning."

**Formal**: `∀p:process. csr_complete(p) ⟹ event_order(nonce_gen, csr_send, verify, create, provision)`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**State Sequence**:
```
Idle → NonceGenerated → CSRRequested → CSRResponseReceived → 
PKCS10SignatureVerified → NonceSignatureVerified → PublicKeyConsistencyVerified →
CertificateCreated → CertificateProvisioned
```

**Enforcement Mechanism**: 
Linear state progression with no bypass transitions. Each state only reachable from previous state.

**Specification Evidence**:
```
Quote (combined steps 1-7):
"1. The client SHALL generate a random 32 byte nonce...
 2. The client SHALL send the nonce to the Node...
 3. The client SHALL verify the inner signature...
 4. The client SHALL verify NonceSignature field...
 5. The client SHALL verify that the public key...
 7. The client SHALL provision the resulting TLS Client Certificate..."
Source: Section 14.3.1.2
```

**Why HOLDS**: 
FSM structure enforces sequential ordering. No state transitions allow reordering.

---

### PROP_025: Server_Authentication_Via_Root_CA (CRITICAL - from FSM internal)

**Property Claim**: "TLS connections must authenticate server using provisioned Root CA."

**Formal**: `∀c:client, s:server, conn:connection. connection_established(c, s, conn) ⟹ server_authenticated(s, root_ca(c))`

**FSM Analysis**:

**Verdict**: ⚠️ **UNVERIFIABLE** (TLS handshake abstracted)

**TLS Connection States**:
```
State: EndpointActive
Trigger: establish_tls_connection
→ TLSConnectionEstablishing
Action: initiate_tls_handshake(endpoint_id, caid)

State: TLSConnectionEstablishing
→ TLSConnectionEstablished (success)
→ TLSConnectionFailed (failure)
```

**Function**:
```json
{
  "name": "initiate_tls_handshake",
  "description": "Initiates TLS client handshake with server authentication using Root CA identified by CAID",
  "algorithm": "Uses TLS 1.2+ with server certificate validation against root_ca[caid]"
}
```

**Problem**: 
Function claims to use Root CA but FSM doesn't model:
- Certificate chain validation steps
- Root CA matching logic
- What happens if server cert doesn't chain to provisioned Root CA

**Abstraction Level**: 
FSM treats TLS handshake as atomic operation. Actual server authentication protocol not modeled.

**Specification Evidence**:
```
Quote: "Authentication of a server ensures that the client is connecting to the correct server and not to an impostor. TLS uses Root CA Certificates to authenticate a server during the handshake process."
Source: Section 14.3.1.1, first paragraph
```

**Why UNVERIFIABLE**: 
FSM abstracts TLS handshake details. Cannot verify internal authentication logic.

---

### PROP_031: Certificate_Chain_Completeness (HIGH - from FSM internal)

**Property Claim**: "CCD must include complete certificate chain from client cert to root CA."

**Formal**: `∀ccd:certdetails, cc:cert, rc:cert. ccd_contains(ccd, cc) ⟹ ∃chain. complete_chain(chain, cc, rc) ∧ ccd_contains_chain(ccd, chain)`

**FSM Analysis**:

**Verdict**: ⚠️ **PARTIALLY_HOLDS** (Completeness not verified)

**Storage**:
```
Function: store_client_certificate_details()
Parameters: (ccdid, client_cert, private_key, intermediate_chain)
```

**Problem**: 
Who validates that `intermediate_chain` is COMPLETE?

**Checking Transition**:
```
Transition: CertificateCreated -> CertificateProvisioned
Guard: certificate_valid == true && intermediate_chain_valid == true
```

**What does `intermediate_chain_valid` check?**
Looking at function:
```json
{
  "name": "get_intermediate_certificate_chain",
  "description": "Obtains intermediate certificate chain needed for TLS handshake",
  "algorithm": "Returns chain of certificates from client cert to root CA (exclusive of root)"
}
```

**ASSUMPTION**: Chain obtained from CA is complete.
**NOT VERIFIED**: FSM doesn't verify chain actually connects to provisioned Root CA.

**Attack Scenario**:
```
1. CA provides incomplete chain (missing intermediate cert)
2. Client provisions with incomplete chain
3. TLS handshake fails because server cannot validate chain to root
4. Result: Denial of Service (legitimate certificate unusable)
```

**Specification Evidence**:
```
Quote: "Client Certificate Details (CCD) is used to refer to the combination of client certificate, private key and chain of intermediate certificates that is needed to complete the TLS handshake"
Source: Section 14.3.1.2, introductory paragraph
```

**Why PARTIALLY_HOLDS**: 
Chain is stored but completeness not verified against provisioned Root CA.

**Severity**: MEDIUM - Incomplete chain causes operational failure, not security breach.

---

### PROP_032: CAID_Identifies_Single_Slot_Over_Time (HIGH - from FSM internal)

**Property Claim**: "CAID must consistently identify the same storage slot over time (no CAID reuse for different CAs)."

**Formal**: `∀n:node, caid:id, s1:slot, s2:slot, t1:time, t2:time. identifies(caid, s1, t1) ∧ identifies(caid, s2, t2) ⟹ s1 = s2`

**FSM Analysis**:

**Verdict**: 🔴 **VIOLATED** (CAID reuse after removal allowed)

**Problem Scenario**:
```
1. Time T1: Provision Root CA_A with CAID=1
   State: RootCAProvisioned
   Storage: slot[1] = CA_A

2. Time T2: Remove Root CA_A
   Transition: RootCAActive -> RootCARemoved
   Action: remove_root_ca(caid=1)
   Storage: slot[1] = empty

3. Time T3: Provision Root CA_B with CAID=1
   Transition: Idle -> RootCAProvisioned
   Guard: caid_unique_in_fabric == true (PASSES because CAID=1 was removed!)
   Storage: slot[1] = CA_B
```

**Violation**: 
CAID=1 now identifies CA_B, previously identified CA_A. Same CAID, different CAs over time.

**Is This Actually a Violation?**
Looking at specification intent:
- CAID is an identifier for currently provisioned CA
- After removal, CAID can be reused
- This is normal identifier recycling

**Revised Analysis**: 
The property as stated requires "single slot over time" which could mean:
- Interpretation 1: CAID always maps to same slot (reuse allowed) ✅
- Interpretation 2: CAID never reused for different CA (reuse forbidden) ❌

**Specification Evidence**:
```
Quote: "A Certificate Authority ID (CAID) is used to uniquely identify a provisioned TLSRCAC associated with a Fabric on a Node."
Source: Section 14.3.1.1
Context: "uniquely identify a PROVISIONED TLSRCAC" - implies active/current, not historical
```

**Revised Verdict**: ✅ **HOLDS** (CAID identifier recycling is normal)

The property should be: "CAID uniquely identifies currently provisioned CA" not "CA over all time."

---

### PROP_033: CCDID_Identifies_Single_Slot_Over_Time (HIGH)

**Property Claim**: "CCDID must consistently identify the same storage slot over time."

**Formal**: `∀n:node, ccdid:id, s1:slot, s2:slot, t1:time, t2:time. identifies(ccdid, s1, t1) ∧ identifies(ccdid, s2, t2) ⟹ s1 = s2`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS** (Same analysis as PROP_032)

CCDID recycling after removal is normal behavior. Property holds for currently provisioned CCDs.

---

### PROP_010: CSR_Nonce_Transmission_Ordering (HIGH)

**Property Claim**: "Client must generate nonce before sending CSR request containing that nonce."

**Formal**: `∀client, nonce, csr. sends(client, csr, nonce) ⟹ happens_before(generates_nonce(client, nonce), sends(client, csr, nonce))`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**State Ordering**:
```
State: Idle
→ NonceGenerated (Action: nonce := generate_32byte_nonce())
→ CSRRequested (Action: send_csr_command(nonce))
```

**Enforcement**: 
Cannot reach CSRRequested without first passing through NonceGenerated. Linear progression enforces ordering.

**Specification Evidence**:
```
Quote: "1. The client SHALL generate a random 32 byte nonce...
        2. The client SHALL send the nonce to the Node..."
Source: Section 14.3.1.2, steps 1-2
```

**Why HOLDS**: 
FSM state transitions enforce happens-before relationship.

---

### PROP_035: Large_Message_Qualifier_For_All_Commands (MEDIUM)

**Property Claim**: "All commands in TLS Certificate Management cluster must use Large Message qualifier."

**Formal**: `∀cmd:command. cluster_command(cmd, tlscert_cluster) ⟹ has_large_msg_qualifier(cmd)`

**FSM Analysis**:

**Verdict**: ⚠️ **UNVERIFIABLE** (Protocol encoding not modeled)

**Problem**: 
FSM models commands as triggers (e.g., `provision_root_ca_command`) but doesn't model protocol-level encoding or message qualifiers.

**Specification Evidence**:
```
Quote: "Commands in this cluster uniformly use the Large Message qualifier, even when the command doesn't require it, to reduce the testing matrix."
Source: Section 14.4, "TLS Certificate Management Cluster" intro
```

**Why UNVERIFIABLE**: 
Message encoding is protocol layer detail not represented in state machine.

**Note**: This is encoding requirement, not behavioral property to verify with FSM.

---

### PROP_040: Optional_CCD_Provisioning (MEDIUM)

**Property Claim**: "Nodes MAY choose to skip CCD provisioning if client certificate authentication not needed."

**Formal**: `∀n:node. tls_client_capable(n) ⟹ (ccd_provisioned(n) ∨ ccd_skipped(n))`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS**

**Optional Path**:
```
Transition: CertificateCreated -> CertificateProvisioned (skip_ccd_provisioning)
Trigger: skip_ccd_provisioning
Guard: client_cert_auth_not_required == true
Comment: "Nodes MAY choose not to provision CCD per spec 14.3.1.2"
```

**Specification Evidence**:
```
Quote: "Some TLS Servers MAY choose to implement Client Certificate Authentication. To facilitate this, Nodes MAY choose to provision Client Certificate Details"
Source: Section 14.3.1.2, first paragraph
```

**Why HOLDS**: 
FSM includes optional skip transition for nodes that don't need client authentication.

---

### PROP_041: Query_Operations_Idempotent_And_Side_Effect_Free (HIGH)

**Property Claim**: "Query operations (GET, RETRIEVE) must be idempotent and side-effect free."

**Formal**: `∀n:node, op:query.operation. is_query(op) ⟹ idempotent(op) ∧ ¬has_side_effects(op)`

**FSM Analysis**:

**Verdict**: ✅ **HOLDS** (in FSM model)

**Query Transitions** (all self-loops):
```
RootCAProvisioned -> RootCAProvisioned (get_root_ca_command)
RootCAActive -> RootCAActive (get_root_ca_command)
CertificateProvisioned -> CertificateProvisioned (retrieve_ccd_command)
ClientCertDetailsActive -> ClientCertDetailsActive (retrieve_ccd_command)
EndpointProvisioned -> EndpointProvisioned (query_endpoint_command)
EndpointActive -> EndpointActive (query_endpoint_command)
```

**Properties**:
1. **State-preserving**: From_state == To_state (no state change)
2. **Read-only actions**: Actions only read data, don't modify storage
3. **Idempotent**: Executing twice gives same result

**Example**:
```
Action: root_ca_data := retrieve_root_ca_by_caid(caid)
Effect: Reads data, doesn't modify root_ca[caid]
```

**Why HOLDS**: 
All query transitions are self-loops with read-only actions. No state modifications.

---

## Recommendations for FSM Corrections

### Priority 1: Add Fabric Isolation (CRITICAL)

**Affected Properties**: PROP_026, PROP_034

**Required Changes**:

1. **Add Fabric Context to All States**
```json
{
  "state_variables": {
    "current_fabric": "fabric_id",
    "resource_fabric": "fabric_id associated with certificate/endpoint"
  }
}
```

2. **Update All Storage Functions**
```
store_root_ca(fabric_id, caid, root_ca_cert)
store_client_certificate_details(fabric_id, ccdid, client_cert, private_key, chain)
store_endpoint(fabric_id, endpoint_id, endpoint_config)
```

3. **Add Fabric Isolation Guards**
```
All certificate/endpoint usage transitions:
Guard: resource.fabric == current_fabric
```

### Priority 2: Add CCDID Consistency Check (HIGH)

**Affected Property**: PROP_016

**Required Change**:
```json
{
  "transition": "CertificateCreated -> CertificateProvisioned",
  "guard": "provision_ccdid == csr_response.ccdid && certificate_valid == true && intermediate_chain_valid == true"
}
```

### Priority 3: Add Client Certificate Time Validation (HIGH)

**Affected Property**: PROP_027

**Required Changes**:

1. **Add Time Validation Transition**
```json
{
  "from_state": "CertificateProvisioned",
  "to_state": "ClientCertDetailsActive",
  "trigger": "validate_certificate_time",
  "guard": "notBefore <= current_time && current_time <= notAfter",
  "comment": "Time validation before activating client certificate"
},
{
  "from_state": "CertificateProvisioned",
  "to_state": "ProvisioningFailed",
  "trigger": "validate_certificate_time",
  "guard": "notBefore > current_time || current_time > notAfter",
  "comment": "Certificate time validation failed"
}
```

2. **Add Invariant**
```json
{
  "state": "ClientCertDetailsActive",
  "invariants": ["certificate_time_valid == true"]
}
```

### Priority 4: Add Explicit Nonce Uniqueness Tracking (MEDIUM)

**Affected Property**: PROP_009

**Required Changes**:

1. **Add State Variable**
```json
{
  "state_variables": {
    "used_nonces": "set of previously used nonce values"
  }
}
```

2. **Add Guard**
```json
{
  "transition": "Idle -> NonceGenerated",
  "guard": "nonce NOT IN used_nonces && tlscert_cluster_available == true"
}
```

3. **Update Action**
```json
{
  "action": "nonce := generate_32byte_nonce(); used_nonces := used_nonces ∪ {nonce}"
}
```

### Priority 5: Add Certificate Chain Completeness Verification (MEDIUM)

**Affected Property**: PROP_031

**Required Changes**:

1. **Add Verification Function**
```json
{
  "name": "verify_chain_completeness",
  "parameters": ["client_cert", "intermediate_chain", "root_ca"],
  "returns": "boolean",
  "algorithm": "Verify each cert in chain validates with next, ending at root_ca"
}
```

2. **Add Guard**
```json
{
  "transition": "CertificateCreated -> CertificateProvisioned",
  "guard": "verify_chain_completeness(client_cert, chain, root_ca) == true"
}
```

---

## Appendix A: Properties Not Fully Analyzed

The following properties were not deeply analyzed (would require additional specification context or are lower priority):

- PROP_002: TLS_Cluster_Support_Mandatory (architectural requirement)
- PROP_005: CAID_Operations_Available (operational requirement)
- PROP_007: CCDID_Operations_Available (operational requirement)
- PROP_017: TLS_Client_Management_Cluster_Required (cross-cluster dependency)
- PROP_018: Endpoint_Provisioning_Via_Command (operational requirement)
- PROP_021: Endpoint_Storage_Minimum (capacity requirement)
- PROP_022: Concurrent_TLS_Connections_Minimum (capacity requirement)
- PROP_023: TLS_Cluster_On_Root_Endpoint_Only (deployment constraint)
- PROP_036: GET_Operation_Via_CAID_Available (operational requirement)
- PROP_037: RETRIEVE_Operation_Via_CCDID_Available (operational requirement)
- PROP_039: TLS_Client_Management_Cluster_Required (duplicate of PROP_017)

These properties are primarily requirements about cluster presence, storage capacity, or command availability rather than behavioral security properties that can be verified against FSM execution paths.

---

## Appendix B: Specification Gaps Identified

### Gap 1: Fabric Isolation Not Explicit in Section 14.3

**Issue**: While Matter architecture assumes Fabric isolation, Section 14.3 does not explicitly state that certificates must be Fabric-scoped.

**Quote Missing**: "Certificates and endpoints SHALL be isolated per Fabric. A certificate provisioned in Fabric A SHALL NOT be usable for TLS connections in Fabric B."

**Impact**: Implementers might miss this critical requirement if only reading Section 14.3.

---

### Gap 2: Atomicity Mechanisms Unspecified

**Issue**: Spec requires certificate updates/removals but doesn't specify atomicity mechanisms.

**Missing Requirements**:
- Transaction semantics (all-or-nothing)
- Rollback procedures on failure
- Power-loss recovery guarantees

**Impact**: Implementations may have inconsistent states after failures.

---

### Gap 3: Client Certificate Time Validation

**Issue**: Spec mandates time validation for certificates but doesn't explicitly require validation at provisioning time for client certificates (only during TLS handshake).

**Missing Requirement**: "Client certificates SHALL be time-validated at provisioning (notBefore ≤ current_time ≤ notAfter)"

**Impact**: Expired certificates could be provisioned, causing immediate handshake failures.

---

### Gap 4: Nonce Reuse Prevention

**Issue**: Spec requires nonce generation but doesn't explicitly forbid nonce reuse.

**Missing Requirement**: "Nonces SHALL NOT be reused. Implementations SHALL maintain history of used nonces or use sufficient entropy to ensure uniqueness."

**Impact**: Weak implementations might reuse nonces, enabling replay attacks.

---

## Appendix C: Analysis Methodology Notes

### Assumptions Made

1. **FSM Correctness**: Assumed FSM accurately represents specification intent
2. **Function Implementations**: Assumed functions like `Crypto_DRBG()` are correctly implemented
3. **External Dependencies**: Assumed Time Synchronization cluster works correctly
4. **Cryptographic Primitives**: Assumed ECDSA, PKCS#10 verification are secure

### Limitations

1. **Abstraction Level**: FSM abstracts implementation details (storage, atomicity, timing)
2. **Probabilistic Properties**: Cannot verify statistical properties (e.g., DRBG collision probability)
3. **Cross-Cluster Dependencies**: Cannot verify properties spanning multiple clusters
4. **Runtime Behavior**: Cannot verify dynamic properties like performance or availability

### Tools That Could Help

1. **Model Checker**: TLA+, SPIN could verify state space exhaustively
2. **Theorem Prover**: Coq, Isabelle could prove properties formally
3. **ProVerif**: Automatic verification of cryptographic protocols
4. **Fault Injection**: Test atomicity and failure recovery

---

## Conclusion

This analysis identified **3 critical FSM violations** and **3 partial violations** across 30 analyzed properties:

**Most Critical Issues**:
1. **Missing Fabric Isolation** - Enables multi-tenancy boundary violations
2. **Missing CCDID Consistency Guard** - Enables certificate/key mismatch
3. **Incomplete Time Validation** - Client certificates not validated at provisioning

**Key Recommendations**:
1. Add Fabric context to all certificate/endpoint operations
2. Add CCDID consistency checking between CSR response and provisioning
3. Add explicit time validation for client certificates
4. Consider adding defense-in-depth nonce uniqueness tracking
5. Add certificate chain completeness verification

**Assessment**: The FSM correctly models most security-critical properties but has significant gaps in:
- Multi-tenancy isolation (Fabric boundaries)
- Cross-step consistency enforcement (CCDID matching)
- Complete validation coverage (client cert time validation)

These gaps should be addressed before deployment in multi-tenant environments.

---

**Analysis Complete**: 2026-02-13  
**Analyzed By**: GitHub Copilot (Claude Sonnet 4.5)  
**Total Properties Examined**: 30 of 41  
**Total Violations Found**: 6 (3 full violations, 3 partial)

## Summary of Violations Found

### Critical Violations

1. **PROP_026: Fabric_Isolation_For_Certificates** - 🔴 VIOLATED
   - **Issue**: FSM does not model Fabric context
   - **Impact**: Certificates from one Fabric could be used in another Fabric
   - **Severity**: CRITICAL - Breaks multi-tenancy isolation

2. **PROP_034: Endpoint_Fabric_Association** - 🔴 VIOLATED  
   - **Issue**: Endpoints not associated with specific Fabric in FSM
   - **Impact**: Endpoint provisioned in Fabric A could be used in Fabric B
   - **Severity**: CRITICAL - Same root cause as PROP_026

3. **PROP_016: Certificate_Provisioning_Uses_Returned_CCDID** - 🔴 VIOLATED
   - **Issue**: No guard enforcing provisioning uses CCDID from CSRResponse
   - **Impact**: Certificate/key mismatch if wrong CCDID used
   - **Severity**: HIGH - Authentication failure

### Partial Violations / Weaknesses

4. **PROP_009: Nonce_Uniqueness_Per_CSR** - ⚠️ PARTIALLY_HOLDS
   - **Issue**: No explicit uniqueness tracking (relies on DRBG probability)
   - **Impact**: Replay attacks if DRBG compromised
   - **Severity**: MEDIUM - Very low probability but lacks defense-in-depth

5. **PROP_027: Time_Validation_For_Certificate_Validity** - ⚠️ PARTIALLY_HOLDS
   - **Issue**: Time validation present for Root CA but not explicit for Client Certificates
   - **Impact**: Expired client certificates could be provisioned
   - **Severity**: HIGH - Operational failure or security gap

6. **PROP_031: Certificate_Chain_Completeness** - ⚠️ PARTIALLY_HOLDS
   - **Issue**: Chain completeness not verified against provisioned Root CA
   - **Impact**: Incomplete chain causes TLS handshake failure
   - **Severity**: MEDIUM - Operational issue

### Unverifiable Properties (FSM Abstraction Limitations)

7. **PROP_001: TLS_Client_Only_Enforcement** - ⚠️ UNVERIFIABLE
   - FSM assumes client-only but doesn't model rejection of server connections

8. **PROP_028: Atomicity_Of_Certificate_Update** - ⚠️ UNVERIFIABLE
   - FSM abstracts atomicity; can't verify transaction implementation

9. **PROP_029: Atomicity_Of_Certificate_Removal** - ⚠️ UNVERIFIABLE
   - Same issue - atomicity claimed but mechanism unspecified

10. **PROP_025: Server_Authentication_Via_Root_CA** - ⚠️ UNVERIFIABLE
    - TLS handshake details abstracted in FSM

11. **PROP_019/020: Storage Minimums** - ⚠️ UNVERIFIABLE
    - Capacity constraints not modeled in state machine

---

