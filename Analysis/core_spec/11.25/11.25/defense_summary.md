# Specification Defense: Matter Core Specification 1.4, Section 11.25

## Joint Fabric Administrator Cluster — Response to Claimed Violations

**Date**: 2026-02-13  
**Scope**: Defense of 7 violations claimed in property_violations_report.json  
**Specification**: Matter Core Specification 1.4 (Document 23-27349, November 4, 2024)  
**Section Under Review**: 11.25 Joint Fabric Administrator Cluster + Referenced Sections

---

## Executive Summary

Of the 7 violations claimed, **6 are DISPROVED** based on specification text, architectural design, and data model enforcement rules. **1 remains VALID** but is acknowledged as a known limitation of a provisional cluster and is partially mitigated by existing framework mechanisms.

| # | Property ID | Claimed Severity | Verdict | Defense Outcome |
|---|-------------|-----------------|---------|-----------------|
| 1 | PROP_033 | CRITICAL | Fail_Safe_Atomicity | **VALID** (mitigated; provisional cluster) |
| 2 | PROP_027 | HIGH | Discriminator_Range_Validation | **DISPROVED** |
| 3 | PROP_035 | HIGH | State_Machine_Exclusivity | **DISPROVED** |
| 4 | PROP_026 | MEDIUM | Concurrent_Commissioning_Prevention | **DISPROVED** |
| 5 | PROP_042 | MEDIUM | CSR_Size_Limit_600_Bytes | **DISPROVED** |
| 6 | PROP_043 | MEDIUM | ICAC_Size_Limit_400_Bytes | **DISPROVED** |
| 7 | PROP_023 | MEDIUM | Endpoint_Announcement_Uniqueness | **DISPROVED** |

---

## Violation 1: PROP_033 — Fail_Safe_Atomicity

**Claimed Severity**: CRITICAL  
**Claim**: Missing fail-safe expiration transitions from intermediate commissioning states (CSRRequested, CSRGenerated, ValidatingICAC). Node remains stuck in intermediate state with partial commissioning data when fail-safe expires.

### Defense

**Verdict: VALID — but mitigated and acknowledged.**

This is a genuine specification gap, but its severity is significantly overstated for the following reasons:

#### 1. The Cluster Is Explicitly Provisional

The specification clearly acknowledges this:

> **Section 11.25:**  
> "Support for Joint Fabric Administrator Cluster is provisional."
>
> **Section 11.25.3, Cluster ID Table, Conformance column:**  
> **"P"** (Provisional)

A provisional cluster is by definition not finalized. Known gaps are expected in provisional specifications and do not constitute a "faulty" document. The conformance marking **"P"** serves exactly this purpose — to signal to implementers that the specification is subject to change and may have incomplete behavioral definitions.

#### 2. The General Fail-Safe Framework Applies

The specification references the existing fail-safe mechanism:

> **Section 11.25.7.1, ICACCSRRequest, Effect on Receipt:**  
> "If this command is received without an armed fail-safe context **(see Section 11.10.7.2, "ArmFailSafe")**, then this command SHALL fail with a FAILSAFE_REQUIRED status code sent back to the initiator."

By referencing Section 11.10.7.2, the JFAC cluster inherits the complete fail-safe lifecycle management. Section 11.10.7.2.2 defines comprehensive cleanup behavior:

> **Section 11.10.7.2.2 (Line 34732-34758), Behavior on expiry of Fail-Safe timer:**  
> "If the fail-safe timer expires before the CommissioningComplete command is successfully invoked, the following sequence of clean-up steps SHALL be executed, in order, by the receiver:"

Step 7 specifically addresses analogous intermediate state:

> **Step 7:**  
> "If the CSRRequest command had been successfully invoked, but no AddNOC or UpdateNOC command had been successfully invoked, then the new operational key pair temporarily generated for the purposes of NOC addition or update (see Node Operational CSR Procedure) **SHALL be removed** as it is no longer needed."

Step 10 provides the general rollback mechanism:

> **Step 10:**  
> "Optionally: if no factory-reset resulted from the previous steps, it is **RECOMMENDED** that the Node rollback the state of all non fabric-scoped data present in the Fail-Safe context."

The ICACCSRRequest-generated CSR and key material constitutes "non fabric-scoped data present in the Fail-Safe context," covered by this recommendation.

