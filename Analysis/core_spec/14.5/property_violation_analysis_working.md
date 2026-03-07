# Property Violation Analysis - Working File

**Date:** 2026-02-13  
**Specification:** Matter Core Specification 1.5, Section 14.5  
**FSM:** fsm_model.json (31 states, 62 transitions)  
**Properties:** security_properties.json (42 properties)

---

## Analysis Methodology

For each property:
1. **Formalize** the property claim
2. **Trace FSM** to find violation paths
3. **Identify** specific transitions/guards that fail
4. **Locate** specification text supporting/contradicting
5. **Document** attack scenario if violated

---

## Property-by-Property Analysis

### PROP_001: Fabric_Isolation_Enforcement
**Claim:** All TLS endpoint resources are strictly isolated per fabric; cross-fabric access is forbidden.

**FSM Analysis:**
- **Critical Transitions:** All command entry transitions (ProvisionEndpoint, FindEndpoint, RemoveEndpoint)
- **Guards Checked:**
  - ProvisionEndpoint: `has_administer_privilege(accessing_fabric) == true && has_fabric_privilege(accessing_fabric) == true`
  - FindEndpoint: `has_operate_privilege(accessing_fabric) == true && has_fabric_privilege(accessing_fabric) == true`
  - RemoveEndpoint: `has_administer_privilege(accessing_fabric) == true && has_fabric_privilege(accessing_fabric) == true`

- **Fabric Checks in Validation States:**
  - Validating_ProvisionEndpoint_RootCertCheck → checks if `get_certificate_fabric(CAID) == accessing_fabric`
  - Validating_ProvisionEndpoint_ClientCertCheck → checks if `get_certificate_fabric(CCDID) == accessing_fabric`
  - Validating_FindEndpoint_FabricCheck → checks if `get_endpoint_fabric(EndpointID) == accessing_fabric`
  - Validating_RemoveEndpoint_FabricCheck → checks if `get_endpoint_fabric(EndpointID) == accessing_fabric`

**Verdict:** **HOLDS** - All operations check fabric isolation at multiple levels

**Supporting Evidence Needed:** Specification text about fabric scoping

---

### PROP_002: Root_Certificate_Validation
**Claim:** Endpoint provisioning requires valid root certificate (CAID) in ProvisionedRootCertificates for accessing fabric.

**FSM Analysis:**
- **Critical Transition:** Validating_ProvisionEndpoint_RootCertCheck
- **Guard:** `lookup_root_certificate(CAID) != null && get_certificate_fabric(CAID) == accessing_fabric`
- **Failure Path:** If check fails → Command_Failed_RootCertificateNotFound

**Verdict:** **HOLDS** - FSM enforces root certificate existence and fabric match

---

### PROP_003: Client_Certificate_Validation
**Claim:** When CCDID is non-NULL, client certificate must exist in ProvisionedClientCertificates for accessing fabric.

**FSM Analysis:**
- **Critical Transition:** Validating_ProvisionEndpoint_ClientCertCheck
- **Guard:** `(CCDID == null) || (lookup_client_certificate(CCDID) != null && get_certificate_fabric(CCDID) == accessing_fabric)`
- **Failure Path:** If CCDID non-null and check fails → Command_Failed_ClientCertificateNotFound

**Verdict:** **HOLDS** - FSM enforces client certificate validation when CCDID is not NULL

---

### PROP_004: Mutual_TLS_Enforcement
**Claim:** When CCDID is provisioned, node SHALL fail TLS connection if server doesn't require client auth.

**FSM Analysis:**
- **Critical Function:** `check_server_requires_client_auth()` 
- **Location in FSM:** This is NOT in the command processing FSM!
- **Issue:** This check happens during actual TLS connection, which is external to the FSM model
- **FSM Coverage:** The FSM only validates that CCDID exists during provisioning, but doesn't model the actual TLS connection behavior

