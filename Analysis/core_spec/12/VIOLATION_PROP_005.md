# VIOLATION ANALYSIS - PROP_005: Administrator_CAT_Version_Revocation

## Property Under Analysis
**ID**: PROP_005  
**Name**: Administrator_CAT_Version_Revocation  
**Claim**: "To revoke an Administrator, the Anchor Administrator SHALL increment the Administrator CAT version, update NOCs for non-revoked Administrators with the new version, and update ACL entries on all Nodes with the new CAT version."

## Verdict: **VIOLATED**

---

## FSM Analysis

### Administrator Removal FSM: Transitions Examined

**Transition 1**: AdminRemoval_TargetComplete → AdminRemoval_AnchorIncrementingCAT
```json
{
  "trigger": "anchor_receives_acknowledgment",
  "actions": [
    "current_admin_cat_version := get_current_admin_cat_version()",
    "new_admin_cat_version := increment_cat_version(current_admin_cat_version)"
  ]
}
```
✓ CAT version increment: **IMPLEMENTED**

**Transition 2**: AdminRemoval_AnchorIncrementingCAT → AdminRemoval_AnchorIssuingSelfNOC
```json
{
  "actions": [
    "new_anchor_noc := issue_self_noc_with_updated_admin_cat(new_admin_cat_version)"
  ]
}
```
✓ Anchor self-NOC update: **IMPLEMENTED**

**Transition 3**: AdminRemoval_AnchorUpdatingOtherAdmins → AdminRemoval_Complete
```json
{
  "actions": [
    "foreach_remaining_admin(add_noc_with_updated_admin_cat(new_admin_cat_version))",
    "log_admin_removal_complete()"
  ]
}
```
✓ Other admins NOC update: **IMPLEMENTED**

**MISSING**: ACL updates on all devices
- FSM updates Administrator NOCs
- FSM does NOT update device ACLs with new CAT version
- Devices retain ACL entries with OLD CAT version

### Attack Path: Self-Issued Bypass

```
State 1: Admin B Removal Initiated
  - Current Administrator CAT version: v1
  - Admin B marked for removal
  - FSM executes AdminRemoval protocol

State 2: CAT Version Incremented
  - New Administrator CAT version: v2
  - Anchor updates its NOC with CAT v2
  - Other admins (Admin C, D, E) updated with CAT v2
  - Admin B NOT updated (revoked)

State 3: Admin B Self-Issues NOC with CAT v2
  - Admin B retains cross-signed ICAC private key
  - Admin B generates new NOC:
    * Subject DN: Administrator CAT v2
    * Issuer: Admin B's ICAC (chains to Anchor RCAC)
  - Admin B signs NOC using ICAC private key

State 4: Admin B Reconnects to Device
  - Device has ACL: "Administrator CAT v2 → ADMINISTER privilege"
  - Admin B presents NOC with CAT v2
  - Device validates:
    * Signature: PASS ✓ (signed by valid ICAC)
    * Chain: PASS ✓ (ICAC chains to Anchor RCAC)  
    * CAT match: PASS ✓ (CAT v2 matches ACL entry)
  - Device grants ADMINISTER privilege to Admin B

Result: **REVOCATION BYPASSED**
```

### Why Violated:

**Root Cause 1: ICAC Revocation Impossible**
- Admin B retains valid ICAC indefinitely
- ICAC chains to Anchor RCAC (cryptographically valid)
- No mechanism to revoke ICACs in Matter protocol
- Admin B can issue unlimited NOCs with ANY CAT value

**Root Cause 2: No NOC Revocation List**
- Matter has no Certificate Revocation List (CRL)
- Matter has no Online Certificate Status Protocol (OCSP)
- Nodes cannot check if NOC is revoked
- Old NOCs remain valid until replaced

**Root Cause 3: CAT Version as Sole Revocation Mechanism**
- Specification relies on CAT version to revoke access
- Assumes revoked admin cannot obtain updated CAT version
- VIOLATION: Revoked admin self-issues NOC with new CAT version using retained ICAC

**Root Cause 4: ACL Updates Not Enforced**
- FSM updates administrator NOCs but NOT device ACLs
- Spec requires "update ACL entries on all Nodes" but FSM doesn't implement this
- Even if ACLs were updated, self-issued NOCs would still match

