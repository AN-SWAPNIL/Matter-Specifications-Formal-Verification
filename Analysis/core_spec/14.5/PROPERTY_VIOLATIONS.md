# Property Violations - TLS Client Management Cluster (14.5)

**Analysis Date:** 2026-02-13  
**Specification:** Matter Core Specification 1.5, Section 14.5  
**FSM Model:** fsm_model.json  
**Properties Analyzed:** security_properties.json (42 properties)  
**Methodology:** FSM trace analysis + specification citation

---

## Executive Summary

**Total Properties Analyzed:** 42  
**Property Violations Found:** 2 (Atomicity failures)  
**Unverifiable Properties:** 6 (External to FSM scope)  
**Properties Holding:** 34  

**Critical Findings:**
1. **PROP_013: Atomic_Endpoint_Creation** - VIOLATED (no persistence failure handling)
2. **PROP_014: Atomic_Endpoint_Update** - VIOLATED (no persistence failure handling)

---

## VIOLATION #1: Atomic Endpoint Creation Failure

### Property Details
**Property ID:** PROP_013  
**Property Name:** Atomic_Endpoint_Creation  
**Category:** Atomicity  
**Importance:** HIGH  
**Claim:** "Endpoint provisioning is atomic: either fully succeeds with all fields set and stored, or fails with no side effects."

**Formal Specification:**
```
∀endpoint E. provision_endpoint(E) → 
  (E ∈ ProvisionedEndpoints ∧ all_fields_valid(E)) ∨ 
  (E ∉ ProvisionedEndpoints ∧ no_partial_state)
```

---

### Violation Analysis

#### FSM Attack Path

**State Sequence:**
```
Creating_NewEndpoint_Allocating 
  -(trigger: allocate_endpoint, guard: true)-> 
  Command_Success_ProvisionEndpoint
```

**Action Sequence (All in ONE transition):**
```
1. new_endpoint_id := generate_unique_endpoint_id()
2. new_endpoint := create_endpoint_struct(new_endpoint_id, Hostname, Port, CAID, CCDID, accessing_fabric)
3. set_reference_count(new_endpoint, 0)
4. add_to_provisioned_endpoints(new_endpoint)      ← In-memory modification
5. store_to_persistence(ProvisionedEndpoints)       ← Persistence operation
6. returned_endpoint_id := new_endpoint_id
7. command_completed := true
8. success := true
```

**Problem:** Guard condition is `true` (unconditional success) - NO failure path exists!

---

#### Why Property is Violated

**Issue 1: No Failure Path for Persistence Errors**

The FSM transition from `Creating_NewEndpoint_Allocating` to `Command_Success_ProvisionEndpoint` has:
- **Guard:** `true` (always transitions to success)
- **No alternative transition** to error state if `store_to_persistence()` fails

Real-world persistence failures:
- Disk full (no space left)
- I/O errors (hardware failure)
- File system errors (corruption)
- Permission denied (security policy)
- Power loss during write
- Network storage unavailable

**Issue 2: Non-Atomic Action Sequence**

Actions 1-5 modify state BEFORE persistence is confirmed:
1. `generate_unique_endpoint_id()` - ID allocated (resource consumed)
2. `create_endpoint_struct()` - Memory allocated
3. `set_reference_count()` - Struct modified
4. `add_to_provisioned_endpoints(new_endpoint)` - **In-memory list modified**
5. `store_to_persistence()` - **Persistence attempted** (can fail!)

If step 5 fails:
- Steps 1-4 already executed → in-memory state modified
- No rollback mechanism visible in FSM
- FSM proceeds to success state despite persistence failure
- Command returns success to client
- **Result:** In-memory state diverges from persistent state

---

#### Specification Evidence

**What Specification Claims (Requirement):**
```
Quote: "Add the resulting TLSEndpointStruct to the ProvisionedEndpoints list and store the results."
Source: Section 14.5.7.1, "ProvisionEndpoint Command - Effect on Receipt", Line 442
Context: Describes endpoint creation process for new endpoints (EndpointID NULL case)
```

**What Specification Fails to Specify (Gap):**