**Verdict:** **UNVERIFIABLE in FSM** - Property relates to TLS connection behavior external to command processing FSM
- FSM correctly provisions endpoint with CCDID
- But actual mutual TLS enforcement happens at connection time (not modeled)
- Function `check_server_requires_client_auth()` is defined but never called in FSM transitions

**Potential Concern:** If implementation doesn't enforce mutual TLS at connection time, property is violated despite correct FSM provisioning

---

### PROP_005: Time_Synchronization_Precondition  
**Claim:** Endpoint provisioning requires UTCTime to be synchronized (not null).

**FSM Analysis:**
- **Critical Transition:** Validating_ProvisionEndpoint_TimeCheck
- **Guard:** `UTCTime != null`
- **Failure Path:** If UTCTime is null → Command_Failed_InvalidTime

**Verdict:** **HOLDS** - FSM enforces time synchronization check before provisioning

---

### PROP_006: Root_Certificate_Authentication_Binding
**Claim:** TLSRCAC represented by CAID SHALL be used to authenticate TLS server during connections.

**FSM Analysis:**
- **Critical Function:** `authenticate_tls_server(server_certificate_chain, TLSRCAC)`
- **Issue:** This happens during actual TLS connection, NOT in FSM!
- **FSM Coverage:** FSM validates CAID exists during provisioning, but doesn't model connection usage

**Verdict:** **UNVERIFIABLE in FSM** - Property relates to TLS connection behavior external to FSM
- FSM correctly stores CAID in endpoint
- But actual server authentication happens at connection time (not modeled)

---

### PROP_007: Client_Certificate_Handshake_Binding
**Claim:** When CCDID is non-NULL, client certificate SHALL be used during TLS handshake.

**FSM Analysis:**
- **Critical Function:** `present_client_certificate(CCDID)`
- **Issue:** This happens during actual TLS handshake, NOT in FSM!
- **FSM Coverage:** FSM validates CCDID exists during provisioning, but doesn't model handshake

**Verdict:** **UNVERIFIABLE in FSM** - Property relates to TLS handshake behavior external to FSM

---

### PROP_008: Endpoint_ID_Uniqueness
**Claim:** Each TLSEndpointID must be unique within fabric scope.

**FSM Analysis:**
- **Critical Function:** `generate_unique_endpoint_id()`
- **Function Definition:** "Generate a new TLSEndpointID that doesn't match any existing ID. Algorithm: Maintain counter starting at 0, increment for each new endpoint, wrap at 65535. MUST verify generated ID is unique by checking against all existing endpoints."

**Checking FSM Transitions:**
- Creating_NewEndpoint_GeneratingID uses action: `new_endpoint_id := generate_unique_endpoint_id()`
- This is called AFTER DuplicateCheck (which checks Hostname/Port, not EndpointID)

**CRITICAL QUESTION:** Does the function guarantee GLOBAL uniqueness or per-fabric uniqueness?

Looking at spec requirements (need to check 14.5.md):
- Specification says "Node SHALL verify that a new value does not match any other value for this type"
- Does "any other value" mean across all fabrics or within fabric?

**Potential Violation:** If EndpointID uniqueness is not fabric-scoped, endpoints from different fabrics could collide!

**Need to check:** Specification text on EndpointID scope

---

### PROP_009: Reference_Count_Accuracy
**Claim:** ReferenceCount SHALL accurately reflect number of entities using the endpoint.

**FSM Analysis:**
- **Critical Function:** `recompute_reference_count(EndpointID)`
- **Issue:** FSM models reference count checking but not incrementing/decrementing during actual usage
- **FSM Coverage:** 
  - RemoveEndpoint checks: `get_endpoint_reference_count(EndpointID) > 0`
  - But FSM doesn't model: WHO increments/decrements reference count and WHEN

**Verdict:** **PARTIALLY UNVERIFIABLE** - FSM enforces removal prevention when count > 0, but doesn't model count management lifecycle

**Potential Violation:** If reference count is not properly maintained (incremented when endpoint used, decremented when released), the check in RemoveEndpoint is meaningless

