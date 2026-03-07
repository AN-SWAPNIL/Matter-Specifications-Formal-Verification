# TLS Certificate Management Cluster FSM Analysis

## State-Defining Attributes

### Root Certificate State Variables (Per CAID)
- **exists**: boolean (certificate entry exists in ProvisionedRootCertificates)
- **caid**: TLSCAID (0 to 65534)
- **certificate**: octstr (DER-encoded certificate, max 3000 bytes)
- **fingerprint**: octstr (derived from certificate)
- **associated_fabric**: fabric_id
- **referenced_by_endpoint**: boolean (exists in TLS Client Management Cluster ProvisionedEndpoints)

### Client Certificate State Variables (Per CCDID)
- **exists**: boolean (entry exists in ProvisionedClientCertificates)
- **ccdid**: TLSCCDID (0 to 65534)
- **key_pair_generated**: boolean (TLS key pair exists)
- **client_certificate**: octstr or NULL (DER-encoded, max 3000 bytes)
- **intermediate_certificates**: list[octstr] (0 to 10, each max 3000 bytes)
- **fingerprint**: octstr or NULL (derived from client_certificate if non-NULL)
- **associated_fabric**: fabric_id
- **referenced_by_endpoint**: boolean (exists in TLS Client Management Cluster ProvisionedEndpoints)

### Global State Variables
- **UTCTime**: timestamp or NULL (from Time Synchronization cluster)
- **provisioned_root_cert_count_per_fabric**: map[fabric_id -> count]
- **provisioned_client_cert_count_per_fabric**: map[fabric_id -> count]
- **MaxRootCertificates**: uint8 (5 to 254)
- **MaxClientCertificates**: uint8 (2 to 254)

---

## States for Root Certificate Lifecycle

### RootCert_NotProvisioned
- **Invariants**: exists == false
- **Description**: No certificate entry exists for this CAID

### RootCert_Provisioned_NotReferenced
- **Invariants**: exists == true, referenced_by_endpoint == false
- **Description**: Certificate provisioned but not used by any TLS endpoint

### RootCert_Provisioned_Referenced
- **Invariants**: exists == true, referenced_by_endpoint == true
- **Description**: Certificate provisioned and in use by at least one TLS endpoint (cannot be removed)

---

## States for Client Certificate Lifecycle

### ClientCert_NotProvisioned
- **Invariants**: exists == false, key_pair_generated == false
- **Description**: No certificate entry, no key pair

### ClientCert_KeyGenerated_CertPending
- **Invariants**: exists == true, key_pair_generated == true, client_certificate == NULL
- **Description**: Key pair generated via ClientCSR, awaiting ProvisionClientCertificate

### ClientCert_Provisioned_NotReferenced
- **Invariants**: exists == true, key_pair_generated == true, client_certificate != NULL, referenced_by_endpoint == false
- **Description**: Full certificate chain provisioned, not used by endpoints

### ClientCert_Provisioned_Referenced
- **Invariants**: exists == true, key_pair_generated == true, client_certificate != NULL, referenced_by_endpoint == true
- **Description**: Certificate in use by at least one TLS endpoint (cannot be removed)

---

## Command Analysis with Transitions

### 1. ProvisionRootCertificate Command

**Inputs**: Certificate (octstr), CAID (TLSCAID or NULL)

**Guard Conditions & Transitions**:

#### Transition Set 1: Precondition Failures (Stay in current state)
- **Guard**: `UTCTime == NULL`
  - **Action**: Return INVALID_IN_STATE
  - **From**: Any state
  - **To**: Same state

- **Guard**: `is_invalid_tls_certificate(Certificate)`
  - **Action**: Return DYNAMIC_CONSTRAINT_ERROR
  - **From**: Any state
  - **To**: Same state

- **Guard**: `fingerprint_exists_in_fabric(fingerprint(Certificate), accessing_fabric) && CAID == NULL`
  - **Action**: Return ALREADY_EXISTS
  - **From**: Any state
  - **To**: Same state