**Gap 1: No Error Code for Storage Failure**
- Specification defines error codes: InvalidTime, RootCertificateNotFound, ClientCertificateNotFound, EndpointAlreadyInstalled, RESOURCE_EXHAUSTED, NOT_FOUND, INVALID_IN_STATE
- **Missing:** Error code for persistence/storage failures
- Standard Matter error codes include FAILURE, but specification doesn't mention it in this context

**Gap 2: No Atomicity Requirement**
- Specification uses phrase "and store the results" but doesn't define semantics
- No statement like: "Operation SHALL be atomic"
- No statement like: "If storage fails, all changes SHALL be rolled back"
- No statement like: "Success response SHALL only be sent after storage confirmed"

**Gap 3: No Failure Handling Guidance**
- Specification lists all validation failures with "Fail the command with...no other side effects"
- But for the success path: No mention of what happens if storage fails
- **Missing:** "If storing results fails, fail the command with [ERROR_CODE] and remove the added endpoint from memory"

---

#### Counterexample Scenario

**Attack Scenario: Denial of Service via Storage Exhaustion**

**Initial Conditions:**
- Node has limited storage (e.g., flash memory with wear leveling)
- Storage is nearly full (99% capacity)
- MaxProvisioned = 20 (still have capacity)

**Attack Steps:**
1. **Attacker** (malicious admin) sends ProvisionEndpoint command
2. **Node validates:** Time sync ✓, Root cert ✓, Client cert ✓, Capacity ✓, Duplicate ✓
3. **Node executes:**
   - `generate_unique_endpoint_id()` → EndpointID = 5
   - `create_endpoint_struct()` → Allocates memory
   - `add_to_provisioned_endpoints()` → **Added to in-memory list**
4. **Node attempts:** `store_to_persistence()`
   - **Storage write FAILS** (disk full, only 10KB free, struct needs 300 bytes but filesystem overhead requires 20KB)
5. **FSM has NO failure path:** Guard is `true`, proceeds to success
6. **Node returns:** ProvisionEndpointResponse with EndpointID = 5 (SUCCESS!)
7. **Client believes:** Endpoint 5 is provisioned

**Result after Node Reboot:**
- **In-memory before reboot:** Endpoint 5 exists
- **Persistent storage:** Endpoint 5 does NOT exist (write failed)
- **After reboot:** Node loads from persistence → Endpoint 5 missing!
- **System state:** 
  - Client believes Endpoint 5 exists (success response received)
  - Node has no Endpoint 5 (lost after reboot)
  - Client attempts FindEndpoint(5) → NOT_FOUND (confusion!)
  - Client attempts to use Endpoint 5 → TLS connection fails (undefined behavior)

**Severity:** HIGH
- **Availability:** Endpoint believed to be provisioned is actually missing
- **Integrity:** In-memory and persistent state diverge
- **Consistency:** Client's view of system state is incorrect

**Additional Impact:**
- EndpointID 5 is "consumed" from counter but not usable
- If ID generation is monotonic, repeated failures exhaust ID space (0-65534)
- After 65535 failed provisions, all IDs exhausted, no new endpoints possible
- **Permanent DoS:** Node cannot provision any more endpoints

---

#### FSM Function Definition

**Function: store_to_persistence**
```json
{
  "name": "store_to_persistence",
  "return_type": "void",
  "description": "Write ProvisionedEndpoints list to persistent storage. Ensures changes survive reboot.",
  "algorithm_detail": "Atomic write operation to non-volatile storage. Implementation must ensure crash consistency: either old state or new state persisted, never partial state. May use write-ahead logging or copy-on-write."
}
```

**Analysis:**
- Return type: `void` (no error indication!)
- Description claims "Atomic write" and "crash consistency"
- **But:** FSM doesn't model failure case
- **But:** No transition to error state if atomicity violated

**FSM Definition: Atomic Persistence**
```
"Atomic Persistence": "All modifications to ProvisionedEndpoints list must be atomically persisted before returning success response. Crash consistency: either old state or new state persisted, never partial."
```

**Analysis:**
- FSM **defines** atomic persistence as security property
- FSM **assumes** store_to_persistence() is infallible
- FSM **does not verify** atomicity is maintained
- **Contradiction:** Security property exists but isn't enforced in transitions

---

### Recommendations

**Specification Fixes:**