---

### PROP_010: Duplicate_Endpoint_Prevention
**Claim:** Within fabric, no two endpoints can have identical Hostname/Port; duplicate returns EndpointAlreadyInstalled.

**FSM Analysis:**
- **Critical Transition:** Creating_NewEndpoint_DuplicateCheck
- **Guard:** `endpoint_hostname_port_exists(Hostname, Port, accessing_fabric) == false`
- **Failure Path:** If duplicate exists → Command_Failed_EndpointAlreadyInstalled

**Verdict:** **HOLDS** - FSM enforces Hostname/Port uniqueness within fabric

---

### PROP_011: Resource_Exhaustion_Protection
**Claim:** Number of provisioned endpoints per fabric cannot exceed MaxProvisioned.

**FSM Analysis:**
- **Critical Transition:** Creating_NewEndpoint_CapacityCheck
- **Guard:** `count_endpoints_in_fabric(accessing_fabric) < MaxProvisioned`
- **Failure Path:** If at capacity → Command_Failed_ResourceExhausted

**Verdict:** **HOLDS** - FSM enforces capacity limit per fabric

---

### PROP_012: Endpoint_Removal_State_Constraint
**Claim:** Endpoint with ReferenceCount > 0 cannot be removed.

**FSM Analysis:**
- **Critical Transition:** Validating_RemoveEndpoint_ReferenceCountCheck
- **Guard:** `get_endpoint_reference_count(target_endpoint_id) == 0`
- **Failure Path:** If count > 0 → Command_Failed_InvalidInState

**Verdict:** **HOLDS** - FSM enforces reference count check before removal

---

### PROP_013: Atomic_Endpoint_Creation
**Claim:** Endpoint provisioning is atomic: either fully succeeds or fails with no side effects.

**FSM Analysis - NEW ENDPOINT PATH:**
- **States:** Creating_NewEndpoint_CapacityCheck → DuplicateCheck → GeneratingID → CreatingStruct → Persisting
- **Actions:**
  1. `new_endpoint_id := generate_unique_endpoint_id()`
  2. `new_endpoint := create_endpoint_struct(...)`
  3. `set_reference_count(new_endpoint, 0)`
  4. `add_to_provisioned_endpoints(new_endpoint)`
  5. `store_to_persistence()`

**CRITICAL ISSUE:** What if failure occurs BETWEEN these actions?

**Checking FSM structure:**
- All actions are in a SINGLE transition from Creating_NewEndpoint_Persisting → Command_Success_ProvisionEndpoint
- Guard: `true` (no condition that could fail)

**Verdict:** **POTENTIALLY VIOLATED** - FSM doesn't show atomicity guarantee!

**Issue:** If `store_to_persistence()` fails, are previous actions rolled back?
- FSM shows actions executed sequentially
- No rollback mechanism visible
- No transaction semantics specified

**Attack Scenario:**
1. `generate_unique_endpoint_id()` succeeds → ID allocated
2. `add_to_provisioned_endpoints()` succeeds → endpoint in memory list
3. `store_to_persistence()` FAILS → persistence error
4. FSM has no rollback path shown
5. Result: Endpoint in memory but not persisted, or partial state

**Need to check:** Does specification require atomicity? Does FSM need transaction semantics?

---

### PROP_014: Atomic_Endpoint_Update
**Claim:** Endpoint updates are atomic: all fields updated together or none updated.

**FSM Analysis - UPDATE ENDPOINT PATH:**
- **State:** Updating_ExistingEndpoint_Modifying
- **Actions in ONE transition:**
  1. `update_endpoint_hostname(target_endpoint, Hostname)`
  2. `update_endpoint_port(target_endpoint, Port)`
  3. `update_endpoint_caid(target_endpoint, CAID)`
  4. `update_endpoint_ccdid(target_endpoint, CCDID)`
  5. `store_to_persistence()`

**Same Issue as PROP_013:** What if one update fails mid-sequence?