#### Transition Set 2: New Certificate Provisioning (CAID == NULL)
- **Guard**: `CAID == NULL && count_root_certs(accessing_fabric) == MaxRootCertificates`
  - **Action**: Return RESOURCE_EXHAUSTED
  - **From**: RootCert_NotProvisioned
  - **To**: RootCert_NotProvisioned

- **Guard**: `CAID == NULL && count_root_certs(accessing_fabric) < MaxRootCertificates && UTCTime != NULL && is_valid_tls_certificate(Certificate) && !fingerprint_exists_in_fabric(fingerprint(Certificate), accessing_fabric)`
  - **Actions**: 
    - `new_caid := generate_unique_tlscaid()`
    - `create_tlscertstruct(new_caid, Certificate, accessing_fabric)`
    - `add_to_provisioned_root_certificates(new_tlscertstruct)`
    - `increment_count_root_certs(accessing_fabric)`
    - `return_response(new_caid)`
  - **From**: RootCert_NotProvisioned
  - **To**: RootCert_Provisioned_NotReferenced

#### Transition Set 3: Certificate Rotation (CAID != NULL)
- **Guard**: `CAID != NULL && !exists_caid(CAID)`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CAID != NULL && exists_caid(CAID) && fabric_of_caid(CAID) != accessing_fabric`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CAID != NULL && exists_caid(CAID) && fabric_of_caid(CAID) == accessing_fabric && UTCTime != NULL && is_valid_tls_certificate(Certificate) && !fingerprint_exists_in_fabric(fingerprint(Certificate), accessing_fabric)`
  - **Actions**: 
    - `update_certificate_field(CAID, Certificate)`
    - `return_response(CAID)`
  - **From**: RootCert_Provisioned_NotReferenced OR RootCert_Provisioned_Referenced
  - **To**: Same state (certificate updated but state unchanged)
  - **Note**: Spec says "updated certificate will only be used for new underlying TLS connections established after this call"

---

### 2. FindRootCertificate Command

**Inputs**: CAID (TLSCAID or NULL)

**Guard Conditions & Transitions**: (Read-only, no state changes)

- **Guard**: `count_provisioned_root_certificates() == 0`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CAID == NULL && count_root_certs(accessing_fabric) == 0`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CAID == NULL && count_root_certs(accessing_fabric) > 0`
  - **Action**: Return list of all TLSCertStruct for accessing_fabric
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CAID != NULL && !exists_caid(CAID)`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CAID != NULL && exists_caid(CAID) && fabric_of_caid(CAID) != accessing_fabric`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CAID != NULL && exists_caid(CAID) && fabric_of_caid(CAID) == accessing_fabric`
  - **Action**: Return list with single TLSCertStruct for CAID
  - **From**: Any state
  - **To**: Same state

---

### 3. LookupRootCertificate Command

**Inputs**: Fingerprint (octstr)

**Guard Conditions & Transitions**: (Read-only)

- **Guard**: `count_provisioned_root_certificates() == 0`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `!exists_fingerprint(Fingerprint) || fabric_of_fingerprint(Fingerprint) != accessing_fabric`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_fingerprint(Fingerprint) && fabric_of_fingerprint(Fingerprint) == accessing_fabric`
  - **Action**: Return CAID of matching entry
  - **From**: Any state
  - **To**: Same state

---

### 4. RemoveRootCertificate Command

**Inputs**: CAID (TLSCAID)

**Guard Conditions & Transitions**:

- **Guard**: `count_provisioned_root_certificates() == 0`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `!exists_caid(CAID)`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_caid(CAID) && fabric_of_caid(CAID) != accessing_fabric`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_caid(CAID) && fabric_of_caid(CAID) == accessing_fabric && referenced_by_endpoint(CAID)`
  - **Action**: Return INVALID_IN_STATE
  - **From**: RootCert_Provisioned_Referenced
  - **To**: RootCert_Provisioned_Referenced

- **Guard**: `exists_caid(CAID) && fabric_of_caid(CAID) == accessing_fabric && !referenced_by_endpoint(CAID)`
  - **Actions**: 
    - `remove_entry(CAID)`
    - `decrement_count_root_certs(accessing_fabric)`
    - `return_success()`
  - **From**: RootCert_Provisioned_NotReferenced
  - **To**: RootCert_NotProvisioned

