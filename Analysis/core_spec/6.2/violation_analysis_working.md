# Property Violation Analysis - Working Document

## Analysis Methodology

For each property:
1. **Identify Critical FSM Transitions** - Which transitions enforce/violate this property?
2. **Check Guards** - Are guards sufficient to prevent violation?
3. **Check Actions** - Do actions properly enforce the property?
4. **Identify Attack Paths** - Can attacker reach violation state?
5. **Cite Specification** - Exact quotes supporting verdict

---

## CRITICAL Properties Analysis

### PROP_001: DAC_Uniqueness_Per_Device

**Property Claim**: Each commissionable Matter Node SHALL include a unique Device Attestation Certificate and corresponding private key.

**FSM Analysis**:
- **Relevant Transitions**: None directly enforce this - it's a manufacturing/provisioning property
- **Attack Path**: N/A - outside FSM scope
- **Verdict**: UNVERIFIABLE from FSM alone - property must be enforced during device manufacturing/provisioning before entering Unattested state

**Status**: UNVERIFIABLE (manufacturing constraint, not runtime)

---

### PROP_002: DAC_X509v3_DER_Encoding

**Property Claim**: The DAC SHALL be a DER-encoded X.509v3-compliant certificate as defined in RFC 5280.

**FSM Analysis**:
- **Critical Transition**: SignatureValidated → CertificateFormatValidated
  - Guard: `validate_dac_format() == true && validate_pai_format() == true && validate_paa_format() == true`
  - Function: validate_dac_format() checks "X.509v3 version, DER encoding, RFC 5280 compliance"
  
- **Attack Path Analysis**: Cannot proceed past CertificateFormatValidated without passing validate_dac_format()
  
**Verdict**: HOLDS - FSM enforces this check

**Specification Evidence**:
```
Section 6.2.2: "The DAC SHALL be a DER-encoded X.509v3-compliant certificate as defined in RFC 5280"
```

**Status**: HOLDS

---

### PROP_003: Certification_Path_Length_Exactly_Two

**Property Claim**: The DAC SHALL be issued by a PAI that chains directly to an approved PAA, resulting in a certification path length of exactly 2.

**FSM Analysis**:
- **Critical Transition**: CertificateFormatValidated → ChainCryptographicallyValidated
  - Guard: `crypto_verify_chain_der(...) == SUCCESS && verify_issuer_subject_matches() == true && path_length == 2`
  - Explicit check: `path_length == 2`
  
- **Attack Path Analysis**: Cannot proceed without path_length == 2
  
**Verdict**: HOLDS - FSM enforces exact path length

**Specification Evidence**:
```
Section 6.2.2: "SHALL be issued by a Product Attestation Intermediate (PAI) that chains directly to an approved Product Attestation Authority (PAA), and therefore SHALL have a certification path length of 2"
```

**Status**: HOLDS

---

### PROP_004: Cryptographic_Algorithm_Binding

**Property Claim**: All certificates SHALL use ECDSA with SHA256 signature algorithm and prime256v1 (secp256r1) elliptic curve.

**FSM Analysis**:
- **Critical Transition**: SignatureValidated → CertificateFormatValidated
  - Function: validate_dac_format() definition states: "Validates DAC certificate structure and constraints: X.509v3 version, DER encoding, RFC 5280 compliance, signature algorithm (ECDSA-SHA256), elliptic curve (prime256v1/secp256r1), subject/issuer field structure"
  
- **Attack Path Analysis**: Cannot proceed without algorithm validation in validate_dac_format()
  
**Verdict**: HOLDS - FSM enforces algorithm requirements

**Specification Evidence**:
```
Section 6.2.1: "This chapter refers to the signature algorithm ECDSA with SHA256 and to the elliptic curve secp256r1 (a.k.a. prime256v1 and NIST P-256)"
```

**Status**: HOLDS

---

### PROP_005: VendorID_ProductID_Presence_In_DAC

**Property Claim**: The DAC SHALL contain specific values of Vendor ID and Product ID in its subject field.

**FSM Analysis**:
- **Critical Transitions**: 
  1. RevocationChecked → VendorIDPolicyValidated (calls extract_vid())
  2. VendorIDPolicyValidated → ProductIDPolicyValidated (calls extract_pid())
  
- **Checking extract_vid/extract_pid requirements**: These functions extract VID/PID from DAC subject
- **Problem**: FSM doesn't explicitly fail if VID/PID are ABSENT, only checks consistency if present

**Attack Path Analysis**:
- What if DAC has no VID/PID at all?
- extract_vid() would return null/undefined
- Guards check equality, not presence: `extract_vid(dac) == extract_vid(pai)`
- If both are null, this passes!

**Verdict**: POTENTIALLY VIOLATED - FSM may not fail if VID/PID are completely absent

**Specification Evidence**:
```
"The DAC also SHALL contain specific values of Vendor ID and Product ID... in its subject field"
```

**Status**: HOLDS - validate_dac_format() checks "subject sequence with exactly one VID and one PID"

---

### PROP_008: PAI_VendorID_Assignment

**Property Claim**: A PAI SHALL be assigned to a Vendor ID value and cannot be shared across vendors.

**FSM Analysis**:
- **Critical Transition**: RevocationChecked → VendorIDPolicyValidated
  - Guard: `extract_vid(dac_certificate) == extract_vid(pai_certificate)`
  - Enforces VID consistency
  
**Verdict**: HOLDS - FSM enforces VID matching between DAC and PAI

**Status**: HOLDS

---

### PROP_047: Revocation_Set_Availability_Warning