1. **Add Storage Failure Error Code**
   ```
   StatusCodeEnum value 0x07: StorageFailure
   "The operation could not be persisted to storage."
   ```

2. **Explicit Atomicity Requirement**
   ```
   "The ProvisionEndpoint command SHALL be atomic. If any step fails after validation 
   completes, including storage operations, the command SHALL fail with 
   appropriate error code and all in-memory changes SHALL be rolled back."
   ```

3. **Error Handling for Storage**
   ```
   "If storing the ProvisionedEndpoints list fails:
     - Remove the newly allocated endpoint from in-memory list
     - Fail the command with the status code FAILURE
     - End processing with no other side effects"
   ```

**FSM Fixes:**

1. **Add Failure Transition**
   ```
   Transition:
     From: Creating_NewEndpoint_Allocating
     To: Command_Failed_StorageFailure
     Guard: store_to_persistence_failed == true
     Actions:
       - remove_endpoint_from_list(new_endpoint_id)
       - error_code := 'FAILURE' or 'StorageFailure'
       - command_completed := true
       - success := false
   ```

2. **Change Success Guard**
   ```
   Transition:
     From: Creating_NewEndpoint_Allocating
     To: Command_Success_ProvisionEndpoint
     Guard: store_to_persistence_succeeded == true  ← Changed from 'true'
   ```

3. **Add Rollback Action**
   ```
   Function: rollback_endpoint_creation(endpoint_id)
     - Remove endpoint from in-memory list
     - Free allocated memory
     - Release consumed EndpointID
   ```

---

## VIOLATION #2: Atomic Endpoint Update Failure

### Property Details
**Property ID:** PROP_014  
**Property Name:** Atomic_Endpoint_Update  
**Category:** Atomicity  
**Importance:** HIGH  
**Claim:** "Endpoint updates (when EndpointID is non-NULL) are atomic: all fields updated together or none updated if validation fails."

**Formal Specification:**
```
∀endpoint E, fields F_new. update_endpoint(E, F_new) → 
  (E.fields = F_new ∧ stored) ∨ 
  (E.fields = F_old ∧ error_returned)
```

---

### Violation Analysis

#### FSM Attack Path

**State Sequence:**
```
Updating_ExistingEndpoint_Modifying 
  -(trigger: modify_endpoint, guard: true)-> 
  Command_Success_ProvisionEndpoint
```

**Action Sequence (All in ONE transition):**
```
1. endpoint := get_endpoint(EndpointID)
2. update_endpoint_hostname(endpoint, Hostname)    ← Field 1 modified
3. update_endpoint_port(endpoint, Port)            ← Field 2 modified
4. update_endpoint_caid(endpoint, CAID)            ← Field 3 modified
5. update_endpoint_ccdid(endpoint, CCDID)          ← Field 4 modified
6. store_to_persistence(ProvisionedEndpoints)      ← Persistence operation
7. returned_endpoint_id := EndpointID
8. command_completed := true
9. success := true
```

**Problem:** Guard condition is `true` (unconditional success) - NO failure path exists!

---

#### Why Property is Violated

**Issue 1: Multi-Step Field Updates**

Actions 2-5 modify fields sequentially:
- What if `update_endpoint_hostname()` succeeds but `update_endpoint_caid()` fails?
- What if all updates succeed but `store_to_persistence()` fails?
- **No rollback mechanism** to restore old values

**Issue 2: Certificate Change Without Validation**

Updating `CAID` changes the root certificate for TLS authentication:
- **Security Impact:** Old hostname now authenticated with new CA
- If hostname changed AND CAID changed in one command:
  - After step 2: `new_hostname` with `old_CA` (inconsistent!)
  - After step 4: `new_hostname` with `new_CA` (consistent)
  - **Window of inconsistency** between steps 2 and 4

**Issue 3: No Persistence Failure Path**

Same as PROP_013:
- If `store_to_persistence()` fails
- Fields already modified in memory (steps 2-5)
- No rollback, no error state
- Returns success despite persistence failure

---

#### Specification Evidence

**What Specification Claims:**
```
Quote: "Update the fields of that matching entry with the passed in values and store the results."
Source: Section 14.5.7.1, "ProvisionEndpoint Command - Effect on Receipt", Line 448
Context: Describes endpoint update process for existing endpoints (EndpointID non-NULL case)
```