---

## Specification Evidence

### What Spec REQUIRES (Section 12.2.4.1, Page 1058):

**Quote**:
```
"User initiated and granted revocation of an Administrator to administer nodes SHALL be  
achieved by updating the Administrator CAT. The Joint Fabric Anchor Administrator SHALL  
increment the version number of the Administrator CAT to a value higher than its current  
value (e.g., from 0x0000 to 0x0001), update the existing credentials (NOC) for all  
Administrator Nodes that are NOT being revoked with the new version of the Administrator CAT,  
and update the ACL entry of all Nodes whose subject list contains the prior version of the  
Administrator CAT with the new version of the Administrator CAT."
```

**Source**: Section 12.2.4.1, "Administrator CAT", Page 1058, Paragraph 6  
**Context**: Defines revocation procedure via CAT version increment

### What Spec ACKNOWLEDGES (Section 12.2.4.1, Page 1058, continued):

**Quote**:
```
"This has the effect of revoking the Administer access of any Administrator Nodes that did  
not receive updated credentials (NOC) with the new version of the Administrator CAT.  
Completing this operation requires visiting all the nodes in the Joint Fabric, a task which  
might take a long time to complete or might never complete if some Nodes are permanently  
offline or otherwise unreachable."
```

**Critical Admission**:
```
"However, any Nodes that are permanently offline are probably not at risk due to the  
no longer trusted Administrator Node because they are inaccessible to it."
```

**What Spec FAILS TO ADDRESS**:
- Spec assumes revoked admin cannot obtain new CAT version
- Spec does not address self-issued NOCs
- Spec does not mention ICAC retention by revoked administrators
- Spec provides no mechanism to prevent ICAC reuse

### What Spec ACKNOWLEDGES (Section 12.2.7.1, Page inferred from FSM):

**Quote from FSM Documentation**:
```
"Note: The specification does not support a method for the TRCA to revoke an ICAC.  
This means any removed administrator can continue to issue NOCs using their ICAC  
if they retain the ICAC private key."
```

**Recommended Workaround**:
```
"If fail-proof revocation is required, perform a complete Anchor transition  
(Section 12.2.6) which invalidates all old ICACs by changing the Anchor CA."
```

---

## Counterexample Scenario

### Attack: Removed Administrator Self-Re-Authorization

**Initial Conditions**:
- Joint Fabric with 4 administrators:
  - Admin A (Anchor)
  - Admin B (target for removal)
  - Admin C, Admin D (remaining admins)
- Administrator CAT version: v1
- All admins have valid cross-signed ICACs
- 1000 devices in fabric with ACL: "Administrator CAT v1 → ADMINISTER"

**Timeline of Attack**:

**T=0: Admin Removal Initiated**
- User consent obtained to remove Admin B
- Anchor executes AdminRemoval FSM
- Admin B receives RemoveFabric command

**T=1: Admin B Executes Removal**
- Admin B deletes Joint Fabric from local fabric table
- Admin B deletes fabric-scoped NOC, RCAC, ACLs
- Admin B sends acknowledgment to Anchor
- ⚠️ **Admin B RETAINS cross-signed ICAC private key**

**T=2: Anchor Increments CAT Version**
- Anchor increments Administrator CAT: v1 → v2
- Anchor issues self-NOC with CAT v2
- Anchor updates Admin C, Admin D with NOCs containing CAT v2
- All 1000 devices updated with ACL: "Administrator CAT v2 → ADMINISTER"
- Admin B NOT included in update (successfully revoked)

**T=3: Admin B Self-Issues NOC with CAT v2**
- Admin B generates new NOC locally:
  ```
  Subject: CN=Admin_B, matter-node-id=0xBBBB, matter-fabric-id=0xABCD1234
  Subject DN: Administrator CAT version 2 (FORGED)
  Issuer: Admin B's cross-signed ICAC
  Validity: NotBefore=now, NotAfter=now+365days
  ```
- Admin B signs using retained ICAC private key
- **Certificate chain still valid**: NOC → Admin B ICAC → Anchor RCAC ✓

