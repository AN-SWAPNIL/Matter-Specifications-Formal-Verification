# Verification Report: Section 11.25 Joint Fabric Administrator Cluster

## Defense Summary Analysis & New Vulnerability Discovery

**Date**: 2026-02-15  
**Scope**: Independent adversarial verification of `defense_summary.md` claims + new vulnerability discovery  
**Specification**: Matter Core Specification 1.4 (Document 23-27349, November 4, 2024)  
**Section Under Review**: 11.25 Joint Fabric Administrator Cluster  
**Sources Used**: Graph RAG (`core_spec` index), `core_spec.md` (49,716 lines), `11.25.md` (654 lines), `joint_fabric_administrator_fsm.json` (2,051 lines), `property_violations_report.json` (668 lines)

---

## Part 1: Verification of Defense Claims

### Methodology

Each defense claim was verified against:

1. **Actual spec text** retrieved via graph RAG and direct reading of `core_spec.md`
2. **FSM JSON** — checking whether cited functions, transitions, and guards actually exist as described
3. **Cross-referencing** — verifying that cited section numbers, line numbers, and quoted text are accurate
4. **Logical analysis** — evaluating whether the defense's reasoning chain holds even if fact claims are accurate

### Summary Table

| #   | Property | Defense Verdict   | My Verdict              | Assessment                               |
| --- | -------- | ----------------- | ----------------------- | ---------------------------------------- |
| 1   | PROP_033 | VALID (mitigated) | **VALID (understated)** | Defense understates the gap              |
| 2   | PROP_027 | DISPROVED         | **AGREE — DISPROVED**   | Defense is correct                       |
| 3   | PROP_035 | DISPROVED         | **PARTIALLY DISAGREE**  | Orthogonality claim contradicted by spec |
| 4   | PROP_026 | DISPROVED         | **PARTIALLY DISAGREE**  | Intra-fabric gap not addressed           |
| 5   | PROP_042 | DISPROVED         | **AGREE — DISPROVED**   | Defense is correct                       |
| 6   | PROP_043 | DISPROVED         | **MOSTLY AGREE**        | Trust model argument is sound            |
| 7   | PROP_023 | DISPROVED         | **AGREE — DISPROVED**   | Defense is correct                       |

**Result: 3 fully confirmed, 2 partially challenged, 1 understated, 1 mostly confirmed**

---

### Claim 1: PROP_033 — Fail_Safe_Atomicity

**Defense Verdict**: VALID but mitigated  
**My Verdict**: **VALID — Gap is more significant than defense acknowledges**

#### What the Defense Claims

The defense argues that while the gap exists, the general fail-safe framework (Section 11.10.7.2.2) covers JFAC cleanup through:

- **Step 7**: CSRRequest-generated key pair removal
- **Step 10**: RECOMMENDED rollback of non-fabric-scoped data

#### What I Found

**Finding 1: Step 7 does NOT cover ICACCSRRequest**

Step 7 of the fail-safe expiry cleanup reads:

> "If the **CSRRequest** command had been successfully invoked, but no AddNOC or UpdateNOC command had been successfully invoked, then the new operational key pair temporarily generated for the purposes of **NOC addition or update** (see Node Operational CSR Procedure) SHALL be removed as it is no longer needed."  
> — Section 11.10.7.2.2, Step 7 (core_spec.md line 34762)

The defense claims this covers ICACCSRRequest. This is **incorrect**:

| Aspect               | CSRRequest (Section 11.18.6.5.1) | ICACCSRRequest (Section 11.25.7.1)  |
| -------------------- | -------------------------------- | ----------------------------------- |
| Purpose              | Node Operational CSR for NOC     | ICA Cross-Signing CSR for ICAC      |
| Key material         | Operational key pair for NOC     | ICA key pair for ICAC cross-signing |
| Referenced in Step 7 | **YES** — explicitly named       | **NO** — not mentioned              |
| Cleanup mandated     | **SHALL** be removed             | Not specified                       |

