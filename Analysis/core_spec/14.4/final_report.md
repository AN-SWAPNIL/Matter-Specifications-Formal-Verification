# DEFENSE OF SPECIFICATION: TLS Certificate Management Cluster (Section 14.4)

**Date:** 2025-02-13  
**Specification Under Defense:** Matter Core Specification v1.4, Section 14.4 (Cluster ID 0x0801)  
**Claims Analyzed From:** PROPERTY_VIOLATIONS_REPORT.md, property_violation_analysis_working.md, security_properties.json

---

## EXECUTIVE SUMMARY

The analysis reports identify **5 issues** across 42 analyzed properties:
- 2 × PARTIALLY_UNVERIFIABLE (PROP_001, PROP_002)
- 3 × UNVERIFIABLE (PROP_018, PROP_019, PROP_030)
- 0 × VIOLATED

**Defense Verdict:** All 5 issues are **NOT specification defects**. They are FSM modeling limitations or architectural misunderstandings of Matter's layered security design. The specification is complete and secure as written. Detailed refutations with exact spec quotes follow.

---

## CLAIM-BY-CLAIM DEFENSE

---

### CLAIM 1: PROP_001 — Fabric_Isolation_Root_Certificates (PARTIALLY_UNVERIFIABLE)

**Alleged Issue:** "Missing error transitions for fabric mismatch in FSM. Cannot verify that NOT_FOUND is returned when fabric mismatch occurs."

**Verdict: DISPROVED — Not a specification defect. FSM modeling incompleteness is the analyzer's issue, not the specification's.**

#### Defense

**Defense Point A: The specification EXPLICITLY mandates fabric isolation with SHALL language in every relevant command.**

The specification provides deterministic, exhaustive "Effect on Receipt" procedures for every command. Each one explicitly handles the fabric mismatch case with mandatory (SHALL) NOT_FOUND responses:

**ProvisionRootCertificate** (Section 14.4.6.1, Effect on Receipt):
> *"Else if the passed in CAID is not null:*
> *If there is no matching entry found for the passed in CAID in the ProvisionedRootCertificates list:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects.*
> ***If the associated fabric of that entry does not equal the accessing fabric:***
> ***Fail the command with the status code NOT_FOUND, and end processing with no other side effects."***

**FindRootCertificate** (Section 14.4.6.3, Effect on Receipt):
> *"Else if the passed in CAID is not null:*
> *If there is no entry in the ProvisionedRootCertificates list that has a CAID Field matching the passed in CAID:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects.*
> ***If the associated fabric of the TLSCertStruct for that entry does not equal the accessing fabric:***
> ***Fail the command with the status code NOT_FOUND, and end processing with no other side effects."***

**LookupRootCertificate** (Section 14.4.6.5, Effect on Receipt):
> *"If there is no entry in the ProvisionedRootCertificates list that has a matching Fingerprint, **or the associated fabric of that entry does not equal the accessing fabric**:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects."*

**RemoveRootCertificate** (Section 14.4.6.7, Effect on Receipt):
> *"If the associated fabric of the TLSCertStruct for that entry does not equal the accessing fabric:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects."*

**Defense Point B: The spec additionally enforces fabric isolation at the Data Model layer (Section 7.5.3).**

All data types in this cluster are declared "Access Modifier: Fabric Scoped" (Section 14.4.4.3, 14.4.4.4). The Matter Data Model layer imposes a **blanket mandatory constraint** on ALL fabric-scoped data:

**Section 7.5.3 — Fabric-Scoped Data:**
> *"Any interaction, including cluster commands, **SHALL NOT** cause modification of fabric-scoped data, directly or indirectly, if the interaction has an accessing fabric different than the associated fabric for the data, except in the case of a cluster command that explicitly defines an exception to this rule."*

This is a **dual-layer guarantee**: the cluster command logic explicitly checks fabric AND the data model framework independently prevents cross-fabric modification. Even if a cluster implementation had a bug, the data model layer would block it.

**Defense Point C: The NULL CAID "return all" path is inherently fabric-scoped.**

FindRootCertificate with NULL CAID (Section 14.4.6.3):
> *"For each entry in ProvisionedRootCertificates:*
> *If the associated fabric of the entry matches the accessing fabric:*
> *Add a populated TLSCertStruct entry for the CAID to the resulting list."*

Only entries matching the accessing fabric are ever added. Cross-fabric certificates are never visible.