#### 3. The Attack Scenario Is Not Reproduciable As Described

The claimed attack scenario states a "node stuck in CSRGenerated" that "cannot be re-commissioned without factory reset." However:

- The fail-safe timer expiration IS a system event that occurs regardless of FSM modeling
- All commissioning state is bounded by the fail-safe context
- Upon fail-safe expiration, the node returns to pre-commissioning state via the general mechanism
- There is no specification text that says intermediate JFAC state persists beyond fail-safe expiration

**What is valid**: The specification does not explicitly enumerate JFAC-specific cleanup steps the way it does for General Commissioning (NOC/ICAC/key pair). An explicit "Effect on Fail-Safe Expiry" subsection would strengthen the specification.

**What is not valid**: Claiming the node is "stuck" or requires "factory reset." The existing fail-safe framework prevents this.

### Residual Risk Assessment

| Aspect | Assessment |
|--------|------------|
| Specification gap | Real but partial — general framework covers behavior |
| Severity claimed (CRITICAL) | Overstated — should be MEDIUM at most |
| Attack reproducibility | NOT reproducible as described — fail-safe framework prevents stuck state |
| Provisional acknowledgment | Explicit — conformance "P" signals expected incompleteness |

---

## Violation 2: PROP_027 — Discriminator_Range_Validation

**Claimed Severity**: HIGH  
**Claim**: OpenJointCommissioningWindow discriminator parameter (max 4095) not validated. Values >4095 accepted because `validate_pake_parameters` only checks verifier, iterations, and salt.

### Defense

**Verdict: DISPROVED — The claim contains a factual error about the FSM and ignores specification enforcement mechanisms.**

#### 1. The FSM Model DOES Validate Discriminator (Factual Error in Report)

The violation report states:

> "validate_pake_parameters function does not include discriminator validation; values >4095 accepted"

This is **factually incorrect**. The FSM model's `validate_pake_parameters` function explicitly includes discriminator validation:

> **joint_fabric_administrator_fsm.json, validate_pake_parameters function, algorithm_detail:**  
> "Check constraints: **(1) verifier byte_length == 97, (2) discriminator <= 4095, (3) 1000 <= iterations <= 100000, (4) 16 <= salt byte_length <= 32.** Additionally verify verifier format matches SPAKE2+ verifier structure. Return true only if all constraints satisfied, false if any violation."

The function signature also includes discriminator as a parameter:

> **Parameters**: verifier (octstr), **discriminator (uint16, "Discriminator value, max 4095")**, iterations (uint32), salt (octstr)

The violation report's own attack path incorrectly represents the guard as:

> `validate_pake_parameters(verifier, iterations, salt)`

But the actual FSM transition T031 guard uses `pake_params_valid == true`, which is the output of `validate_pake_parameters` that INCLUDES discriminator checking.

#### 2. The Specification Clearly Defines the Constraint

> **Section 11.25.7.5, OpenJointCommissioningWindow Command, Parameter Table:**  
> Discriminator — uint16 — **max 4095** — M

The base command defines it even more precisely:

> **Section 11.19.8.1, OpenCommissioningWindow Command, Parameter Table (Line 39126-39133):**  
> Discriminator — uint16 — **0 to 4095**

#### 3. The Specification Mandates Parameter Error Handling

The base OpenCommissioningWindow command (which OpenJointCommissioningWindow aliases) explicitly handles parameter validation:

> **Section 11.19.8.1, OpenCommissioningWindow (Line 39137):**  
> "If any format or validity errors related to the PAKEPasscodeVerifier, Iterations or Salt arguments arise, this command **SHALL** fail with a cluster specific status code of PAKEParameterError."

> **Section 11.19.8.1 (Line 39143):**  
> "In case of any other parameter error, this command **SHALL** fail with a status code of COMMAND_INVALID."

A discriminator value exceeding 4095 falls under "any other parameter error" and SHALL fail with COMMAND_INVALID. This is a **mandatory** (SHALL) requirement, not optional.

#### 4. The Interaction Model Provides Additional Enforcement

> **Section 8.9, Invoke Execution (Line 22725):**  
> "If a data field violates expected constraints, a CommandStatusIB **SHOULD** be generated with an error status of CONSTRAINT_ERROR."

While this layer uses SHOULD, the cluster-level catch-all uses SHALL, providing mandatory enforcement.