---

### 5. ClientCSR Command

**Inputs**: Nonce (octstr, 32 bytes), CCDID (TLSCCDID or NULL)

**Guard Conditions & Transitions**:

#### Transition Set 1: New Key Pair Generation (CCDID == NULL)
- **Guard**: `CCDID == NULL && count_client_certs(accessing_fabric) == MaxClientCertificates`
  - **Action**: Return RESOURCE_EXHAUSTED
  - **From**: ClientCert_NotProvisioned
  - **To**: ClientCert_NotProvisioned

- **Guard**: `CCDID == NULL && count_client_certs(accessing_fabric) < MaxClientCertificates`
  - **Sub-transitions based on key collision**:
    - **Guard**: `CCDID == NULL && count_client_certs(accessing_fabric) < MaxClientCertificates && key_collision_detected(new_keypair)`
      - **Actions**: 
        - `new_keypair := crypto_generate_keypair()`
        - `discard_keypair(new_keypair)`
      - **Action**: Return DYNAMIC_CONSTRAINT_ERROR
      - **From**: ClientCert_NotProvisioned
      - **To**: ClientCert_NotProvisioned
    
    - **Guard**: `CCDID == NULL && count_client_certs(accessing_fabric) < MaxClientCertificates && !key_collision_detected(new_keypair)`
      - **Actions**: 
        - `new_keypair := crypto_generate_keypair()`
        - `new_ccdid := generate_unique_tlsccdid()`
        - `create_tlsclientcertdetailstruct(new_ccdid, accessing_fabric)`
        - `associate_keypair(new_ccdid, new_keypair)`
        - `set_client_certificate_null(new_ccdid)`
        - `set_intermediate_certificates_null(new_ccdid)`
        - `add_to_provisioned_client_certificates(new_tlsclientcertdetailstruct)`
        - `increment_count_client_certs(accessing_fabric)`
        - `tls_csr := generate_pkcs10_csr(new_keypair)`
        - `nonce_signature := crypto_sign(Nonce, private_key(new_keypair))`
        - `return_response(new_ccdid, tls_csr, nonce_signature)`
      - **From**: ClientCert_NotProvisioned
      - **To**: ClientCert_KeyGenerated_CertPending

#### Transition Set 2: Key Pair Reuse for Rotation (CCDID != NULL)
- **Guard**: `CCDID != NULL && !exists_ccdid(CCDID)`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CCDID != NULL && exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) != accessing_fabric`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `CCDID != NULL && exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) == accessing_fabric`
  - **Actions**: 
    - `existing_keypair := get_keypair(CCDID)`
    - `tls_csr := generate_pkcs10_csr(existing_keypair)`
    - `nonce_signature := crypto_sign(Nonce, private_key(existing_keypair))`
    - `return_response(CCDID, tls_csr, nonce_signature)`
  - **From**: ClientCert_KeyGenerated_CertPending OR ClientCert_Provisioned_NotReferenced OR ClientCert_Provisioned_Referenced
  - **To**: Same state (CSR generated but state unchanged)

---

### 6. ProvisionClientCertificate Command

**Inputs**: CCDID (TLSCCDID), ClientCertificate (octstr), IntermediateCertificates (list[octstr])

**Guard Conditions & Transitions**:

- **Guard**: `count_provisioned_client_certificates() == 0`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `fingerprint_exists_in_fabric(fingerprint(ClientCertificate), accessing_fabric)`
  - **Action**: Return ALREADY_EXISTS
  - **From**: Any state
  - **To**: Same state

- **Guard**: `!exists_ccdid(CCDID)`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) != accessing_fabric`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) == accessing_fabric && (is_invalid_tls_certificate(ClientCertificate) || any_invalid_in_list(IntermediateCertificates))`
  - **Action**: Return DYNAMIC_CONSTRAINT_ERROR
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) == accessing_fabric && !public_private_key_correspondence(ClientCertificate, get_private_key(CCDID))`
  - **Action**: Return DYNAMIC_CONSTRAINT_ERROR
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) == accessing_fabric && is_valid_tls_certificate(ClientCertificate) && all_valid_in_list(IntermediateCertificates) && public_private_key_correspondence(ClientCertificate, get_private_key(CCDID)) && !fingerprint_exists_in_fabric(fingerprint(ClientCertificate), accessing_fabric)`
  - **Actions**: 
    - `update_client_certificate_field(CCDID, ClientCertificate)`
    - `update_intermediate_certificates_field(CCDID, IntermediateCertificates)`
    - `return_success()`
  - **From**: ClientCert_KeyGenerated_CertPending
  - **To**: ClientCert_Provisioned_NotReferenced
  - **Note**: Can also be used for rotation from ClientCert_Provisioned_* states

---

### 7. FindClientCertificate Command

**Inputs**: CCDID (TLSCCDID or NULL)

**Guard Conditions & Transitions**: (Read-only)

Similar structure to FindRootCertificate, returns TLSClientCertificateDetailStruct entries.

---

### 8. LookupClientCertificate Command

**Inputs**: Fingerprint (octstr)

**Guard Conditions & Transitions**: (Read-only)

Similar structure to LookupRootCertificate, returns CCDID for given fingerprint.

---

### 9. RemoveClientCertificate Command

**Inputs**: CCDID (TLSCCDID)

**Guard Conditions & Transitions**:

- **Guard**: `count_provisioned_client_certificates() == 0`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `!exists_ccdid(CCDID)`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) != accessing_fabric`
  - **Action**: Return NOT_FOUND
  - **From**: Any state
  - **To**: Same state