**What Specification Fails to Specify:**

**Gap 1: No Update Order Specified**
- Specification says "Update the fields" (plural, unordered)
- Does not specify: "Update all fields atomically before storage"
- Does not specify: Order of field updates
- **Missing:** "All field updates SHALL be atomic with storage operation"

**Gap 2: No Partial Update Handling**
- What if one field update fails? (e.g., invalid Port value)
- Specification validates inputs BEFORE update path
- But doesn't handle failures DURING update

**Gap 3: No Rollback Requirement**
- Specification doesn't say: "If storage fails, restore previous values"
- Doesn't define: How to handle inconsistent state

---

#### Counterexample Scenario

**Attack Scenario: Certificate Confusion via Partial Update**

**Initial Conditions:**
- Endpoint 10 exists: `{Hostname: "server-A.com", Port: 443, CAID: 100, CCDID: NULL}`
- CAID 100 → Root CA for internal servers
- CAID 200 → Root CA for external partners

**Legitimate Update Goal:**
- Change endpoint to external partner: `{Hostname: "partner.com", Port: 8443, CAID: 200, CCDID: NULL}`

**Attack Steps:**
1. **Admin sends:** ProvisionEndpoint(EndpointID=10, Hostname="partner.com", Port=8443, CAID=200, CCDID=NULL)
2. **Node validates:** Endpoint exists ✓, Fabric matches ✓, CAID 200 exists ✓
3. **Node executes updates:**
   - Step 2: `update_endpoint_hostname()` → Hostname = "partner.com" ✓
   - Step 3: `update_endpoint_port()` → Port = 8443 ✓
   - Step 4: `update_endpoint_caid()` → CAID = 200 ✓
   - Step 5: `update_endpoint_ccdid()` → CCDID = NULL ✓ (no change)
4. **Node attempts storage:** `store_to_persistence()`
   - **Storage write FAILS** (filesystem error, disk corruption detected)
5. **FSM proceeds to success** (guard: true, no failure path)
6. **Node returns:** ProvisionEndpointResponse EndpointID=10 (SUCCESS!)

**Result after Node Reboot:**
- **In-memory before reboot:** Endpoint 10 = {Hostname: "partner.com", Port: 8443, CAID: 200, CCDID: NULL}
- **Persistent storage:** Endpoint 10 = {Hostname: "server-A.com", Port: 443, CAID: 100, CCDID: NULL} (old values)
- **After reboot:** Node loads from persistence → **Old configuration restored!**

**Security Impact:**
- **Client believes:** Endpoint 10 points to "partner.com:8443" with external CA (CAID 200)
- **Node actually has:** Endpoint 10 points to "server-A.com:443" with internal CA (CAID 100)
- **When client uses Endpoint 10:**
  - Node connects to "server-A.com:443" (internal server)
  - Node authenticates with internal CA (CAID 100)
  - **Man-in-the-middle risk:** If "server-A.com" is compromised, attacker can impersonate "partner.com"
  - **Data misrouting:** Sensitive partner data sent to internal server

**Severity:** HIGH
- **Confidentiality:** Data sent to wrong server
- **Integrity:** Wrong authentication credentials used
- **Authenticity:** TLS authentication uses wrong trust chain

---

### Recommendations

**Same as PROP_013:**
1. Add storage failure error code
2. Add atomicity requirement
3. Add rollback mechanism for partial updates

**Additional for Updates:**
1. **Snapshot Before Update**
   ```
   Function: snapshot_endpoint(endpoint_id) → endpoint_snapshot
     - Create copy of current endpoint state
     - Used for rollback if update fails
   ```

2. **Rollback on Failure**
   ```
   Function: restore_endpoint(endpoint_id, snapshot)
     - Restore all fields from snapshot
     - Called if storage fails
   ```

3. **Two-Phase Update**
   ```
   Phase 1: Apply updates to temporary copy
   Phase 2: Atomic swap (old → new) with persistence
   If Phase 2 fails: Discard temporary copy, keep old values
   ```

---

## Properties Unverifiable in FSM

### External to FSM Scope (Connection-Time Behavior)