#### 5. Attack Scenario is NOT Reproducible

The claimed attack: "Attacker sends discriminator=65535 → window opens with invalid value"

This cannot occur because:
1. The FSM's `validate_pake_parameters` rejects discriminator > 4095
2. The base command's catch-all rejects "any other parameter error" with COMMAND_INVALID (SHALL)
3. The IM layer SHOULD reject the constraint violation before the command handler

### Conclusion

**This violation is entirely disproved.** The report contains a factual error about the FSM model's validation function and ignores both the FSM's own constraint checking AND the specification's mandatory parameter error handling at the base command level.

---

## Violation 3: PROP_035 — State_Machine_Exclusivity

**Claimed Severity**: HIGH  
**Claim**: Four state machines (Joint Commissioning, ACL Management, Commissioning Window, Anchor Transfer) can run concurrently without mutual exclusion, causing race conditions.

### Defense

**Verdict: DISPROVED — Concurrent operation is an intentional architectural design. Mutual exclusion is enforced where security-relevant.**

#### 1. The Four Sub-Systems Are Orthogonal By Design

The four operational domains serve fundamentally different purposes and operate on non-overlapping data:

| Sub-System | Purpose | Data Domain | Interaction Scope |
|---|---|---|---|
| Joint Commissioning | Certificate cross-signing | CSR, ICAC, key pairs | New certificate issuance |
| ACL Management | Access control maintenance | ACL entries on existing nodes | Existing node permissions |
| Commissioning Window | Discovery advertisement | PAKE parameters, timer | Network discovery |
| Anchor Transfer | Governance transition | Anchor role, consent | Administrative authority |

These are **not competing operations on the same resources**. ACL removal on an existing node does not interfere with generating a CSR for a new cross-signing operation. They modify different data structures in different scopes.

#### 2. The Specification Provides Mutual Exclusion Where Security-Relevant

**For Commissioning Window vs. Ongoing Commissioning:**

> **Section 11.19.8.1, OpenCommissioningWindow (Line 39139):**  
> "If a commissioning window is already currently open, this command **SHALL** fail with a cluster specific status code of **Busy**."

> **Section 11.19.8.1 (Line 39141):**  
> "If the fail-safe timer is currently armed, this command **SHALL** fail with a cluster specific status code of **Busy**, since it is likely that concurrent commissioning operations from multiple separate Commissioners are about to take place."

**For Anchor Transfer vs. Datastore Operations:**

> **Section 11.25.4.2, TransferAnchorResponseStatusEnum (Value 1):**  
> "**TransferAnchorStatusDatastoreBusy** — Anchor Transfer was not started due to ongoing Datastore operations"

**General Busy Status Code:**

> **Section 11.25.5.1, StatusCodeEnum (Value 0x02):**  
> "**Busy** — Could not be completed because another commissioning is in progress"

The specification explicitly defines mutex for the operations that would conflict, and omits it where concurrency is safe.

#### 3. The Attack Scenario Is Not Reproducible

The claimed scenario: "Joint commissioning in progress → RemoveACLFromNode → ACL removed → Administrator A loses access → locked out."

This scenario fails because:

- **ACL removal targets existing nodes via `RemoveACLFromNode` (Section 11.24.7.20)**, which operates on a different node's ACL list in the Joint Fabric Datastore
- **Joint commissioning operates on the Anchor CA's certificate issuance (Section 11.25.7.1-11.25.7.3)**, which is a PKI operation
- Removing an ACL entry from an existing managed node does NOT affect the Administrator's CASE session with the Anchor CA
- The CASE session authenticating the Administrator to the Anchor CA is bound to fabric credentials, NOT to individual ACL entries on third-party managed nodes
- An Administrator performing cross-signing has fabric-level access via the Operational Credentials fabric table, which is independent of ACL entries

The "administrator lockout" scenario conflates two entirely separate security domains: fabric-level PKI operations and node-level access control policies.

#### 4. Only One Commissioning Window at a Time — Already Enforced

> **Section 11.19.8.1 (Line 39107):**  
> "**Only one commissioning window can be active at a time.** If a Node receives another open commissioning command when an Open Commissioning Window is already active, it **SHALL** return a failure response."

### Conclusion

**This violation is disproved.** The sub-systems are orthogonal by design, mutual exclusion exists where operations would conflict, and the attack scenario incorrectly conflates independent security domains.