- **Guard**: `exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) == accessing_fabric && referenced_by_endpoint(CCDID)`
  - **Action**: Return INVALID_IN_STATE
  - **From**: ClientCert_Provisioned_Referenced
  - **To**: ClientCert_Provisioned_Referenced

- **Guard**: `exists_ccdid(CCDID) && fabric_of_ccdid(CCDID) == accessing_fabric && !referenced_by_endpoint(CCDID)`
  - **Actions**: 
    - `remove_entry(CCDID)`
    - `remove_tls_keypair(CCDID)`
    - `decrement_count_client_certs(accessing_fabric)`
    - `return_success()`
  - **From**: ClientCert_KeyGenerated_CertPending OR ClientCert_Provisioned_NotReferenced
  - **To**: ClientCert_NotProvisioned

---

## Functions Required

### Cryptographic Functions
1. **crypto_generate_keypair()**: Generate new TLS key pair (ECDSA)
2. **crypto_sign(message, private_key)**: ECDSA signature generation
3. **generate_pkcs10_csr(keypair)**: Generate PKCS#10 CSR with signature
4. **fingerprint(certificate)**: Compute certificate fingerprint (hash)
5. **public_private_key_correspondence(certificate, private_key)**: Verify public key in cert matches private key

### Validation Functions
6. **is_valid_tls_certificate(cert)**: Validate DER-encoded TLS certificate
7. **is_invalid_tls_certificate(cert)**: Negation of above
8. **any_invalid_in_list(cert_list)**: Check if any cert in list is invalid
9. **all_valid_in_list(cert_list)**: Check if all certs in list are valid
10. **key_collision_detected(keypair)**: Check if keypair collides with existing TLS or operational credential keys

### ID Generation Functions
11. **generate_unique_tlscaid()**: Generate unique TLSCAID (0-65534) with collision detection
12. **generate_unique_tlsccdid()**: Generate unique TLSCCDID (0-65534) with collision detection

### State Query Functions
13. **exists_caid(caid)**: Check if CAID exists in ProvisionedRootCertificates
14. **exists_ccdid(ccdid)**: Check if CCDID exists in ProvisionedClientCertificates
15. **fabric_of_caid(caid)**: Get associated fabric for CAID
16. **fabric_of_ccdid(ccdid)**: Get associated fabric for CCDID
17. **referenced_by_endpoint(id)**: Check if CAID/CCDID referenced in TLS Client Management Cluster
18. **fingerprint_exists_in_fabric(fingerprint, fabric)**: Check if fingerprint exists for fabric
19. **fabric_of_fingerprint(fingerprint)**: Get associated fabric for fingerprint
20. **count_root_certs(fabric)**: Count root certificates for fabric
21. **count_client_certs(fabric)**: Count client certificates for fabric
22. **count_provisioned_root_certificates()**: Total count across all fabrics
23. **count_provisioned_client_certificates()**: Total count across all fabrics