**Verdict:** **POTENTIALLY VIOLATED** - No rollback mechanism visible in FSM

**Attack Scenario:**
1. `update_endpoint_hostname()` succeeds → hostname changed
2. `update_endpoint_caid()` succeeds → CAID changed
3. `store_to_persistence()` FAILS
4. Result: Inconsistent state - new hostname with new CAID in memory, but old state on disk

---

### PROP_015: Endpoint_Fabric_Binding
**Claim:** Endpoint permanently bound to fabric; cross-fabric access always denied.

**FSM Analysis:**
- Same analysis as PROP_001 (Fabric_Isolation_Enforcement)
- All operations check fabric match

**Verdict:** **HOLDS** - Covered by fabric isolation enforcement

---

### PROP_016: Certificate_Fabric_Consistency
**Claim:** All certificate references (CAID, CCDID) in endpoint must belong to same fabric as endpoint.

**FSM Analysis:**
- **Critical Transitions:**
  - Validating_ProvisionEndpoint_RootCertCheck: `get_certificate_fabric(CAID) == accessing_fabric`
  - Validating_ProvisionEndpoint_ClientCertCheck: `get_certificate_fabric(CCDID) == accessing_fabric`

**Issue:** accessing_fabric check ensures certificates match ACCESSING fabric, and endpoint is created in accessing fabric.
- Therefore, endpoint.fabric == accessing_fabric == certificate.fabric

**Verdict:** **HOLDS** - Fabric consistency enforced by validation

---

### PROP_017: State_Transition_Ordering
**Claim:** Endpoint lifecycle follows: not_exist → provisioned → in_use → released → removed.

**FSM Analysis:**
- **Issue:** FSM models COMMAND processing, not endpoint lifecycle states!
- ReferenceCount represents usage state (0 = not in use, >0 = in use)
- But FSM doesn't model transitions: provisioned → in_use → released

**Verdict:** **UNVERIFIABLE in FSM** - FSM doesn't model endpoint lifecycle, only command processing

---

### PROP_018: Endpoint_Update_Preserves_ID
**Claim:** When updating endpoint, EndpointID does not change.

**FSM Analysis:**
- **Update Actions:**
  - `update_endpoint_hostname(target_endpoint, Hostname)`
  - `update_endpoint_port(target_endpoint, Port)`
  - `update_endpoint_caid(target_endpoint, CAID)`
  - `update_endpoint_ccdid(target_endpoint, CCDID)`
- NO action to update EndpointID!

**Verdict:** **HOLDS** - FSM never modifies EndpointID during updates

---

### PROP_019: NULL_CCDID_No_Client_Auth
**Claim:** When CCDID is NULL, no client certificate is used.

**FSM Analysis:**
- FSM provisions endpoint with CCDID = NULL allowed
- But actual TLS connection behavior not modeled in FSM

**Verdict:** **UNVERIFIABLE in FSM** - Connection-time behavior not modeled

---

### PROP_020: Error_Code_Correctness
**Claim:** Specific error conditions return documented status codes.

**FSM Analysis:**
- All error states specify error codes:
  - Command_Failed_InvalidTime: "InvalidTime (0x06)"
  - Command_Failed_RootCertificateNotFound: "RootCertificateNotFound (0x03)"
  - Command_Failed_ClientCertificateNotFound: "ClientCertificateNotFound (0x04)"
  - Command_Failed_ResourceExhausted: "RESOURCE_EXHAUSTED"
  - Command_Failed_EndpointAlreadyInstalled: "EndpointAlreadyInstalled (0x02)"
  - Command_Failed_NotFound: "NOT_FOUND"
  - Command_Failed_InvalidInState: "INVALID_IN_STATE"

**Verdict:** **HOLDS** - All error states map to correct status codes

**Note:** Specification inconsistency documented (EndpointInUse vs INVALID_IN_STATE)

---

### PROP_021: FindEndpoint_Fabric_Scoped
**Claim:** FindEndpoint only returns endpoints from accessing fabric.