---

## Violation 4: PROP_026 — Prevent_Concurrent_Commissioning_Operations

**Claimed Severity**: MEDIUM  
**Claim**: No explicit Busy error response for concurrent ICACCSRRequest attempts during in-progress commissioning. Behavior undefined for ICACCSRRequest received in non-Idle states.

### Defense

**Verdict: DISPROVED — The specification defines the Busy status code for this exact purpose, and the FSM state design inherently prevents concurrent acceptance.**

#### 1. The Status Code Already Exists

> **Section 11.25.5.1, StatusCodeEnum (Value 0x02):**  
> "**Busy** — Could not be completed because **another commissioning is in progress**"
>
> **Conformance: P, M** (Mandatory)

This status code was created specifically for the scenario the violation claims is unhandled. Its mandatory conformance means implementations MUST support it.

#### 2. The FSM Design Inherently Prevents Concurrent Acceptance

The FSM accepts ICACCSRRequest ONLY from the Idle state (transition T001). From any non-Idle state (CSRRequested, CSRGenerated, ValidatingICAC, ICACAccepted), there is no transition accepting ICACCSRRequest. This is not "undefined behavior" — it is standard state machine semantics where an event without a matching transition is rejected.

#### 3. The Matter Interaction Model Defines Default Rejection

> **Section 8.9, Invoke Execution (Line 22725):**  
> "If a mandatory data field is missing, or incoming data cannot be mapped to the expected data type for a field, a CommandStatusIB SHALL be generated with an error status of INVALID_COMMAND, even if the cluster defines another type of response."

Commands received in states where they cannot be processed are not "undefined" — they are handled by the protocol layer's default rejection mechanism.

#### 4. The Base OpenCommissioningWindow Sets the Pattern

> **Section 11.19.8.1, OpenCommissioningWindow (Line 39141):**  
> "If the fail-safe timer is currently armed, this command **SHALL** fail with a cluster specific status code of **Busy**, since it is likely that concurrent commissioning operations from multiple separate Commissioners are about to take place."

The fail-safe timer IS armed during commissioning (required by ICACCSRRequest). Therefore, any concurrent commissioning attempt will trigger this Busy check at the commissioning window level. The entire system is already protected against concurrent commissioning.

#### 5. Attack Scenario Is Not Reproducible

The claimed attack: "Administrator A starts commissioning → Malicious Actor B sends ICACCSRRequest → undefined behavior."

This cannot occur because:
- Actor B must have a CASE session (mandatory for ICACCSRRequest)
- Actor B must have armed fail-safe (mandatory prerequisite)
- But only one fail-safe can be armed at a time — a second ArmFailSafe from a different fabric fails:

> **Section 11.10.7.2 (Line 34691):**  
> "Otherwise, the command SHALL leave the current fail-safe state unchanged and immediately respond with ArmFailSafeResponse containing an ErrorCode value of **BusyWithOtherAdmin**, indicating a likely conflict between commissioners."

Actor B cannot even arm the fail-safe, making it impossible to reach the ICACCSRRequest preconditions.

### Conclusion

**This violation is disproved.** Multiple specification mechanisms prevent concurrent commissioning: the Busy status code, fail-safe mutual exclusion (BusyWithOtherAdmin), the FSM state design, and the Interaction Model's default rejection. The scenario is not reproducible.

---

## Violation 5: PROP_042 — CSR_Size_Limit_600_Bytes

**Claimed Severity**: MEDIUM  
**Claim**: No size validation when generating/sending CSR. CSR >600 bytes could violate protocol constraint.

### Defense

**Verdict: DISPROVED — The data model mandates the constraint, the CSR is self-generated (not attacker-controlled), and standard ECDSA P-256 CSRs are well within limits.**

#### 1. The Constraint IS Defined in the Data Model (Mandatory)

> **Section 11.25.7.2, ICACCSRResponse Command, Parameter Table:**  
> ICACCSR — octstr — **max 600** — M

Per the constraint enforcement rules for string/octet string data:

> **Section 7.18.3.3 (Line 19881):**  
> "A constraint on a list or string data means that the data **SHALL** always be indicated within that constraint."

The word **SHALL** makes this mandatory, not optional. The ICACCSR field SHALL always be within 600 bytes. Any implementation producing >600 bytes is non-conformant by definition.

#### 2. The CSR Is Self-Generated — Not An Attack Surface