Step 7 explicitly references "CSRRequest" (Node Operational Credentials, Section 11.18.6.5.1) and "NOC addition or update." ICACCSRRequest generates a **different** key pair for **ICA cross-signing**, not for NOC. The commands produce different cryptographic material for different purposes.

**Finding 2: Step 10 is RECOMMENDED, not SHALL**

> "Optionally: if no factory-reset resulted from the previous steps, it is **RECOMMENDED** that the Node rollback the state of all non fabric-scoped data present in the Fail-Safe context."  
> — Section 11.10.7.2.2, Step 10 (core_spec.md line 34770)

Per Matter terminology, "RECOMMENDED" means implementations SHOULD but are not required to. This is explicitly optional ("Optionally:"). The defense's claim that this step "covers" JFAC cleanup is an interpretation of optional behavior, not a mandatory protection.

**Finding 3: Fail-Safe Context does NOT list ICACCSRRequest state**

The Fail-Safe Context (core_spec.md lines 34718-34726) tracks:

- Fail-safe timer duration
- Network Commissioning Networks state
- Whether AddNOC or UpdateNOC has occurred
- Fabric Index
- Operational credentials for UpdateNOC
- **Optionally**: non-fabric-scoped data mutated during fail-safe

ICACCSRRequest generated state (ICA CSR, ICA key pair) is NOT listed. The "Optionally" clause for non-fabric-scoped data requires implementations to **choose** to store it.

**Finding 4: FSM confirms the gap — 3 states missing fail_safe_expired**

Grep of FSM confirms exactly **1** transition handles `fail_safe_expired`:

- **T016**: ICACAccepted → Idle (line 682)

States **missing** fail_safe_expired transitions:

- **CSRRequested** — only exits via `generate_csr_success` (T006)
- **CSRGenerated** — only exits via `AddICAC` (T007-T010)
- **ValidatingICAC** — only exits via `validation_complete` (T011-T014)

#### Revised Assessment

| Aspect                | Defense Claim  | My Finding                                                      |
| --------------------- | -------------- | --------------------------------------------------------------- |
| Step 7 covers JFAC    | Yes            | **No** — Step 7 is for CSRRequest/NOC, not ICACCSRRequest/ICAC  |
| Step 10 covers JFAC   | Yes            | **Partial** — RECOMMENDED, not SHALL; optionally stored         |
| Gap severity          | MEDIUM at most | **MEDIUM-HIGH** — 3 intermediate states with no cleanup mandate |
| Provisional mitigates | Yes            | Partially — but doesn't excuse the spec gap analysis            |

---

### Claim 2: PROP_027 — Discriminator_Range_Validation

**Defense Verdict**: DISPROVED  
**My Verdict**: **AGREE — DISPROVED**

#### Verification

**Fact check: Does the FSM validate discriminator?**

The `validate_pake_parameters` function (joint_fabric_administrator_fsm.json, line 1344):

```json
"parameters": [
  {"name": "verifier", "type": "octstr"},
  {"name": "discriminator", "type": "uint16", "description": "Discriminator value, max 4095"},
  {"name": "iterations", "type": "uint32"},
  {"name": "salt", "type": "octstr"}
],
"algorithm_detail": "Check constraints: (1) verifier byte_length == 97, (2) discriminator <= 4095, (3) 1000 <= iterations <= 100000, (4) 16 <= salt byte_length <= 32."
```

**Confirmed**: The function includes discriminator as parameter and check (2) validates `discriminator <= 4095`. The violation report (PROP_027) contains a **factual error** stating "validate_pake_parameters function does not include discriminator validation." The report's attack path also misrepresents the function call as `validate_pake_parameters(verifier, iterations, salt)`, omitting the discriminator parameter.

**Spec enforcement verified:**

> "In case of any other parameter error, this command **SHALL** fail with a status code of COMMAND_INVALID."  
> — Section 11.19.8.1, OpenCommissioningWindow (core_spec.md line 39156)

The discriminator constraint is also enforced by the base alias command's catch-all, which uses SHALL (mandatory).

**Conclusion**: Defense is **correct**. Violation report contains a factual error about the FSM.

---

### Claim 3: PROP_035 — State_Machine_Exclusivity