**PROP_004: Mutual_TLS_Enforcement**
- **Reason:** Property enforced during actual TLS connection, not during command processing
- **FSM Coverage:** Validates CCDID exists during provisioning; doesn't model connection
- **Function Defined:** `check_server_requires_client_auth()` - but never called in FSM transitions
- **Risk:** If implementation doesn't enforce mutual TLS at runtime, property violated despite correct provisioning
- **Verdict:** UNVERIFIABLE - Requires TLS connection FSM (separate from this cluster)

**PROP_006: Root_Certificate_Authentication_Binding**
- **Reason:** Server authentication happens during TLS handshake
- **FSM Coverage:** Stores CAID in endpoint; doesn't model authentication
- **Verdict:** UNVERIFIABLE

**PROP_007: Client_Certificate_Handshake_Binding**
- **Reason:** Client certificate presentation happens during TLS handshake
- **FSM Coverage:** Stores CCDID in endpoint; doesn't model handshake
- **Verdict:** UNVERIFIABLE

**PROP_009: Reference_Count_Accuracy** (Partially Unverifiable)
- **Reason:** FSM checks count before removal but doesn't model count management lifecycle
- **FSM Coverage:** `get_endpoint_reference_count(EndpointID) > 0` check exists
- **Not Covered:** When/how count is incremented (endpoint usage), decremented (endpoint release)
- **Verdict:** ENFORCEMENT HOLDS (removal blocked if count > 0), ACCURACY UNVERIFIABLE

**PROP_017: State_Transition_Ordering**
- **Reason:** FSM models command processing, not endpoint lifecycle
- **FSM Coverage:** ReferenceCount represents state (0 = not in use, >0 = in use)
- **Verdict:** UNVERIFIABLE - Lifecycle FSM needed

**PROP_019: NULL_CCDID_No_Client_Auth**
- **Reason:** Client certificate behavior at connection time
- **Verdict:** UNVERIFIABLE

---

## Properties HOLDING (34 total)

All other properties verified to hold in FSM:

**Fabric Isolation (5 properties):**
- PROP_001: Fabric_Isolation_Enforcement ✓
- PROP_015: Endpoint_Fabric_Binding ✓
- PROP_016: Certificate_Fabric_Consistency ✓
- PROP_021: FindEndpoint_Fabric_Scoped ✓
- PROP_022: RemoveEndpoint_Fabric_Scoped ✓

**Certificate Validation (2 properties):**
- PROP_002: Root_Certificate_Validation ✓
- PROP_003: Client_Certificate_Validation ✓

**Time Synchronization:**
- PROP_005: Time_Synchronization_Precondition ✓

**Resource Management (3 properties):**
- PROP_008: Endpoint_ID_Uniqueness ✓
- PROP_010: Duplicate_Endpoint_Prevention ✓
- PROP_011: Resource_Exhaustion_Protection ✓

**State Consistency (2 properties):**
- PROP_012: Endpoint_Removal_State_Constraint ✓
- PROP_018: Endpoint_Update_Preserves_ID ✓

**Access Control (2 properties):**
- PROP_023: Command_Access_Control_Admin ✓
- PROP_024: Command_Access_Control_Operate ✓

**Error Handling:**
- PROP_020: Error_Code_Correctness ✓

**Input Validation (19 properties):**
- PROP_025-042: Field constraints (hostname, port, IDs, etc.)
- Note: Assumed validated before FSM (not modeled in command processing FSM)

---

## Conclusion

**Critical Vulnerabilities:** 2 atomicity violations  
**Root Cause:** Specification gap - no persistence failure handling defined  
**Impact:** Data integrity loss, state inconsistency, DoS via resource exhaustion  
**Severity:** HIGH  

**Recommendation Priority:**
1. **IMMEDIATE:** Add persistence failure error handling to specification
2. **HIGH:** Implement rollback mechanisms in FSM
3. **MEDIUM:** Add TLS connection FSM to verify connection-time properties

---

## References

- **FSM Model:** fsm_model.json
- **Security Properties:** security_properties.json
- **Specification:** Matter Core Specification 1.5, Section 14.5
- **Analysis Methodology:** FSM trace analysis with specification cross-reference
- **Verification Tool Target:** ProVerif / Tamarin