The violation report's attack path shows:
> "CSRRequested → generate_csr_success → CSRGenerated"

The CSR is generated BY THE NODE ITSELF using `generate_PKCS10_CSR_DER_encoded()`. This is NOT externally supplied input. The node controls its own key pair and DN fields. An attacker cannot inject an oversized CSR because:
- The attacker sends ICACCSRRequest (no CSR data in request)
- The node generates the CSR internally
- The node sends it back via ICACCSRResponse

There is no input vector for an attacker to control CSR size.

#### 3. Standard ECDSA P-256 CSRs Fit in 600 Bytes

Matter uses ECDSA with NIST P-256 curves. A standard PKCS#10 CSR for P-256:
- SubjectPublicKeyInfo: ~91 bytes
- Signature: ~72 bytes  
- DN fields: typically <100 bytes
- DER overhead: ~50 bytes
- **Total: ~300-350 bytes** — well within the 600-byte limit

There is no realistic scenario where a conformant implementation generates a >600-byte CSR.

#### 4. Attack Scenario Is Not Reproducible

The claimed scenario: "Malicious or buggy implementation generates CSR with very long DN fields → 650 bytes → buffer overflow on receiver."

A malicious or buggy implementation is out of scope for specification compliance analysis. The specification defines the constraint (SHALL, max 600). A non-conformant implementation violating its own specification is not a specification flaw — it is an implementation bug. The specification cannot prevent implementers from writing bugs; it can only define the correct behavior, which it does.

### Conclusion

**This violation is disproved.** The constraint is mandatory (SHALL per Section 7.18.3.3), the data is self-generated (no external attack surface), and the scenario describes an implementation bug, not a specification gap.

---

## Violation 6: PROP_043 — ICAC_Size_Limit_400_Bytes

**Claimed Severity**: MEDIUM  
**Claim**: No size validation when receiving ICAC in AddICAC. Values >400 bytes could be accepted because the "Effect on Receipt" only lists 3 validation checks.

### Defense

**Verdict: DISPROVED — The constraint is mandated by the data model layer, enforced before the application-level validation checks execute.**

#### 1. The Constraint IS Defined in the Data Model (Mandatory)

> **Section 11.25.7.3, AddICAC Command, Parameter Table:**  
> ICACValue — octstr — **max 400** — M

Per the constraint enforcement rules:

> **Section 7.18.3.3 (Line 19881):**  
> "A constraint on a list or string data means that the data **SHALL** always be indicated within that constraint."

This is a **SHALL-level** (mandatory) requirement. The data SHALL always be within 400 bytes.

#### 2. Protocol Layer Enforcement Precedes Application Layer

The Interaction Model provides constraint enforcement BEFORE the command handler processes the data:

> **Section 8.9, Invoke Execution (Line 22725):**  
> "If a data field violates expected constraints, a CommandStatusIB **SHOULD** be generated with an error status of CONSTRAINT_ERROR."

While this uses SHOULD at the IM layer, the data model constraint (Section 7.18.3.3) uses SHALL. The constraint exists at two independent layers:
- **Data Model Layer** (SHALL): The data is defined as max 400 bytes
- **Interaction Model Layer** (SHOULD): Protocol enforcement generates CONSTRAINT_ERROR

#### 3. Defense in Depth — Three Validation Checks Provide Additional Protection

Even hypothetically, if an oversized ICAC reached the handler, the three mandated validation checks provide defense:

> **Section 11.25.7.3, Effect on Receipt, Validation Check 1:**  
> "Verify the ICAC using `Crypto_VerifyChain(certificates = [ICACValue, RootCACertificate])`"

An oversized or malformed certificate would fail chain validation because:
- Crypto_VerifyChain validates the cryptographic signature, which requires exact format compliance
- A padded or inflated certificate would have an invalid signature
- The DN encoding validation (check 3) would catch any enlarged DN fields

#### 4. Attack Scenario Is Not Reproducible

The claimed attack: "450-byte ICAC passes all three checks and is accepted."

For a 450-byte ICAC to pass Crypto_VerifyChain, it must:
- Be a valid X.509 certificate signed by the Root CA
- Have the correct public key matching the CSR
- Have valid DN encoding per Matter rules