**Defense Verdict**: DISPROVED  
**My Verdict**: **PARTIALLY DISAGREE — Orthogonality claim is contradicted by the spec**

#### What the Defense Claims

The defense argues the 4 subsystems are "orthogonal by design" and operate on non-overlapping data domains. Mutual exclusion is only enforced "where security-relevant."

#### What I Found

**Finding 1: The spec itself defines cross-subsystem interactions**

The Anchor Transfer procedure (Chapter 12.2.6, page 1066 of graph RAG) explicitly references Joint Commissioning state:

> **Step 2f**: "set **BusyAnchorTransfer** error status for the **ICACSRResponse** in case an **ICA Cross Signing is in progress**."

> **Step 3a**: "All other Joint Fabric Administrators SHALL: a. **stop commissioning of any new devices** into the Joint Fabric"

If the subsystems were truly orthogonal, there would be no need for:

- BusyAnchorTransfer to affect ICACSRResponse
- Anchor transfer to stop commissioning

The spec **explicitly acknowledges** that Anchor Transfer and Joint Commissioning can conflict and provides cross-state coordination mechanisms.

**Finding 2: BusyAnchorTransfer is completely absent from the FSM**

Grep search for "BusyAnchorTransfer" in joint_fabric_administrator_fsm.json returned **zero matches**. This cross-subsystem interaction defined in the spec is not modeled in the FSM at all. This means:

- TransferAnchorRequest (T040) has no guard checking `commissioning_in_progress`
- ICACCSRRequest (T001) has no guard checking `anchor_transfer_in_progress`
- The BusyAnchorTransfer status response is not generated by any transition

**Finding 3: The specific ACL attack scenario is likely non-reproducible**

The defense correctly argues that ACL management (Section 11.24, RemoveACLFromNode) and Joint Commissioning (Section 11.25.7.1, ICACCSRRequest) operate on different data. ACL removal targets managed nodes' access control lists, while commissioning operates on PKI certificate issuance. The specific "administrator lockout" scenario in PROP_035 does conflate independent security domains.

#### Revised Assessment

| Defense Argument                          | My Finding                                                                            |
| ----------------------------------------- | ------------------------------------------------------------------------------------- |
| "4 subsystems are orthogonal"             | **INCORRECT** — spec defines BusyAnchorTransfer and step 3a as cross-interactions     |
| "Mutex where security-relevant"           | **PARTIALLY CORRECT** — mutex exists but is NOT modeled in the FSM                    |
| ACL-commissioning attack not reproducible | **LIKELY CORRECT** — different data domains                                           |
| Overall DISPROVED                         | **PARTIALLY VALID** — Anchor Transfer ↔ Joint Commissioning interaction IS a real gap |

---

### Claim 4: PROP_026 — Prevent_Concurrent_Commissioning_Operations

**Defense Verdict**: DISPROVED  
**My Verdict**: **PARTIALLY DISAGREE — Intra-fabric concurrent operations not addressed**

#### What the Defense Claims

The defense argues BusyWithOtherAdmin (Section 11.10.7.2) prevents concurrent commissioning by blocking a second administrator from arming the fail-safe.

#### What I Found

**Finding 1: BusyWithOtherAdmin is inter-fabric only**

> "Otherwise, the command SHALL leave the current fail-safe state unchanged and immediately respond with ArmFailSafeResponse containing an ErrorCode value of **BusyWithOtherAdmin**"  
> — Section 11.10.7.2, ArmFailSafe (core_spec.md line 34700)

This is triggered when the **accessing Fabric does NOT match** the fail-safe context's associated Fabric. However:

> "If ExpiryLengthSeconds is non-zero and the fail-safe timer was currently armed, and the **accessing Fabric matches** the fail-safe context's associated Fabric, then the fail-safe timer **SHALL be re-armed** to expire in ExpiryLengthSeconds."  
> — Section 11.10.7.2, ArmFailSafe (core_spec.md line 34696)