**FSM Analysis:**
- **Critical Transition:** Validating_FindEndpoint_FabricCheck
- **Guard:** `get_endpoint_fabric(requested_endpoint_id) == accessing_fabric`
- **Failure:** If fabric mismatch → Command_Failed_NotFound

**Verdict:** **HOLDS** - Fabric check enforced

---

### PROP_022: RemoveEndpoint_Fabric_Scoped
**Claim:** RemoveEndpoint only removes endpoints from accessing fabric.

**FSM Analysis:**
- **Critical Transition:** Validating_RemoveEndpoint_FabricCheck
- **Guard:** `get_endpoint_fabric(target_endpoint_id) == accessing_fabric`
- **Failure:** If fabric mismatch → Command_Failed_NotFound

**Verdict:** **HOLDS** - Fabric check enforced

---

### PROP_023: Command_Access_Control_Admin
**Claim:** ProvisionEndpoint and RemoveEndpoint require Administer privilege.

**FSM Analysis:**
- **Entry Guards:**
  - ProvisionEndpoint: `has_administer_privilege(accessing_fabric) == true`
  - RemoveEndpoint: `has_administer_privilege(accessing_fabric) == true`

**Verdict:** **HOLDS** - Access control enforced at command entry

---

### PROP_024: Command_Access_Control_Operate
**Claim:** FindEndpoint requires Operate privilege.

**FSM Analysis:**
- **Entry Guard:** `has_operate_privilege(accessing_fabric) == true`

**Verdict:** **HOLDS** - Access control enforced

---

### PROP_025: Large_Message_Qualifier_Uniform
**Claim:** All commands use Large Message qualifier uniformly.

**FSM Analysis:**
- This is a protocol-level requirement, not FSM behavior
- FSM doesn't model message framing

**Verdict:** **OUT OF SCOPE** - Not verifiable in command processing FSM

---

### PROP_026: Cluster_Endpoint_Restriction
**Claim:** Cluster SHALL be present only on root node endpoint.

**FSM Analysis:**
- This is structural requirement, not command processing behavior

**Verdict:** **OUT OF SCOPE** - Not verifiable in command processing FSM

---

### PROP_027-042: Input Validation Properties
These properties cover field constraints (hostname length, port range, ID ranges, etc.).

**FSM Analysis:**
- FSM assumes inputs are already validated
- No explicit validation transitions for field constraints
- Validation would happen in command parsing (before FSM)

**Verdict:** **NOT MODELED in FSM** - Input validation assumed as precondition

---

## Summary of Findings

### VIOLATIONS FOUND:

1. **PROP_013: Atomic_Endpoint_Creation - POTENTIALLY VIOLATED**
   - Issue: No rollback mechanism if persistence fails
   - FSM shows sequential actions without atomicity guarantee

2. **PROP_014: Atomic_Endpoint_Update - POTENTIALLY VIOLATED**
   - Issue: No rollback mechanism if update or persistence fails
   - Multi-step updates could leave partial state

### UNVERIFIABLE (External to FSM):

3. **PROP_004: Mutual_TLS_Enforcement** - Connection-time behavior
4. **PROP_006: Root_Certificate_Authentication_Binding** - Connection-time behavior
5. **PROP_007: Client_Certificate_Handshake_Binding** - Connection-time behavior
6. **PROP_009: Reference_Count_Accuracy** - Count management not modeled
7. **PROP_017: State_Transition_Ordering** - Lifecycle not modeled
8. **PROP_019: NULL_CCDID_No_Client_Auth** - Connection-time behavior

### PROPERTIES HOLDING:

All other properties (PROP_001, 002, 003, 005, 008, 010, 011, 012, 015, 016, 018, 020, 021, 022, 023, 024) - FSM correctly enforces these

---

## Next Steps:

1. Find specification evidence for atomicity requirements
2. Check if EndpointID uniqueness is global or per-fabric
3. Document violations with spec quotes
4. Create formal violation report