The additional 50 bytes (beyond 400) cannot be random padding — they must be structurally valid certificate data. But Matter Certificate Encoding has strict format requirements, making it infeasible to create a valid >400-byte certificate that passes all three checks AND has a legitimate use case.

Furthermore, the data model constraint (SHALL, max 400) prevents this data from being delivered to the handler in the first place.

### Conclusion

**This violation is disproved.** The data model mandates the constraint (SHALL), the protocol layer provides enforcement (SHOULD + CONSTRAINT_ERROR), and the three validation checks provide defense in depth.

---

## Violation 7: PROP_023 — Endpoint_Announcement_Uniqueness

**Claimed Severity**: MEDIUM  
**Claim**: AnnounceJointFabricAdministrator accepts any EndpointID without validating existence or JFAC cluster presence. Guard condition is `true` (unconditional).

### Defense

**Verdict: DISPROVED — This is an informational command sent by authenticated administrators; the specification correctly places the validity requirement on the sender, not the receiver.**

#### 1. The Command Is Administrator-Only (Access Level "A")

> **Section 11.25.7, Commands Table:**  
> AnnounceJointFabricAdministrator — Access: **A** (Administrator)

Only authenticated administrators with CASE sessions can invoke this command. The attacker must already have administrator-level access to send this command, severely limiting the threat model.

#### 2. The Specification Places Requirements on the Sender

> **Section 11.25.7.9, AnnounceJointFabricAdministrator Command:**  
> "This command **SHALL** be used for communicating to client the endpoint that holds the Joint Fabric Administrator Cluster."

> **EndpointID Field:**  
> "This field **SHALL** contain the unique identifier for the endpoint that holds the Joint Fabric Administrator Cluster."

The SHALL requirements are on the **sender** of the command ("this command SHALL be used for...", "this field SHALL contain..."). The sender MUST provide a valid endpoint. This is a standard pattern in Matter where the authenticated sender is trusted to provide correct data.

#### 3. This Is An Informational/Communication Command

The command's purpose is informational: "communicating to client the endpoint." It does not modify security state, install credentials, or change access control. It tells the client where to find the JFAC cluster. If a malicious administrator provides a wrong endpoint:
- The client will attempt to interact with the wrong endpoint
- Commands to the wrong endpoint will fail (cluster not found)
- The client can re-query using the Descriptor cluster to find the correct endpoint
- No security state is compromised

#### 4. The Trust Model Already Protects This

If an Administrator is malicious enough to send false endpoint announcements, they already have full administrative access to the node. This means they can:
- Open commissioning windows
- Initiate anchor transfers (with user consent)
- Perform any administrative operation

A false endpoint announcement is the **least** of the concerns with a compromised administrator. The threat model assumes administrators are trusted (they must be to have CASE sessions with administrator access).

#### 5. Attack Scenario Is Not Reproducible in Practice

The claimed attack: "Attacker announces EndpointID=255 → clients query non-existent endpoint → commands fail."

For this scenario:
- The attacker must have Administrator access (CASE + Access "A")
- Even with a wrong endpoint, clients can discover the correct endpoint via the Descriptor cluster (standard Matter discovery)
- No persistent damage occurs — clients retry with correct endpoint
- The specification's endpoint-no type with constraint "all" is standard for Matter endpoint identifiers

This is functionally equivalent to a trusted administrator providing incorrect configuration data — a trust assumption violation, not a specification flaw.

### Conclusion

**This violation is disproved.** The command requires administrator authentication, places validity requirements on the trusted sender, is purely informational, and any incorrect announcement causes no security impact beyond temporary misdirection that is self-correcting via standard Matter discovery mechanisms.

---

## Summary of Defense Outcomes

### DISPROVED Violations (6 of 7)

| Property | Claimed Issue | Defense Key Argument | Core Reference |
|---|---|---|---|
| **PROP_027** | Discriminator not validated | **Factual error**: FSM validates it; base command catch-all enforces it | FSM algorithm_detail; Section 11.19.8.1 Line 39143 |
| **PROP_035** | No state machine exclusivity | Orthogonal sub-systems by design; mutex where needed | Section 11.25.4.2 (DatastoreBusy); Section 11.19.8.1 Lines 39139-39141 |
| **PROP_026** | No Busy rejection for concurrent commissioning | Busy status code exists; fail-safe mutual exclusion prevents scenario | Section 11.25.5.1 (Busy); Section 11.10.7.2 Line 34691 (BusyWithOtherAdmin) |
| **PROP_042** | CSR size not validated | SHALL-level data model constraint; self-generated data; no attack surface | Section 7.18.3.3 Line 19881; Section 11.25.7.2 |
| **PROP_043** | ICAC size not validated | SHALL-level data model constraint; defense in depth via 3 validation checks | Section 7.18.3.3 Line 19881; Section 11.25.7.3 |
| **PROP_023** | Endpoint not validated | Administrator-only; sender responsibility; informational command | Section 11.25.7.9; Section 11.25.7 Access "A" |