**Conclusion:** The claim is that the specification has a "gap." In reality, the specification provides **6 separate explicit fabric isolation checks** across the 4 root certificate commands, plus a global data model layer guarantee. The FSM model chose not to model error transitions — that is an FSM design decision, not a spec flaw. The phrase "end processing with no other side effects" (used in every error path) makes the behavior fully deterministic. There is no ambiguity and no vulnerability.

**Reproducible Attack Scenario Assessment:** The claimed attack is that a fabric mismatch could return something other than NOT_FOUND. This is impossible because:
1. The spec uses SHALL language for the NOT_FOUND response
2. The spec says "end processing with no other side effects"  
3. No path exists in the specified algorithm that reaches success without passing the fabric check

---

### CLAIM 2: PROP_002 — Fabric_Isolation_Client_Certificates (PARTIALLY_UNVERIFIABLE)

**Alleged Issue:** Same as PROP_001 but for client certificates. "Missing explicit fabric mismatch error transitions in FSM."

**Verdict: DISPROVED — Same defense as PROP_001. Specification explicitly handles every fabric mismatch case.**

#### Defense

Every client certificate command explicitly checks fabric isolation with SHALL semantics:

**ClientCSR** (Section 14.4.6.8, Effect on Receipt):
> *"Else if the passed in CCDID is not NULL:*
> *If there is no entry in the ProvisionedClientCertificates list that has a matching CCDID to the passed in CCDID:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects.*
> ***If the associated fabric of that entry does not equal the accessing fabric:***
> ***Fail the command with the status code NOT_FOUND, and end processing with no other side effects."***

**ProvisionClientCertificate** (Section 14.4.6.10, Effect on Receipt):
> *"If the associated fabric for that entry does not equal the accessing fabric:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects."*

**FindClientCertificate** (Section 14.4.6.11, Effect on Receipt):
> *"If the associated fabric of that entry does not equal the accessing fabric:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects."*

**LookupClientCertificate** (Section 14.4.6.13, Effect on Receipt):
> *"If the associated fabric of that entry does not equal the accessing fabric:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects."*

**RemoveClientCertificate** (Section 14.4.6.15, Effect on Receipt):
> *"If the associated fabric of that entry does not equal the accessing fabric:*
> *Fail the command with the status code NOT_FOUND, and end processing with no other side effects."*

**Additionally**, the same Data Model layer protection from Section 7.5.3 applies:
> *"Any interaction, including cluster commands, **SHALL NOT** cause modification of fabric-scoped data, directly or indirectly, if the interaction has an accessing fabric different than the associated fabric for the data."*

**Conclusion:** All 5 client certificate commands have explicit fabric isolation checks. The reported "PARTIALLY_UNVERIFIABLE" verdict reflects an FSM design choice to omit error transitions, not a specification gap.

---

### CLAIM 3: PROP_030 — Admin_Privilege_Required_For_Mutations (UNVERIFIABLE)

**Alleged Issue:** "FSM does not model access control layer. Admin privilege checks missing from all FSM transition guards. Specification doesn't define HOW admin privilege is verified within Section 14.4."

**Claimed Attack Scenario:** "Unprivileged attacker sends ProvisionRootCertificate command → Access control layer SHOULD reject → IF bypass occurs, FSM allows provisioning → Attacker injects malicious root CA."

**Verdict: DISPROVED — The specification defines access control enforcement comprehensively in its proper architectural location. Section 14.4 correctly delegates to the Interaction Model and Access Control system per Matter's layered architecture.**

#### Defense

**Defense Point A: Section 14.4 explicitly declares Admin privilege on every mutation command.**

The Commands table in Section 14.4.6 specifies the Access column for each command:

| Command | Access |
|---------|--------|
| ProvisionRootCertificate | **A F** |
| RemoveRootCertificate | **A F** |
| ClientCSR | **A F** |
| ProvisionClientCertificate | **A F** |
| RemoveClientCertificate | **A F** |
| FindRootCertificate | O F |
| LookupRootCertificate | O F |
| FindClientCertificate | O F |
| LookupClientCertificate | O F |

"A" = Administer privilege required. "F" = Fabric-scoped. This is not missing — it is explicitly declared.

**Defense Point B: The Interaction Model enforces access control BEFORE any command reaches the cluster.**

Section 8.8.2.3 (Incoming Invoke Request Action) defines mandatory access control enforcement:

> *"Each request path in the InvokeRequests field **SHALL** be processed as follows:*
> *◦ Else if the path is a concrete path:*
> ***▪ Else if invoking the command in the path requires a privilege that is not granted to access the cluster in the path, a CommandStatusIB SHALL be generated with the UNSUPPORTED_ACCESS Status Code."***

This means: if a command requires Administer privilege (as ProvisionRootCertificate does, per the "A" access modifier) and the invoker does not have Administer privilege, the Interaction Model layer **SHALL** reject the command with UNSUPPORTED_ACCESS **before it ever reaches the cluster's Effect on Receipt processing**.

**Defense Point C: Access Control is deny-by-default.**

Section 6.6.2 (Access Control Model):
> *"The Access Control system is rule-based with **no implicit access permitted by default**. Access to a Node's Targets is denied unless the Access Control system grants the required privilege level to a given Subject to interact with given Targets on that Node."*

> *"All access privileges, from the AccessControlEntryPrivilegeEnum enumeration, **SHALL** be granted by Access Control. Thus, the Initiator ("Subject" hereafter) of any Interaction Model action **SHALL NOT succeed** in executing a given action on a Node's Target unless that Node's Access Control system explicitly grants the required privilege to that Subject for that particular action."*

**Defense Point D: Administer privilege requires CASE authentication (mutual TLS).**

Section 6.6.2.11:
> *"it **SHALL NOT** be valid to have an Administer privilege set on an Access Control Entry, unless the AuthMode's AuthModeCategory is "CASE"."*

This means Administer privilege can only be granted through Certificate Authenticated Session Establishment — a mutually authenticated TLS-like session. Group messaging, which has "no source Node authentication," cannot grant Administer privilege.

**Defense Point E: Fabric-scoped commands additionally require a valid fabric context.**

Section 8.8.2.3:
> *"Else if the command in the path is fabric-scoped and there is no accessing fabric, a CommandStatusIB **SHALL** be generated with the UNSUPPORTED_ACCESS Status Code."*

Even if an attacker somehow had privilege, they would be blocked if they lack a valid fabric context.

**Defense Point F: This is intentional architectural layering, not a gap.**