**Property Claim**: If revocation set is unavailable, Commissioner SHOULD notify user that commissioning could succeed for non-genuine devices.

**FSM Analysis**:
- **Critical Transition**: PAAValidated → RevocationCheckSkipped
  - Guard: `revocation_data_available == false`
  - Actions include: `notify_user('revocation_check_bypassed')`
  
**Verdict**: HOLDS - User notification is present

**Specification Evidence**:
```
Section 6.2.4.2: "If revocation set unavailable... Commissioner SHOULD notify user"
```

**Status**: HOLDS

---

### PROP_048: Stale_CRL_Warning  

**Property Claim**: If CRL is stale, Commissioner MAY proceed and SHOULD notify user of potential risk.

**FSM Analysis**:
- **Critical Transition**: PAAValidated → CRLStaleWarning
  - Guard: `revocation_data_available == true && crl_is_stale() == true && no_revocations_found() == true`
  - Actions include: `notify_user('crl_stale_warning')`
  
**Verdict**: HOLDS - User notification is present

**Specification Evidence**:
```
Section 6.2.4.2: "If no updated CRL available beyond nextUpdate... Commissioner MAY assume no updated revocation information... SHOULD notify user"
```

**Status**: HOLDS

---

## Checking for Potential Violations

### Analysis Focus: Looking for properties where FSM lacks enforcement

Let me systematically check all CRITICAL properties:

#### Properties That HOLD (with FSM evidence)

1. **PROP_002** (DAC_X509v3_DER_Encoding) - HOLDS
   - FSM validates via validate_dac_format()
   
2. **PROP_003** (Certification_Path_Length_Exactly_Two) - HOLDS
   - FSM explicitly checks `path_length == 2` in guard

3. **PROP_004** (Cryptographic_Algorithm_Binding) - HOLDS
   - FSM validates in validate_*_format() functions

4. **PROP_008** (PAI_VendorID_Assignment) - HOLDS
   - FSM checks VID consistency

5. **PROP_010** (DAC_Issuer_Matches_PAI_Subject) - HOLDS
   - FSM calls verify_issuer_subject_matches()

6. **PROP_021** (Attestation_Nonce_Fresh_Random_32_Bytes) - HOLDS
   - FSM calls generate_random_nonce() with length check

7. **PROP_022** (Attestation_Nonce_Match_In_Response) - HOLDS
   - FSM checks `extract_nonce(attestation_elements) == attestation_nonce`

8. **PROP_023** (Attestation_Signature_Cryptographic_Verification) - HOLDS
   - FSM calls crypto_verify()

9. **PROP_024** (Certificate_Chain_Validation_With_Revocation) - HOLDS
   - FSM calls crypto_verify_chain_der() and has revocation checks

10. **PROP_026** (PAA_In_Trusted_Root_Store) - HOLDS
    - FSM checks both paa_in_trusted_store() and paa_in_dcl_at_time()

11. **PROP_027** (VendorID_Consistency_Across_Chain) - HOLDS
    - FSM validates VID matching in VendorIDPolicyValidated transition

12. **PROP_028** (Certification_Declaration_VendorID_Match) - HOLDS
    - FSM calls cd_vid_matches_basic_info()

13. **PROP_029** (Certification_Declaration_ProductID_Containment) - HOLDS
    - FSM calls cd_pid_in_array()

14. **PROP_032** (DAC_Without_Origin_Standard_VID_PID_Validation) - HOLDS
    - FSM calls validate_dac_origin_fields()

15. **PROP_041** (DAC_Issuer_Matches_PAI_Subject_Byte_For_Byte) - HOLDS
    - FSM calls verify_issuer_subject_matches() which checks byte-for-byte

16. **PROP_042** (PAI_Issuer_Matches_PAA_Subject_Byte_For_Byte) - HOLDS
    - Same as above

17. **PROP_050** (CRL_Signer_Certificate_Validation) - HOLDS
    - FSM's is_revoked() function handles CRL signer validation (per definition)

18. **PROP_056** (Commissioner_Holds_Private_Key_Proof) - HOLDS
    - FSM verifies attestation signature proving key possession

19. **PROP_057** (AttestationChallenge_From_Secure_Session) - HOLDS
    - FSM checks `extract_challenge(attestation_elements) == get_session_challenge(commissioning_session)`

#### Properties That Are UNVERIFIABLE (device/manufacturing constraints, not runtime)

1. **PROP_001** (DAC_Uniqueness_Per_Device) - UNVERIFIABLE
   - Requires checking across all devices, manufacturing constraint

2. **PROP_058** (DAC_Uniqueness_Requirement_Enforced) - UNVERIFIABLE
   - Same as PROP_001, subject uniqueness per RFC 5280 is manufacturing constraint

3. **PROP_059** (Private_Key_Confidentiality) - UNVERIFIABLE
   - Device implementation detail, not runtime verifiable

4. **PROP_062** (Immutable_Credentials) - UNVERIFIABLE
   - Device firmware/hardware constraint, not runtime verifiable

#### Properties To Investigate Further

Let me now look for possible gaps...

---

### Deep Dive: Potential Violations

#### Checking PROP_060: Certificate_Size_Constraints

**Property Claim**: Certificate format is constrained to maximum sizes to reduce complexity

**FSM Analysis**:
- Searching for size checks in validate_*_format() functions...
- Function definitions say: "Check DAC constraints per Section 6.2.2.3" but don't explicitly mention SIZE limits
- **Question**: Does the FSM check certificate size limits?

Let me check the spec for explicit size requirements...