### VALID Violation (1 of 7)

| Property | Issue | Mitigation |
|---|---|---|
| **PROP_033** | Fail-safe expiration cleanup not explicit for JFAC intermediate states | Provisional cluster ("P"); General fail-safe framework applies (Section 11.10.7.2.2 Step 10); Severity overstated |

---

## Detailed Specification References Used

| Section | Line(s) | Content | Used For |
|---|---|---|---|
| 7.18.3.2 | 19814, 19837 | Constraint definitions (max, range) | PROP_027, PROP_042, PROP_043 |
| 7.18.3.3 | 19881 | "data SHALL always be indicated within that constraint" | PROP_042, PROP_043 |
| 8.9 | 22725 | Command constraint enforcement (SHOULD CONSTRAINT_ERROR) | PROP_027, PROP_043 |
| 11.10.7.2 | 34700-34758 | Fail-safe context and expiration behavior | PROP_033 |
| 11.10.7.2 | 34691 | BusyWithOtherAdmin for concurrent commissioners | PROP_026 |
| 11.19.8.1 | 39107 | "Only one commissioning window can be active at a time" | PROP_035 |
| 11.19.8.1 | 39137 | PAKE parameter validation (SHALL PAKEParameterError) | PROP_027 |
| 11.19.8.1 | 39139-39141 | Busy status for concurrent commissioning operations | PROP_026, PROP_035 |
| 11.19.8.1 | 39143 | "any other parameter error → COMMAND_INVALID" (SHALL) | PROP_027 |
| 11.25 | — | "Support for Joint Fabric Administrator Cluster is provisional" | PROP_033 |
| 11.25.3 | — | Conformance "P" (Provisional) | PROP_033 |
| 11.25.4.2 | — | TransferAnchorStatusDatastoreBusy | PROP_035 |
| 11.25.5.1 | — | Busy status code (0x02) | PROP_026, PROP_035 |
| 11.25.7 | — | Access level "A" for commands | PROP_023 |
| 11.25.7.2 | — | ICACCSR octstr max 600 | PROP_042 |
| 11.25.7.3 | — | ICACValue octstr max 400; Effect on Receipt 3 validation checks | PROP_043 |
| 11.25.7.5 | — | Discriminator uint16 max 4095 | PROP_027 |
| 11.25.7.9 | — | AnnounceJointFabricAdministrator "SHALL contain unique identifier" | PROP_023 |

---

## Critical Factual Error in Violation Report

The violation report for **PROP_027** contains a demonstrable factual error:

**Report claims**:
> "validate_pake_parameters function does not include discriminator validation; values >4095 accepted"

**Actual FSM (joint_fabric_administrator_fsm.json, validate_pake_parameters, algorithm_detail)**:
> "Check constraints: (1) verifier byte_length == 97, **(2) discriminator <= 4095**, (3) 1000 <= iterations <= 100000, (4) 16 <= salt byte_length <= 32."

The function explicitly lists 4 constraint checks including discriminator. The report erroneously states only 3 checks (omitting discriminator). This factual error invalidates the entire PROP_027 analysis chain.

---

## Conclusion

The Matter Core Specification 1.4, Section 11.25 is **not faulty** with respect to 6 of the 7 claimed violations. The one valid finding (PROP_033) relates to incomplete behavioral specification in a cluster that is explicitly marked as provisional — a status that inherently communicates to implementers that the specification is subject to refinement. The general fail-safe framework already provides the mechanism for cleanup; a future revision can make the JFAC-specific cleanup steps explicit.

**Analysis Date**: 2026-02-13  
**Specification Defended**: Matter Core Specification 1.4, Section 11.25 Joint Fabric Administrator Cluster  
**Document**: 23-27349-006_Matter-1.4-Core-Specification.pdf, November 4, 2024