In the Joint Fabric architecture (Chapter 12), **all Joint Fabric Administrators share the same fabric**. Admin B on the same Joint Fabric CAN re-arm the fail-safe because the accessing fabric matches. BusyWithOtherAdmin does NOT trigger for same-fabric administrators.

**Finding 2: Busy status code exists but is not referenced in ICACCSRRequest**

The Busy status code (Section 11.25.5.1, value 0x02) is defined with summary "Could not be completed because another commissioning is in progress." But ICACCSRRequest's Effect on Receipt (Section 11.25.7.1) lists only 4 checks:

1. CASE session required → INVALID_COMMAND
2. Armed fail-safe required → FAILSAFE_REQUIRED
3. VID verification required → VIDNotVerified
4. Prior AddICAC → CONSTRAINT_ERROR

**No check for "commissioning already in progress"** is listed. The Busy status code exists but its usage is never mandated for ICACCSRRequest.

**Finding 3: Practical impact is limited by trust model**

Within the same Joint Fabric, administrators should be cooperating. A same-fabric administrator interfering with commissioning implies a compromised administrator, which is an elevated threat model. The BusyWithOtherAdmin protection handles the primary threat (cross-fabric interference).

#### Revised Assessment

| Defense Argument                           | My Finding                                                            |
| ------------------------------------------ | --------------------------------------------------------------------- |
| BusyWithOtherAdmin prevents concurrent ops | **Only for cross-fabric** — same-fabric admins can re-arm fail-safe   |
| Actor B cannot arm fail-safe               | **Only true for different fabric** — Joint Fabric admins share fabric |
| Busy status code covers this               | **Exists but NOT referenced** in ICACCSRRequest Effect on Receipt     |
| Violation DISPROVED                        | **Partially** — cross-fabric: protected; intra-fabric: gap exists     |

---

### Claim 5: PROP_042 — CSR_Size_Limit_600_Bytes

**Defense Verdict**: DISPROVED  
**My Verdict**: **AGREE — DISPROVED**

#### Verification

- Section 11.25.7.2: ICACCSR `octstr` max 600 — **confirmed**
- Section 7.18.3.3 (line 19881): "A constraint on a **list or string** data means that the data **SHALL** always be indicated within that constraint" — **confirmed**, and `octstr` IS a string type, so this SHALL applies
- The CSR is self-generated by the node via `generate_PKCS10_CSR_DER_encoded()` — **confirmed** from FSM T006
- No external input controls CSR content — the ICACCSRRequest command carries no CSR data
- Standard ECDSA P-256 CSR: ~300-350 bytes — well within 600-byte limit

**Conclusion**: Defense is correct. The SHALL constraint is mandatory for string types. The data is self-generated with no external attack surface. A buggy implementation is an implementation flaw, not a specification flaw.

---

### Claim 6: PROP_043 — ICAC_Size_Limit_400_Bytes

**Defense Verdict**: DISPROVED  
**My Verdict**: **MOSTLY AGREE — but defense overstates multi-layer protection**

#### Verification

**Confirmed facts:**

- Section 11.25.7.3: ICACValue `octstr` max 400 — **confirmed**
- Section 7.18.3.3 SHALL constraint applies to `octstr` — **confirmed**
- Three validation checks in Effect on Receipt — **confirmed**

**Caveat: IM enforcement is SHOULD, not SHALL**

> "If a data field violates expected constraints, a CommandStatusIB **SHOULD** be generated with an error status of CONSTRAINT_ERROR."  
> — Section 8.9, Invoke Execution (core_spec.md line 22728)