**T=4: Admin B Attempts Access to Device_001**
- Admin B discovers Device_001 via DNS-SD
- Admin B initiates CASE session with forged NOC
- Device_001 validates Admin B's NOC:
  ```
  1. Check signature: verify(NOC, Admin_B_ICAC_pubkey) → PASS ✓
  2. Check ICAC chain: verify(ICAC, Anchor_RCAC_pubkey) → PASS ✓
  3. Check CAT version: NOC.cat_version == 2 → PASS ✓
  4. Check ACL: "Administrator CAT v2" grants ADMINISTER → PASS ✓
  ```
- CASE session established

**T=5: Admin B Regains Administrative Control**
- Admin B executes AddNOC command on Device_001
- Admin B commissions new devices to fabric
- Admin B modifies ACLs on accessible devices
- Admin B reads sensitive attributes
- **VIOLATION**: Revoked administrator fully operational

**Attack Success Rate**:
- 100% if revoked admin retains ICAC private key
- Undetectable by fabric monitoring (valid cryptographic credentials)
- Persistent (admin can self-issue NOCs indefinitely)

---

## FSM Gap Analysis

### Gap 1: ACL Update Not Implemented

**Expected Function** (from spec):
```json
{
  "name": "update_all_device_acls_with_new_cat_version",
  "parameters": [
    {
      "name": "old_cat_version",
      "type": "16-bit"
    },
    {
      "name": "new_cat_version",
      "type": "16-bit"
    }
  ],
  "return_type": "status_code",
  "description": "Updates ACL entries on all devices in fabric to replace old CAT version with new CAT version.",
  "algorithm_detail": "Queries all commissioned devices from fabric table. For each device: establishes CASE session, reads AccessControlList attribute (cluster 0x001F), modifies entries with CaseSubjectAdmin==old_cat_version to use new_cat_version, writes updated ACL via AccessControlEntryChanged event. Handles errors for unreachable devices. Returns success count."
}
```

**Actual FSM**: Function does not exist

**Impact**: Even without self-issued NOCs, incomplete ACL updates leave some devices accessible to revoked admin if they cache old ACLs.

### Gap 2: ICAC Deletion Not Enforced

**Expected Action** (post-removal):
```json
{
  "state": "AdminRemoval_TargetComplete",
  "missing_action": "securely_delete_icac_private_key()"
}
```

**Actual FSM**: No function to delete or invalidate ICAC after removal

**Spec Ambiguity**: Section 12.2.7 describes deleting "fabric-scoped data" but doesn't explicitly list ICAC as fabric-scoped. ICAC was cross-signed by Anchor, arguably making it fabric-scoped, but implementations may interpret otherwise.

### Gap 3: No NOC Revocation Check

**Missing Guard** (at CASE establishment):
```json
{
  "guard": "noc_not_revoked(noc) && issuer_icac_not_revoked(noc.issuer)",
  "implementation": "Query revocation list from Anchor Datastore. Check if NOC serial number or ICAC fingerprint is revoked."
}
```

**Actual FSM**: No revocation check mechanism exists

---

## Severity Assessment

**Severity**: **CRITICAL**

**Justification**:
1. **Complete Revocation Bypass**: CAT version mechanism is bypassable
2. **Persistent Attack**: Revoked admin retains indefinite access
3. **Undetectable**: Uses valid cryptographic credentials
4. **No Mitigation**: Specification provides no fix except Anchor transition
5. **Widespread**: Affects all Matter Joint Fabrics

**Exploitability**: HIGH
- Requires revoked administrator to retain ICAC private key
- Trivial to execute (standard NOC generation)
- No special timing or race conditions needed

**Impact**: CRITICAL
- Revoked administrators maintain full fabric access
- Cannot trust administrator removal operation
- Revocation mechanism is security theater

**CVSS 3.1 Score**: 9.1 (Critical)
- Attack Vector: Network (AV:N)
- Attack Complexity: Low (AC:L)
- Privileges Required: High (PR:H) - requires admin privileges initially
- User Interaction: None (UI:N)
- Scope: Changed (S:C) - affects entire fabric
- Confidentiality: High (C:H)
- Integrity: High (I:H)
- Availability: High (A:H)

---

## Recommendations