### Mutation Functions
24. **create_tlscertstruct(caid, certificate, fabric)**: Create new TLSCertStruct entry
25. **add_to_provisioned_root_certificates(struct)**: Add to list
26. **update_certificate_field(caid, certificate)**: Update certificate in existing entry
27. **remove_entry(id)**: Remove entry from list
28. **create_tlsclientcertdetailstruct(ccdid, fabric)**: Create new TLSClientCertificateDetailStruct
29. **associate_keypair(ccdid, keypair)**: Associate key pair with CCDID
30. **set_client_certificate_null(ccdid)**: Set ClientCertificate field to NULL
31. **set_intermediate_certificates_null(ccdid)**: Set IntermediateCertificates field to NULL
32. **add_to_provisioned_client_certificates(struct)**: Add to list
33. **update_client_certificate_field(ccdid, certificate)**: Update client certificate
34. **update_intermediate_certificates_field(ccdid, cert_list)**: Update intermediate certificates
35. **remove_tls_keypair(ccdid)**: Securely delete TLS key pair
36. **get_keypair(ccdid)**: Retrieve key pair for CCDID
37. **get_private_key(ccdid)**: Retrieve private key for CCDID
38. **private_key(keypair)**: Extract private key from keypair
39. **increment_count_root_certs(fabric)**: Increment counter
40. **decrement_count_root_certs(fabric)**: Decrement counter
41. **increment_count_client_certs(fabric)**: Increment counter
42. **decrement_count_client_certs(fabric)**: Decrement counter

### Response Functions
43. **return_response(caid)**: Return ProvisionRootCertificateResponse
44. **return_success()**: Return SUCCESS status
45. **discard_keypair(keypair)**: Discard generated keypair on collision

---

## Security Properties

1. **Fabric Isolation**: All operations enforce accessing_fabric == associated_fabric
2. **Reference Integrity**: Cannot remove certificates referenced by endpoints (INVALID_IN_STATE)
3. **Key Collision Prevention**: Reject new key pairs that collide with existing keys
4. **Public-Private Key Correspondence**: Client certificate public key must match stored private key
5. **Fingerprint Uniqueness**: No duplicate fingerprints within a fabric
6. **Time Synchronization Requirement**: UTCTime must be non-NULL for root certificate provisioning
7. **Resource Exhaustion Prevention**: Enforce MaxRootCertificates and MaxClientCertificates limits
8. **Private Key Cleanup**: Remove private key when removing client certificate
9. **Certificate Rotation Isolation**: Updated certificates only affect new TLS connections

---

## Cryptographic Operations

1. **Key Pair Generation**: ECDSA key pair using Crypto_GenerateKeypair
2. **CSR Generation**: PKCS#10 format with ECDSA signature (RFC 2986 section 4.2)
3. **Nonce Signature**: ECDSA signature of nonce using TLS private key
4. **Certificate Fingerprint**: Hash-based fingerprint (algorithm not specified, likely SHA-256)
5. **Certificate Validation**: DER decoding and TLS certificate format validation
6. **Public-Private Key Verification**: Verify certificate's subjectPublicKey corresponds to private key

---

## Security Assumptions

1. **Time Synchronization Cluster**: Provides accurate UTCTime before certificate operations
2. **TLS Client Management Cluster**: Enforces referential integrity with CAID/CCDID
3. **Fabric Identity Authentication**: Accessing fabric identity cannot be spoofed
4. **Crypto Primitives Security**: ECDSA, key generation, and signature verification are secure
5. **Memory Protection**: Private keys stored securely and erased on deletion
6. **DRBG Entropy**: Sufficient entropy for key generation without predictable outputs
7. **Admin Privilege Enforcement**: Commands with 'A' access modifier enforce admin privilege
8. **Certificate Authority**: External CA properly validates CSRs and issues correct certificates