The defense claims "defense in depth" with two layers: data model (SHALL) and IM (SHOULD). But the IM layer is discretionary. If an implementation does not perform IM-layer constraint checking (permitted since it's SHOULD), the oversized ICAC reaches the handler. The three validation checks (Crypto_VerifyChain, public key match, DN encoding) validate **certificate correctness**, not **size**.

A valid >400-byte certificate with additional DN attributes COULD theoretically pass all three checks if properly signed by the Root CA.

**However**, the trust model argument is sound: the administrator sending AddICAC must have CASE session + admin access. A malicious administrator with this level of access can perform far more damaging operations than sending an oversized certificate.

**Conclusion**: Mostly agree. The trust model defense is the strongest argument. The multi-layer enforcement claim is slightly overstated due to IM SHOULD vs SHALL.

---

### Claim 7: PROP_023 — Endpoint_Announcement_Uniqueness

**Defense Verdict**: DISPROVED  
**My Verdict**: **AGREE — DISPROVED**

#### Verification

- Command requires Access "A" (Administrator) — **confirmed** from Section 11.25.7, Commands Table
- SHALL constraint on sender: "This field **SHALL** contain the unique identifier for the endpoint that holds the Joint Fabric Administrator Cluster" — **confirmed** from Section 11.25.7.9
- Informational command — communicates endpoint location, does not modify security state — **confirmed**
- Wrong endpoint → client queries fail → client rediscovers via Descriptor cluster — correct analysis
- Compromised administrator has far greater capabilities — valid trust model argument

**Conclusion**: Defense is correct. The command requires admin authentication, places validity requirements on the trusted sender, and any incorrect announcement is self-correcting via standard Matter discovery. This is not a specification flaw.

---

## Part 2: New Vulnerabilities for Formal Verification

The following vulnerabilities were discovered during the deep analysis. Each is verified against actual spec text and FSM state.

### Summary

| #   | ID      | Name                                    | Severity     | Category            |
| --- | ------- | --------------------------------------- | ------------ | ------------------- |
| 1   | NEW-001 | Anchor Transfer Missing Timeout/Abort   | **CRITICAL** | Denial of Service   |
| 2   | NEW-002 | BusyAnchorTransfer Not Modeled in FSM   | **HIGH**     | Cross-Subsystem Gap |
| 3   | NEW-003 | AwaitingVIDVerification Dead State      | **MEDIUM**   | FSM Modeling Error  |
| 4   | NEW-004 | Administrator Session Binding Ambiguity | **MEDIUM**   | Specification Gap   |

---

### NEW-001: Anchor Transfer Missing Timeout/Abort — CRITICAL

**Category**: Denial of Service  
**Severity**: CRITICAL  
**Type**: Specification + FSM Gap

#### Evidence

**FSM Analysis**: The `AnchorTransfer_InProgress` state can ONLY exit via `TransferAnchorComplete` (transition T044):

```
T040: AnchorTransfer_Idle → AnchorTransfer_RequestReceived  (trigger: TransferAnchorRequest)
T041: AnchorTransfer_RequestReceived → AnchorTransfer_InProgress  (trigger: preconditions_checked, user_consent + datastore idle)
T044: AnchorTransfer_InProgress → AnchorTransfer_Complete  (trigger: TransferAnchorComplete)
```

There is **NO** timeout transition, **NO** abort transition, **NO** fail-safe integration for anchor transfer. If `TransferAnchorComplete` is never received, the system remains in `AnchorTransfer_InProgress` indefinitely.

**Spec Evidence — Side effects are permanent until completion:**

The Anchor Transfer procedure (Chapter 12.2.6, page 1066) mandates these state changes upon entering transfer:

> **Step 2c**: "check all the Datastore entries of type DatastoreStatusEntry. If any of these entries has a value that equals to `Pending` or to `DeletePending` then TransferAnchorResponse command with StatusCode set to TransferAnchorStatusDatastoreBusy **SHALL** be sent"

> **Step 2d**: "put Joint Fabric Datastore in **read only state** by setting the Datastore StatusEntry to `DeletePending`"

> **Step 2e**: "**stop DNS SD advertising** of the `Administrator`, `Anchor` and `Datastore` capability inside the JF TXT key"

> **Step 2f**: "set BusyAnchorTransfer error status for the ICACSRResponse in case an ICA Cross Signing is in progress"

> **Step 3a**: "All other Joint Fabric Administrators SHALL: a. **stop commissioning of any new devices** into the Joint Fabric"

**Impact if TransferAnchorComplete never arrives**:

- Datastore locked in read-only (`DeletePending`) — **permanent**
- DNS-SD advertising stopped — no new administrators can discover the Joint Fabric — **permanent**
- All other administrators stopped from commissioning — **permanent**
- ICA cross-signing blocked (BusyAnchorTransfer) — **permanent**

**Attack Scenario**:

1. Malicious Administrator A obtains user consent for anchor transfer
2. A sends TransferAnchorRequest → approved (user consent + datastore idle)
3. Anchor enters AnchorTransfer_InProgress — executes steps 2d, 2e, 2f, 3a
4. A disconnects (network failure, intentional disconnect, or malicious abort)
5. TransferAnchorComplete never arrives
6. **Result**: Entire Joint Fabric permanently disabled — no commissioning, no datastore writes, no advertising
7. **Recovery**: No spec-defined recovery mechanism — **factory reset is the only recovery**

**Key distinction from PROP_033**: This is NOT bounded by fail-safe timer. TransferAnchorRequest does NOT require armed fail-safe. The anchor transfer procedure has NO timeout mechanism at all.

**Formal Verification Property**:

```
AG(AnchorTransfer_InProgress → AF(AnchorTransfer_Complete ∨ AnchorTransfer_Idle))
```

This **FAILS** — no liveness guarantee. The system can remain in AnchorTransfer_InProgress forever.

---

### NEW-002: BusyAnchorTransfer Not Modeled in FSM — HIGH

**Category**: Cross-Subsystem Interaction Gap  
**Severity**: HIGH  
**Type**: FSM Modeling Gap (spec has protection, FSM doesn't model it)

#### Evidence

**Spec defines the interaction** (Chapter 12.2.6, page 1066):

> **Step 2f**: "set **BusyAnchorTransfer** error status for the **ICACSRResponse** in case an ICA Cross Signing is in progress"

> **Step 3a**: "All other Joint Fabric Administrators SHALL: a. **stop commissioning of any new devices** into the Joint Fabric"

**FSM does NOT model this interaction**:

- Grep for "BusyAnchorTransfer" in FSM JSON: **0 matches**
- TransferAnchorRequest transition T040 has guard: `is_anchor == true` — no check for `commissioning_in_progress`
- ICACCSRRequest transition T001 has guard: `case_session_active == true && fail_safe_armed == true && vid_verified == true && prior_AddICAC_executed == false` — no check for `anchor_transfer_in_progress`

**Consequence**: The FSM allows concurrent execution of Anchor Transfer and Joint Commissioning with no guards, even though the spec mandates cross-state coordination. Formal verification tools analyzing this FSM would MISS this interaction because it's not modeled.

**Missing transitions/guards for formal model**:

1. T040 should include guard: `commissioning_in_progress == false`
2. T001 should include guard: `anchor_transfer_in_progress == false`
3. T041 should include action: `set_busy_anchor_transfer_for_icacsr()`
4. New transition needed: CSRGenerated → ErrorState on `anchor_transfer_started` trigger, returning BusyAnchorTransfer

**Formal Verification Property**:

```
AG(AnchorTransfer_InProgress → ¬(CSRRequested ∨ CSRGenerated ∨ ValidatingICAC))
```

This **FAILS** in the current FSM — both state machines can be active simultaneously.

---

### NEW-003: AwaitingVIDVerification Dead State — MEDIUM

**Category**: FSM Modeling Error  
**Severity**: MEDIUM  
**Type**: FSM Structural Defect

#### Evidence

The FSM declares the `AwaitingVIDVerification` state (line 26):

```json
{
  "name": "AwaitingVIDVerification",
  "description": "Received ICACCSRRequest but VID verification has not been completed",
  "invariants": ["vid_verified == false", "fail_safe_armed == true"],
  "state_variables": {
    "fail_safe_armed": "boolean",
    "vid_verified": "boolean",
    "request_pending": "boolean"
  }
}
```

Grep for transitions TO or FROM this state:

- `to_state.*Awaiting`: **0 matches**
- `from_state.*Awaiting`: **0 matches**

The state is **unreachable** — a dead state in the FSM. The VID Verification process referenced by ICACCSRRequest (Section 11.25.7.1: "If the Fabric Table Vendor ID Verification Procedure has not been executed against the initiator of this command") is treated as a **precondition** (guard: `vid_verified == true` in T001) rather than modeled as a state transition sequence.

**Impact for formal verification**:

- The VID Verification process is a security-critical prerequisite that occurs outside the FSM model
- The FSM assumes VID verification is complete before entering the commissioning flow
- If VID verification has timing, ordering, or concurrency properties, they cannot be verified with this FSM
- This is a modeling completeness issue, not a spec vulnerability

**Formal Verification Property**:

```
EF(state = AwaitingVIDVerification)
```

This **FAILS** — state is unreachable (dead state).

---

### NEW-004: Administrator Session Binding Ambiguity — MEDIUM

**Category**: Specification Gap  
**Severity**: MEDIUM  
**Type**: Specification Ambiguity

#### Evidence

**Spec text** (Section 11.25.7.3, AddICAC Effect on Receipt, validation check 2):

> "The public key of the ICAC **SHALL** match the public key present in the last ICACCSRResponse **provided to the Administrator that sent the AddICAC command**."

The phrase "provided to the Administrator that sent the AddICAC command" implies per-administrator tracking. But the specification does NOT define:

1. **How** the binding between ICACCSRResponse and the specific administrator is maintained
2. Whether binding is by **CASE session**, **Node ID**, **Fabric Index**, or **other mechanism**
3. What happens if the CASE session is re-established between ICACCSRRequest and AddICAC
4. What happens if another administrator on the **same fabric** re-arms the fail-safe (permitted by spec) and sends AddICAC

**Scenario**:

1. Admin A (Joint Fabric, Fabric 1) arms fail-safe, sends ICACCSRRequest → receives CSR with public key K
2. Admin A's CASE session drops or times out
3. Admin B (Joint Fabric, same Fabric 1) re-arms fail-safe (permitted — same fabric)
4. Admin B sends AddICAC with an ICAC containing public key K (obtained from Admin A)
5. Check 2 says "match the public key present in the last ICACCSRResponse provided to **the Administrator** that sent the AddICAC command"
6. The last ICACCSRResponse was provided to Admin A, not Admin B
7. But how does the node distinguish Admin A from Admin B? Both are on the same fabric.

**Impact**: The per-administrator session binding mechanism is ambiguous. Implementations may use different binding strategies (session-based, fabric-based, node-ID-based), leading to interoperability issues and potential security gaps.

**Formal Verification Property**:

```
AG(AddICAC → icac_pubkey = last_CSR_pubkey_for_SAME_administrator)
```

The binding semantics of "SAME_administrator" are undefined, making this property unverifiable.

---

## Part 3: Consolidated Findings

### Defense Accuracy Assessment

| Category                     | Count                                                                         |
| ---------------------------- | ----------------------------------------------------------------------------- |
| Fully Correct Defenses       | 3 (PROP_027, PROP_042, PROP_023)                                              |
| Mostly Correct Defenses      | 1 (PROP_043 — overstates IM enforcement)                                      |
| Partially Incorrect Defenses | 2 (PROP_035 — false orthogonality claim; PROP_026 — ignores intra-fabric gap) |
| Understated Gap              | 1 (PROP_033 — Step 7 is for CSRRequest/NOC, not ICACCSRRequest/ICAC)          |

### Critical Error Found in Defense

**PROP_033 Defense — Step 7 Misattribution**

The defense claims fail-safe cleanup Step 7 covers ICACCSRRequest key material. This is **incorrect**. Step 7 explicitly names "CSRRequest" (Node Operational Credentials, Section 11.18.6.5.1) and references "NOC addition or update." ICACCSRRequest (Section 11.25.7.1) generates ICA cross-signing key material, which is a different cryptographic operation. The defense conflates two distinct CSR commands and their respective key material.

### Critical Error Found in Violation Report

**PROP_027 Violation — Factual Error**

The violation report claims `validate_pake_parameters` does not include discriminator validation. The FSM function explicitly includes discriminator as a parameter and validates `discriminator <= 4095` as check (2). The violation report's attack path also misrepresents the function signature by omitting the discriminator parameter. This factual error invalidates the entire PROP_027 violation analysis.

### New Vulnerabilities Summary

| ID      | Name                                  | Severity     | Proven?                                                                                                                                                                                                       |
| ------- | ------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NEW-001 | Anchor Transfer Missing Timeout/Abort | **CRITICAL** | **YES** — FSM has no exit from AnchorTransfer_InProgress except TransferAnchorComplete; spec defines permanent side effects (read-only datastore, stopped advertising, blocked commissioning) with no timeout |
| NEW-002 | BusyAnchorTransfer Not Modeled        | **HIGH**     | **YES** — spec defines cross-interaction (Ch 12.2.6 step 2f), FSM has 0 matches for BusyAnchorTransfer                                                                                                        |
| NEW-003 | AwaitingVIDVerification Dead State    | **MEDIUM**   | **YES** — 0 transitions to/from state; unreachable in FSM                                                                                                                                                     |
| NEW-004 | Administrator Session Binding         | **MEDIUM**   | **YES** — spec says "provided to the Administrator" but doesn't define binding mechanism                                                                                                                      |

### Formal Verification Properties to Add

```
# NEW-001: Liveness of anchor transfer
AG(AnchorTransfer_InProgress → AF≤timeout(AnchorTransfer_Complete ∨ AnchorTransfer_Idle))

# NEW-002: Mutual exclusion of anchor transfer and commissioning
AG(AnchorTransfer_InProgress → ¬(CSRRequested ∨ CSRGenerated ∨ ValidatingICAC ∨ ICACAccepted))
AG((CSRRequested ∨ CSRGenerated ∨ ValidatingICAC) → ¬AnchorTransfer_InProgress)

# NEW-003: State reachability
EF(AwaitingVIDVerification)  # Should be reachable or removed

# NEW-004: Session binding
AG(AddICAC_accepted → icac_pubkey = last_CSR_pubkey_for_same_session)
```

---

## Specification References

| Section             | Line(s) in core_spec.md | Content                                                                        | Used For                      |
| ------------------- | ----------------------- | ------------------------------------------------------------------------------ | ----------------------------- |
| 7.18.3.3            | 19881                   | "data SHALL always be indicated within that constraint" (lists/strings)        | PROP_042, PROP_043            |
| 8.9                 | 22728                   | "SHOULD be generated with an error status of CONSTRAINT_ERROR"                 | PROP_043 (IM layer is SHOULD) |
| 11.10.7.2           | 34696-34700             | ArmFailSafe — same fabric re-arm vs BusyWithOtherAdmin                         | PROP_026                      |
| 11.10.7.2.2         | 34750-34770             | Fail-safe expiry Steps 1-10                                                    | PROP_033                      |
| 11.10.7.2.2 Step 7  | 34762                   | "If the CSRRequest command had been successfully invoked" — NOT ICACCSRRequest | PROP_033                      |
| 11.10.7.2.2 Step 10 | 34770                   | "RECOMMENDED...rollback...non fabric-scoped data" — optional                   | PROP_033                      |
| 11.19.8.1           | 39152-39156             | PAKEParameterError, Busy, COMMAND_INVALID for OpenCommissioningWindow          | PROP_027                      |
| 11.25.5.1           | —                       | Busy status code (0x02) — not referenced in ICACCSRRequest                     | PROP_026                      |
| 11.25.7.1           | —                       | ICACCSRRequest Effect on Receipt — 4 checks, no Busy check                     | PROP_026                      |
| 11.25.7.3           | —                       | AddICAC "public key...provided to the Administrator that sent"                 | NEW-004                       |
| 12.2.6              | page 1066               | TransferAnchorRequest procedure — Steps 2d, 2e, 2f, 3a                         | NEW-001, NEW-002              |

---

**Analysis Date**: 2026-02-15  
**Verification Against**: defense_summary.md (2026-02-13)  
**Specification**: Matter Core Specification 1.4, Section 11.25 Joint Fabric Administrator Cluster  
**Document**: 23-27349-006_Matter-1.4-Core-Specification.pdf, November 4, 2024