### Critical Fix 1: ICAC Revocation List (IRL)

**Add to Anchor Datastore**:
```json
{
  "attribute": "ICARevocationList",
  "cluster": "Joint Fabric Datastore",
  "type": "array<ICA_Fingerprint>",
  "description": "List of revoked ICAC SHA-256 fingerprints",
  "access": "Anchor: Read/Write, Administrators: Read, Devices: Read"
}
```

**Enforce at CASE**:
- Nodes check NOC issuer ICAC against IRL during CASE handshake
- Reject NOCs issued by revoked ICACs
- Update IRL when administrator removed

### Critical Fix 2: Mandatory ICAC Deletion

**Add to RemoveFabric Specification**:
```
"When executing RemoveFabric command, the target administrator SHALL securely delete  
its cross-signed ICAC private key and certificate. The ICAC SHALL be considered  
fabric-scoped data and subject to secure erasure requirements."
```

**Implementation**:
- Overwrite ICAC private key with random data (3 passes minimum)
- Delete ICAC certificate from non-volatile storage
- Attest to Anchor that ICAC has been deleted

### Fix 3: Short-Lived ICACs

**Add to Specification**:
```
"Cross-signed ICACs SHALL have a validity period of no more than 90 days.  
Administrators SHALL periodically request ICAC renewal from Anchor.  
Anchor SHALL NOT renew ICACs for administrators pending removal."
```

**Benefit**: Limits revoked admin's attack window to ICAC expiry

### Fix 4: NOC Serial Number Tracking

**Add to Specification**:
```
"All NOCs issued SHALL contain unique serial numbers. Anchor SHALL maintain  
a NOC Revocation List (NRL) containing serial numbers of revoked NOCs.  
Nodes SHALL reject NOCs with serial numbers in NRL."
```

**Limitation**: Doesn't prevent self-issued NOCs with new serial numbers, but provides additional layer

### Fix 5: Anchor-Signed NOC Distribution

**Protocol Change**:
```
"Administrator NOC updates SHALL be distributed by Anchor using NOCs signed  
by Anchor ICAC (not by administrator's own ICAC). This creates authority  
delegation without granting self-issuance capability."
```

**Benefit**: Administrators cannot self-issue NOCs; must obtain from Anchor

---

## Related Properties

**PROP_006**: Anchor_CAT_Issuance_Restriction
- Shares same root cause: ICAC revocation impossible
- Non-Anchor admins can self-issue Anchor CAT NOCs

**PROP_002**: Anchor_ICAC_Reserved_Attribute
- Assumes 'jf-anchor-icac' attribute distinguishes Anchor ICAC
- But no enforcement prevents other ICACs from issuing sensitive CATs

**PROP_043**: Administrator_Removal_User_Consent
- User consent obtained but revocation ineffective
- Creates false sense of security

---

## Specification Amendment Required

### Add New Section: 12.2.7.2 "ICAC Revocation"

**Proposed Text**:
```
"When an administrator is removed from Joint Fabric (Section 12.2.7), the Anchor  
Administrator SHALL add the removed administrator's ICAC fingerprint to the  
ICA Revocation List (IRL) maintained in the Joint Fabric Datastore.

All nodes performing CASE session establishment SHALL query the IRL and reject  
NOCs issued by revoked ICACs, even if the NOC signature and certificate chain  
are cryptographically valid.

The removed administrator SHALL securely delete its cross-signed ICAC private key  
and certificate as part of executing the RemoveFabric command. Failure to delete  
the ICAC constitutes a security violation and SHALL be logged.

If a removed administrator is discovered to have retained its ICAC and issued  
new NOCs, the Anchor Administrator SHALL initiate a full Anchor transition  
(Section 12.2.6) to invalidate all ICACs and re-establish fabric trust hierarchy."
```

---

## Status
- **Property**: VIOLATED
- **Confidence**: 100%
- **Evidence Quality**: HIGH (FSM explicitly acknowledges ICAC retention issue)
- **Exploitability**: HIGH (trivial for revoked admin with retained ICAC)
- **Severity**: CRITICAL
- **Specification Acknowledgment**: PARTIAL (acknowledges ICAC revocation gap but doesn't prevent self-issued NOCs)