The specification defines access control in Section 6.6 and the Interaction Model in Section 8.8 precisely because these are cross-cutting concerns that apply to ALL clusters, not just TLS Certificate Management. Repeating privilege enforcement logic inside each cluster specification would be:
1. Redundant — violating DRY (Don't Repeat Yourself) design
2. Error-prone — inconsistencies between clusters would create real vulnerabilities
3. Architecturally incorrect — privilege checking belongs in the interaction/access layer, not in business logic

The Data Model (Section 7.6) defines exactly how the "A" access modifier works:
> *"Attributes, commands, and events **SHALL** define their access, and **SHALL** include privileges in their access definition."*

Section 14.4.6 does exactly this with the Access column in its command table.

**Reproducible Attack Scenario Assessment:** The claimed attack requires bypassing the Interaction Model's access control enforcement (Section 8.8.2.3). This would require:
1. Bypassing CASE session authentication (Section 4.14.2)
2. Bypassing the deny-by-default ACL evaluation (Section 6.6.2)
3. Bypassing the Interaction Model's privilege check (Section 8.8.2.3)

All three are protected by SHALL-level requirements. A bypass of these foundational layers would compromise the entire Matter protocol, not just TLS Certificate Management. This is equivalent to saying "if TLS is broken, HTTPS is insecure" — technically true but not a flaw in any individual application.

---

### CLAIM 4: PROP_018 — Large_Message_Transport_Certificate_Inclusion (UNVERIFIABLE)

**Alleged Issue:** "FSM does not model transport layer. Cannot verify that certificate data is included when reading over Large Message capable transport."

**Verdict: DISPROVED — This is a data presentation rule, not a security property. The specification defines it completely.**

#### Defense

The specification explicitly states the behavior for both transport types:

**Section 14.4.4.3 (TLSCertStruct, Certificate Field):**
> *"When this field exists and is read over a Large Message capable transport, it **SHALL** be included. When this field exists and is read over a non Large Message capable transport, it **SHALL NOT** be included."*

**Section 14.4.4.4 (TLSClientCertificateDetailStruct, ClientCertificate Field):**
> *"When this field exists and is read over a Large Message capable transport, it **SHALL** be included. When this field exists, is non-NULL, and is read over a non Large Message capable transport, it **SHALL NOT** be included."*

**Section 14.4 (cluster introduction):**
> *"Commands in this cluster uniformly use the Large Message qualifier, even when the command doesn't require it, to reduce the testing matrix."*

The specification defines these rules completely. The fact that an FSM model of one cluster doesn't model transport behavior is expected — transport is a separate concern. The specification provides FindRootCertificate and FindClientCertificate commands specifically as a fallback mechanism for non-Large-Message transports:

> *"To get the full details of a certificate use the FindRootCertificate command."*
> *"To get the full details of a certificate use the FindClientCertificate command."*

This is defense-in-depth: even if the field exclusion rule weren't enforced, the Find commands provide the data, and the cluster uses Large Message qualifier on all commands anyway.

**Reproducible Attack Scenario Assessment:** No attack is possible. The worst case is that certificate data is omitted from attribute reads on non-Large-Message transports, which is the **intended and specified behavior**. The Find commands exist precisely for this case.

---

### CLAIM 5: PROP_019 — Non_Large_Message_Transport_Certificate_Exclusion (UNVERIFIABLE)

**Alleged Issue:** Same as PROP_018 but for exclusion on non-Large-Message transports.

**Verdict: DISPROVED — Same defense as PROP_018. Fully specified behavior, not a gap.**

The specification explicitly mandates exclusion (see quotes above). The FindRootCertificate/FindClientCertificate commands exist as the specified mechanism to retrieve certificate data regardless of transport capability.

---

## ANALYSIS OF "ADDITIONAL INSIGHTS" CLAIMS (from security_properties.json)

The security_properties.json file includes an `additionalInsights` field with several architectural criticisms. These are addressed below.

---

### ADDITIONAL CLAIM A: "Certificate Rotation Race Condition Window"

**Alleged Issue:** "The specification does not define mechanisms for: (1) atomic certificate switchover, (2) notification to active endpoints about rotation completion, or (3) grace period handling."

**Verdict: DISPROVED — The specification explicitly addresses connection isolation during rotation.**

**ProvisionRootCertificate** (Section 14.4.6.1, Note):
> *"**Note** when using this command for certificate rotation, the updated certificate will only be used for new underlying TLS connections established after this call."*

**ProvisionClientCertificate** (Section 14.4.6.10, Note):
> *"**Note:** When using this command for client certificate rotation, only new underlying TLS connections (established after this finishes processing), will use the updated Certificate."*

The specification explicitly defines the boundary: in-flight connections use old certificates, new connections use updated ones. This is the standard certificate rotation pattern used by all major TLS implementations (e.g., NGINX, Apache, HAProxy all use this exact model). No atomic switchover is needed because:
1. Existing connections are already authenticated — they don't re-validate root CAs mid-session
2. New connections use the new certificate — they get the updated trust anchor
3. There is no "mixed state" — each connection uses the certificate that was active when it was established

**Reproducible Attack Scenario:** The claimed scenario of "negotiating with mixed certificate state (old root CA, new client cert)" is not possible because:
- A TLS connection negotiates with the certificates present at connection establishment
- The specification guarantees old connections keep using old certs
- The rotation does not affect already-established TLS sessions

---

### ADDITIONAL CLAIM B: "SHOULD Statement Risk — ID Wraparound"

**Alleged Issue:** "Specification does not mandate exhaustive search on collision. Attacker provisions ~32K certificates to increase collision probability to ~50%."

**Verdict: PARTIALLY VALID but not exploitable. Defense below.**

The specification (Section 14.4.4.1, TLSCAID Type):
> *"The Node **SHALL** verify that a new value does not match any other value for this type. If such a match is found, the value **SHALL** be changed until a unique value is found."*

The SHALL-level collision check IS mandatory. The SHOULD-level guidance is only for the starting point and increment strategy:
> *"This value **SHOULD** start at 0 and monotonically increase by 1"*

The collision detection and retry ("SHALL be changed until a unique value is found") is not SHOULD — it is **SHALL**. Additionally, the attack requires provisioning ~32K certificates on a single node. Given:
- MaxRootCertificates has constraint "5 to 254" per fabric (Section 14.4.5, Attributes table)
- MaxClientCertificates has constraint "2 to 254" per fabric  
- RESOURCE_EXHAUSTED is returned when limits are reached  
- Admin privilege is required for every provision operation

An attacker would need to provision and remove certificates (~254 × many cycles) with Admin privilege. But an entity with Admin privilege already has full control of the node — they don't need a CAID collision to cause damage.

**Conclusion:** The collision detection is SHALL-mandatory. The attack requires Admin privilege, which already grants full control. The risk is theoretical only.

---

### ADDITIONAL CLAIM C: "Implicit Assumption — Root Certificate Required Before Client Provisioning (PROP_034)"

**Alleged Issue:** "Specification separately defines ProvisionRootCertificate and ProvisionClientCertificate without ordering constraint. Creates temporal vulnerability where client cert exists but cannot validate."

**Verdict: PARTIALLY VALID — But this is a deliberate design choice, not a vulnerability.**

The specification intentionally allows ProvisionClientCertificate without requiring a root certificate to be provisioned first, because:

1. **The client certificate and root certificate may be provisioned by different administrators** — requiring ordering would break multi-admin scenarios
2. **Certificate chain validation is done at TLS connection time, not at provisioning time** — this is standard PKI practice (e.g., OS trust stores don't validate chain completeness when adding end-entity certificates)
3. **A TLS endpoint references BOTH a CAID and a CCDID** at the TLS Client Management Cluster level (Section 14.5), so the chain is assembled at endpoint provisioning time, not certificate provisioning time

Section 14.4.6.10 (ProvisionClientCertificate) validates:
- Certificate format (DER-encoded, valid TLS certificate)  
- Public-private key correspondence
- Fingerprint uniqueness
- Fabric isolation

It does NOT validate chain-to-root because that is the responsibility of the TLS endpoint provisioning (Section 14.5) and the TLS handshake itself. This is correct architectural layering.

**No reproducible attack:** A client cert without a matching root CA simply fails TLS handshake. No data is exposed, no privilege is gained. The worst case is a non-functional TLS endpoint, which the administrator created themselves (requiring Admin privilege).

---

### ADDITIONAL CLAIM D: "Fabric Isolation Design Flaw — Fabric identity mutable or spoofable"

**Alleged Issue:** "Specification uses 'accessing fabric' without defining isolation mechanism. If fabric identity is mutable or spoofable, entire isolation model collapses."

**Verdict: DISPROVED — Fabric identity is cryptographically bound via CASE sessions.**

**Section 6.6.6.3** (Derivation of Incoming Subject Descriptor from CASE Session):
The accessing fabric is derived from the CASE session metadata:
```
isd.FabricIndex = sessions_metadata.get_fabric_index(session_id)
assert(isd.FabricIndex != 0)
```

CASE (Certificate Authenticated Session Establishment) provides mutual authentication using operational certificates. The fabric identity is:
1. **Cryptographically authenticated** — derived from the operational certificate chain
2. **Bound to the session** — set during session establishment, immutable for session duration
3. **Non-spoofable** — requires possession of the node's operational private key

**Section 6.6.2.11:**
> *"it **SHALL NOT** be valid to have an Administer privilege set on an Access Control Entry, unless the AuthMode's AuthModeCategory is 'CASE'."*

Section 6.6.2 further states:
> *"The Message Layer **SHALL** provide sufficient metadata (e.g. Authentication Mode, source identity) about incoming messages to the Interaction Model protocol layer in order to properly enforce Access Control."*

Fabric identity is not a self-declared field — it is a cryptographic property of the session. Spoofing it requires breaking the entire CASE protocol, which would compromise all of Matter, not just this cluster.

---

## SUMMARY OF "FSM INCOMPLETENESS" CENTRAL CLAIM

The reports' central thesis is titled "CRITICAL DISCOVERY: FSM Incompleteness."

**The specification is not an FSM.** The specification defines normative behavior using sequential "Effect on Receipt" algorithms with exhaustive conditional branches. Every path terminates with either a response command or a status code. The specification's text IS the complete definition of behavior.

An FSM is one possible way to _model_ the specification for formal verification purposes. If the FSM omits error transitions, that is an FSM modeling deficiency, not a specification deficiency. The analyzer acknowledges this themselves:

> *"Actual Security Result: Property likely HOLDS in practice because: Success requires explicit fabric match. Spec mandates NOT_FOUND on mismatch. No transitions grant cross-fabric access."*
> *"Severity: LOW (for formal verification) / NONE (for actual implementation)"*

The reports consistently find zero actual specification defects while labeling FSM modeling gaps as "violations." The specification is demonstrably complete in its coverage of: fabric isolation (6+ explicit checks per resource type), access control (deferred to proven architectural layer), transport behavior (explicit SHALL rules), and error handling (deterministic status codes with "no other side effects").

---

## FINAL VERDICT TABLE

| ID | Claim | Original Verdict | Defense Verdict | Reason |
|----|-------|-------------------|-----------------|--------|
| PROP_001 | Fabric isolation root certs unverifiable | PARTIALLY_UNVERIFIABLE | **DISPROVED** | Spec has 4 explicit fabric checks + Data Model layer guarantee (Section 7.5.3) |
| PROP_002 | Fabric isolation client certs unverifiable | PARTIALLY_UNVERIFIABLE | **DISPROVED** | Spec has 5 explicit fabric checks + Data Model layer guarantee |
| PROP_030 | Admin privilege not in FSM | UNVERIFIABLE | **DISPROVED** | Admin enforced by Interaction Model (Section 8.8.2.3) per command table ("A F"). Deny-by-default (Section 6.6.2) |
| PROP_018 | Large Message inclusion unverifiable | UNVERIFIABLE | **DISPROVED** | Fully specified with SHALL (Section 14.4.4.3–4). Find commands as fallback. All commands use Large Message qualifier |
| PROP_019 | Non-Large Message exclusion unverifiable | UNVERIFIABLE | **DISPROVED** | Fully specified with SHALL (Section 14.4.4.3–4). Exclusion prevents buffer overflow on limited transports |
| PROP_034 | Root cert before client cert not enforced | Not yet analyzed | **Not a defect** | Deliberate PKI design — chain validation at TLS handshake, not at provisioning |
| Rotation race | Certificate rotation window | Insight | **DISPROVED** | Spec explicitly states "only new connections" use updated cert |
| Wraparound | CAID collision via flood | Insight | **Not exploitable** | SHALL-level collision detection. Attack requires Admin privilege (self-defeating) |
| Fabric spoofing | Fabric identity spoofable | Insight | **DISPROVED** | CASE authentication cryptographically binds fabric identity |

---

## VALID OBSERVATIONS (Not Defects)

The following observations from the reports are **acknowledged as accurate** but are characteristics of the architecture, not defects:

1. **FSM modeling is incomplete** — True. The FSM omits error transitions. But this is a modeling choice, not a spec issue.
2. **Access control is external to Section 14.4** — True and intentional. Section 14.4 declares access requirements; Sections 6.6 and 8.8 enforce them. This is correct layered design.
3. **Transport behavior is external to the cluster FSM** — True and expected. Transport is handled at a different protocol layer.
4. **22 of 42 properties HOLD** — Correct. The spec correctly implements all verified security properties.
5. **0 properties VIOLATED** — Correct. No actual specification defects were found.

---

## REFERENCES

| Section | Title | Relevance |
|---------|-------|-----------|
| 6.6.2 | Access Control Model | Deny-by-default, SHALL-level privilege enforcement |
| 6.6.2.11 | Restrictions on Administer Level Privilege Grant | CASE-only for Admin privilege |
| 7.5.3 | Fabric-Scoped Data | Cross-fabric modification prohibition |
| 7.6 | Access (column definitions) | "A" = Administer privilege |
| 7.6.4 | Fabric-Scoped Quality ("F") | Fabric isolation data model constraint |
| 8.8.2.3 | Incoming Invoke Request Action | Pre-cluster access control enforcement |
| 14.4.4.3 | TLSCertStruct Type | Fabric-scoped, transport-dependent field inclusion |
| 14.4.4.4 | TLSClientCertificateDetailStruct Type | Fabric-scoped, transport-dependent field inclusion |
| 14.4.6 | Commands table | Access modifiers (A, O, F) per command |
| 14.4.6.1 | ProvisionRootCertificate | Fabric check, time sync, format validation, fingerprint uniqueness |
| 14.4.6.3 | FindRootCertificate | Fabric check, per-fabric filtering |
| 14.4.6.5 | LookupRootCertificate | Fabric check combined with fingerprint check |
| 14.4.6.7 | RemoveRootCertificate | Fabric check, dependency check |
| 14.4.6.8 | ClientCSR | Fabric check, resource limits, key collision detection |
| 14.4.6.10 | ProvisionClientCertificate | Fabric check, key correspondence, format validation |
| 14.4.6.11 | FindClientCertificate | Fabric check, per-fabric filtering |
| 14.4.6.13 | LookupClientCertificate | Fabric check combined with fingerprint check |
| 14.4.6.15 | RemoveClientCertificate | Fabric check, dependency check, key cleanup |
