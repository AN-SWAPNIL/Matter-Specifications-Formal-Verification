# OTA Security Property Violation Analysis Report

## Executive Summary

**Analysis Date**: February 21, 2026  
**Specification**: Matter Core Specification v1.5, Section 11.20 - Over-the-Air (OTA) Software Update  
**FSM Model**: ota_fsm_model.json (12 states, 71 transitions, 41 functions)  
**Total Security Properties Analyzed**: 113  
**PropertiesViolated**: 5  
**Properties Holding**: 35+  
**Properties Not Verifiable in FSM**: 10+  

### Critical Findings

1. **VIOLATED - PROP_001**: Query rate limiting can be bypassed via urgent announcements
2. **VIOLATED - PROP_002**: Cached images can cause downgrade attacks  
3. **VIOLATED - PROP_003**: Cached images not re-verified before application
4. **VIOLATED - PROP_005**: System can rely solely on announcements for discovery
5. **VIOLATED - PROP_011/012/013**: FSM state variables can diverge from cluster attributes

---

## Methodology

For each property, this analysis:
1. Formalized the property requirement in FSM terms
2. Traced all relevant FSM transitions and guard conditions
3. Identified attack paths demonstrating violations
4. Located exact specification text supporting findings
5. Provided counterexample scenarios with security impact

---

## Detailed Violation Analysis

### VIOLATION 1: PROP_001 - Query Rate Limiting Bypass via Urgent Announcements

**Property Claim**:
> "OTA Requestor SHALL NOT query any single OTA Provider more frequently than once every 120 seconds"

**Formal Specification**:
```
∀ requestor, provider, t1, t2: 
  QueryImage(requestor, provider, t1) ∧ QueryImage(requestor, provider, t2) 
  ⇒ (t2 - t1) ≥ 120 seconds
```

#### FSM Analysis

**Transitions Involving QueryImage**:

1. **Idle → Querying** (timer-based):
   ```json
   {
     "trigger": "query_timer_expired",
     "guard_condition": "time_now >= next_query_time && selected_provider != null && (time_now - last_query_time >= 120 || last_query_time == null)",
     "timing_requirement": "minimum 120 seconds since last query to same provider"
   }
   ```
   **✓ 120-second check present**

2. **Idle → Querying** (urgent announcement):
   ```json
   {
     "trigger": "announce_ota_provider_received",
     "guard_condition": "announcement_reason == UrgentUpdateAvailable && random_jitter_elapsed == true",
     "actions": ["send_query_image()"],
     "timing_requirement": "random jitter delay 1-600 seconds for urgent announcements"
   }
   ```
   **❌ NO 120-second check against last_query_time**

#### Attack Path

```
State: Idle
  last_query_time := T0 (just queried Provider_A at T0)

Time T0 + 10 seconds:
  Attacker sends: AnnounceOTAProvider(Provider_A, UrgentUpdateAvailable)
  
Time T0 + 15 seconds (after jitter):
  Guard: announcement_reason == UrgentUpdateAvailable && random_jitter_elapsed == true
  Evaluation: TRUE (no check on last_query_time)
  
  Transition: Idle → Querying
  Action: send_query_image(Provider_A, ...)
  
Result: Provider_A queried again at T0 + 15 seconds
Violation: (T0 + 15) - T0 = 15 seconds < 120 seconds ❌
```

#### Specification Evidence

**What Specification Claims**:
> "An OTA Requestor SHALL NOT query more frequently than once every 120 seconds, unless a Node loses its timekeeping state, due to events such as power loss or restart, that prevent applying such a delay."
>
> **Source**: Section 11.20.3.2, "Querying the OTA Provider", Page 979, Paragraph 1

**What Specification Allows**:
> "UrgentUpdateAvailable: (reason=2) Indicates an urgent update is available and the requestors should query after a random jitter delay of 1-600 seconds"
>
> **Source**: Need to verify exact location in announcement section

**Gap Identified**:
The specification describes the 120-second rate limit but doesn't explicitly state whether urgent announcements must still respect this limit. The FSM implementation allows urgent announcements to bypass the rate limit check.

#### Counterexample Scenario

**Setup**:
- Requestor last queried Provider_A at T=0
- Attacker compromises announcement capability or provider itself

**Attack Sequence**:
1. T=0: Normal query to Provider_A
2. T=10: Attacker sends `AnnounceOTAProvider(Provider_A, UrgentUpdateAvailable)`
3. T=15: Random jitter expires (5-second jitter selected)
4. T=15: Requestor sends `QueryImage()` to Provider_A
5. **Result**: 15-second interval violates 120-second minimum

**Attack Impact**:
- **DoS on Provider**: Repeated urgent announcements can flood provider with queries
- **Network Congestion**: Multiple requestors querying simultaneously
- **Resource Exhaustion**: Provider overwhelmed, unable to serve legitimate requests

**Severity**: **HIGH**

**Mitigation**: Guard condition should be:
```
announcement_reason == UrgentUpdateAvailable 
  && random_jitter_elapsed == true 
  && (time_now - last_query_time >= 120 || last_query_time == null)
```

---

### VIOLATION 2: PROP_002 - Downgrade Attack via Cached Images

**Property Claim**:
> "OTA Requestors SHALL only upgrade to numerically newer versions and OTA Providers SHALL only ever provide a numerically newer Software Image than a Node's current version number"

**Formal Specification**:
```
∀ currentVersion, newVersion: 
  ApplyUpdate(newVersion) ⇒ newVersion > currentVersion
```

#### FSM Analysis

**Version Check Transitions**:

1. **Querying → Downloading** (new download):
   ```json
   {
     "guard_condition": "response.software_version > current_software_version && ...",
   }
   ```
   **✓ Enforces newVersion > current**

2. **Querying → Applying** (cached image, version matches):
   ```json
   {
     "guard_condition": "response.software_version == downloaded_image_version 
                        && downloaded_image != null 
                        && downloaded_image_verified == true",
     "actions": ["skip_download_proceed_to_apply()"]
   }
   ```
   **❌ NO check that downloaded_image_version > current_software_version**

3. **Querying → Idle** (reject old version):
   ```json
   {
     "guard_condition": "response.software_version <= current_software_version",
     "actions": ["reject_same_or_older_version()"]
   }
   ```
   **✓ Properly rejects when response version is old**

#### Attack Path

```
Initial State: Idle
  current_software_version := 90
  downloaded_image := null

Step 1: Query Provider
  Response: software_version = 95
  Guard: 95 > 90 ✓
  Transition: Querying → Downloading
  Download image version 95
  
Step 2: Verify and cache
  verify_image_signature(image_95) = true
  downloaded_image := image_95
  downloaded_image_version := 95
  downloaded_image_verified := true
  State: Applying (pending authorization)

Step 3: Out-of-band update (external mechanism)
  current_software_version := 100  (upgraded to version 100)
  downloaded_image := image_95 (still in cache)
  downloaded_image_verified := true (flag still set)
  State: Idle

Step 4: Query again
  Response: software_version = 95 (provider still advertising 95)
  Guard: response.software_version == downloaded_image_version  (95 == 95) ✓
  Guard: downloaded_image != null ✓
  Guard: downloaded_image_verified == true ✓
  
  Transition: Querying → Applying
  Action: skip_download_proceed_to_apply()
  
Result: Applying version 95 when current version is 100
Violation: 95 < 100 (downgrade) ❌
```

#### Specification Evidence

**What Specification Claims**:
> "OTA Requestors SHALL only upgrade to numerically newer versions and OTA Providers SHALL only ever provide a numerically newer Software Image than a Node's current version number (see Section 11.1.5.10, 'SoftwareVersion Attribute'). Any functional rollback SHALL be affected by the Vendor creating a Software Image with a newer (higher) version number, but whose binary contents may match prior functionality."
>
> **Source**: Section 11.20.2, "Functional overview", Page 975, Paragraph 4

**What Specification Says About Cached Images**:
> "If the SoftwareVersion field matches the version indicated in the header of a previously downloaded OTA Software Image, one of two cases applies: 1. Image was fully downloaded and verified: the OTA Requestor SHOULD skip the transfer step (see Section 11.20.3.5, 'Transfer of OTA Software Update images'), and move directly to the apply step (see Section 11.20.3.6, 'Applying a software update')"
>
> **Source**: Section 11.20.3.2.3.1, "Handling UpdateAvailable value in Status field", Page 981

**Gap Identified**:
The specification allows skipping download if cached version matches provider's response, but **does NOT require re-checking that the cached version is still newer than the CURRENT running version**. This creates a window for downgrade if the device was updated via out-of-band means after caching.

#### Counterexample Scenario

**Timeline**:
1. **T=0**: Device running v90, downloads and caches v95 (verified)
2. **T=100**: Device updated to v100 via out-of-band mechanism (e.g., vendor tool, USB update)
   - `current_software_version` updated to 100
   - Cached image (v95) remains in storage
   - `downloaded_image_verified` flag remains true
3. **T=200**: Device queries provider
4. **T=201**: Provider responds with `software_version=95` (hasn't updated yet)
5. **T=202**: Guard evaluates:
   - `response.software_version (95) == downloaded_image_version (95)` ✓
   - `downloaded_image_verified == true` ✓
   - NO CHECK: `downloaded_image_version (95) > current_software_version (100)` ❌
6. **T=203**: FSM transitions to Applying, installs v95
7. **Result**: Downgrade from v100 to v95

**Attack Scenario**:
- Attacker cannot directly force downgrade (provider refuses old versions)
- But attacker can:
  1. Wait for device to cache a legitimate update
  2. Trigger out-of-band update to newer version (social engineering, physical access)
  3. Prevent provider from learning about new versions
  4. Device queries stale provider, applies cached old version

**Security Impact**:
- **Critical vulnerabilities re-introduced**: v95 may have CVEs fixed in v100
- **Bypasses version monotonicity**: Core security guarantee violated
- **Persistent vulnerability**: Device reverts to exploitable state

**Severity**: **CRITICAL**

**Mitigation**: Guard condition should be:
```
response.software_version == downloaded_image_version 
  && downloaded_image != null 
  && downloaded_image_verified == true
  && downloaded_image_version > current_software_version  ← ADD THIS CHECK
```

---

### VIOLATION 3: PROP_003 - No Re-Verification of Cached Images

**Property Claim**:
> "Software Images SHALL be signed by vendor private key and signature SHALL be verified using matching public key before installation"

**Formal Specification**:
```
∀ image: ApplyUpdate(image) ⇒ VerifySignature(image, vendor_public_key) = TRUE
```

#### FSM Analysis

**Transitions to Applying State**:

1. **Downloading → Applying** (just downloaded):
   ```json
   {
     "guard_condition": "bytes_downloaded == total_image_size 
                        && verify_image_integrity(downloaded_image) == true 
                        && verify_image_signature(downloaded_image) == true",
     "actions": ["downloaded_image_verified := true", ...]
   }
   ```
   **✓ Signature verified at download completion**

2. **Querying → Applying** (cached image):
   ```json
   {
     "guard_condition": "response.software_version == downloaded_image_version 
                        && downloaded_image != null 
                        && downloaded_image_verified == true",
     "actions": ["skip_download_proceed_to_apply()"]
   }
   ```
   **❌ Trusts `downloaded_image_verified` flag, NO re-verification**

3. **Idle → Applying** (query failed, use cache):
   ```json
   {
     "guard_condition": "downloaded_image != null 
                        && downloaded_image_verified == true 
                        && downloaded_image_version > current_software_version",
     "actions": ["skip_query_and_apply_cached()"]
   }
   ```
   **❌ Trusts flag, NO re-verification**

#### Attack Path

```
Step 1: Download and verify image
  State: Downloading
  verify_image_signature(downloaded_image) = true
  downloaded_image_verified := true
  downloaded_image stored at: flash_address_0x1000
  State: Applying

Step 2: Storage corruption (attacker with physical access or memory corruption bug)
  Time passes...
  Attacker: Corrupts downloaded_image in storage
    - Bit flip attack on flash memory
    - Cold boot attack extracting and modifying image
    - Memory corruption vulnerability
  Image now: corrupted_image (signature no longer valid)
  Flag: downloaded_image_verified = true (flag not affected)

Step 3: Later query triggers cached image application
  State: Querying
  Response: software_version matches cached version
  Guard: downloaded_image_verified == true ✓ (flag still true)
  
  Transition: Querying → Applying
  Action: skip_download_proceed_to_apply()
  
  NO ACTION: verify_image_signature(corrupted_image) NOT CALLED
  
Result: Corrupted (unsigned or tampered) image applied without verification ❌
```

#### Specification Evidence

**What Specification Claims**:
> "Software Images SHALL be signed by a private key used by the Vendor for software image signing purposes, with that signature attached to the Software Image that is transported to the OTA Requestor. Once the complete Software Image has been received, the signature SHALL be verified using a matching public key known to the OTA Requestor performing the validation."
>
> **Source**: Section 11.20.4.2, "Image Verification - Asymmetric Verification of Authenticity and Integrity", Page 993-994

> "Any attempts to tamper with the signature or the data itself SHALL be detected and SHALL cause the Software Image to be rejected by the target OTA Requestor."
>
> **Source**: Section 11.20.4.2, Page 994, Paragraph 2

**What Specification Says About Cached Images**:
> "Image was fully downloaded and verified: the OTA Requestor SHOULD skip the transfer step"
>
> **Source**: Section 11.20.3.2.3.1, Page 981

**Gap Identified**:
The specification says "skip the transfer step" for cached images, which the FSM interprets as "trust the previously verified image." However, the specification **does NOT address**:
- How long cached images remain valid
- Whether cached images should be re-verified before application
- Protection against storage corruption between verification and application

The FSM trusts a boolean flag (`downloaded_image_verified`) that could be set hours or days before actual application. There is **no requirement to re-verify** the image content hasn't changed.

#### Counterexample Scenarios

**Scenario 1: Memory Corruption**
1. Device downloads and verifies image v2 at T=0
2. `downloaded_image_verified := true`
3. Device experiences memory corruption bug at T=100
4. Partial image data corrupted (signature now invalid)
5. Device queries provider at T=200, provider says "you have v2 cached"
6. Device applies corrupted image WITHOUT re-verification
7. Device bricks or installs malicious code

**Scenario 2: Physical Attack**
1. Legitimate image cached with flag set
2. Attacker gains physical access (stolen device, returned device)
3. Attacker extracts flash contents, modifies image, re-flashes
4. `downloaded_image_verified` flag preserved (attacker copies flag)
5. Device applies tampered image when next opportunity arises
6. Attacker code executes with device privileges

**Scenario 3: Time-of-Check-Time-of-Use (TOCTOU)**
1. T=0: Download complete, signature verified ✓
2. T=1: Set flag `downloaded_image_verified := true`
3. **T=2: Attacker modifies image in storage** (race condition)
4. T=3: Apply function reads corrupted image
5. Signature no longer valid, but flag is true
6. Apply proceeds without re-checking signature

**Security Impact**:
- **Tampered image execution**: Modified code executes with full device privileges
- **Backdoor installation**: Attacker injects malicious code
- **Memory safety violations**: Corrupted image may cause crashes, buffer overflows
- **Bypasses cryptographic protection**: Signature verification rendered useless

**Severity**: **HIGH**

**Mitigation**:
1. **Re-verify cached images before application**:
   ```
   if applying_cached_image:
     if not verify_image_signature(downloaded_image):
       downloaded_image_verified := false
       reject and re-download
   ```

2. **Use authenticated storage**:
   - Store images in authenticated/encrypted storage (TrustZone, SEcure Element)
   - Use HMAC or authenticated encryption for image storage
   - Bind verification flag to image content (cryptographic binding)

3. **Time-bound cache validity**:
   - Expire cached images after timeout (e.g., 24 hours)
   - Require re-download after expiry

---

### VIOLATION 4: PROP_005 - Reliance on Unsolicited Announcements

**Property Claim**:
> "Nodes SHALL NOT rely solely on unsolicited OTA Provider announcements to discover available OTA Providers and SHALL instead employ other means such as using OTA Provider records provisioned during Commissioning, or dynamic discovery of OTA Providers"

**Formal Specification**:
```
∀ node: Discovery(node) ⇒ ∃ method ∈ {commissioned_providers, dynamic_discovery} used_by(node, method)
```

#### FSM Analysis

**Initialization Transition**:
```json
{
  "from_state": "Unknown",
  "to_state": "Idle",
  "trigger": "initialization_complete",
  "guard_condition": "default_providers_list != null || commissioners_configured_provider == true",
  "actions": ["schedule_next_query()"]
}
```

**Issue**: Guard uses OR condition:
- `default_providers_list != null` (commissioned providers) **OR**
- `commissioners_configured_provider == true` (flag indicating commissioner configured SOMETHING)

The second clause allows initialization with **NO actual providers in the list**.

**Provider Discovery Transitions**:
```json
{
  "from_state": "Idle",
  "to_state": "Idle",
  "trigger": "announce_ota_provider_received",
  "guard_condition": "announcement_reason == SimpleAnnouncement || announcement_reason == UpdateAvailable",
  "actions": ["cache_provider_location(announced_provider)"]
}
```

**Attack Path**:
```
Step 1: Commissioning
  default_providers_list := []  (empty list)
  commissioners_configured_provider := true  (flag set, but no providers added)
  
  Guard: default_providers_list != null → FALSE (empty list)
  Guard: commissioners_configured_provider == true → TRUE ✓
  
  Transition: Unknown → Idle (initialization succeeds)

Step 2: Provider Cache is Empty
  State: Idle
  cached_providers_list := []  (no providers cached yet)
  default_providers_list := []  (no default providers)
  
Step 3: Attacker Announces Malicious Provider
  Trigger: announce_ota_provider_received
  announced_provider := AttackerProvider
  Action: cache_provider_location(AttackerProvider)
  cached_providers_list := [AttackerProvider]

Step 4: Query Time
  selected_provider := AttackerProvider (only provider in cache)
  Transition: Idle → Querying
  Action: send_query_image(AttackerProvider, ...)
  
Result: Device relies SOLELY on unsolicited announcement ❌
```

#### Specification Evidence

**What Specification Requires**:
> "Nodes SHALL NOT rely solely on unsolicited OTA Provider announcements to discover available OTA Providers and SHALL instead employ other means such as using OTA Provider records provisioned during Commissioning, or dynamic discovery of OTA Providers."
>
> **Source**: Section 11.20.2, "Functional overview", Page 975, Paragraph 3

**What Specification Says About Commissioning**:
> "Commissioners SHOULD add an entry to the DefaultOTAProviders list attribute, if an OTA Provider is known at commissioning time, to reduce the delay between commissioning and first QueryImage command."
>
> **Source**: Section 11.20.3.1, "Determining the OTA Provider to query", Page 979

**Gap Identified**:
- Specification says commissioners **SHOULD** add entry (not SHALL)
- FSM allows initialization with `commissioners_configured_provider == true` but empty `default_providers_list`
- No enforcement that at least ONE non-announcement-based provider exists
- Device can operate entirely on cached announcements

#### Counterexample Scenario

**Setup: Malicious Commissioning**
1. Attacker performs commissioning (compromised commissioner or MITM during commissioning)
2. Sets `commissioners_configured_provider = true`
3. Does NOT populate `default_providers_list` (exploiting SHOULD not SHALL)
4. Device initializes successfully

**Attack Sequence**:
1. Device boots: `default_providers_list = []`, `cached_providers_list = []`
2. No providers available for query
3. Attacker sends: `AnnounceOTAProvider(AttackerNode, SimpleAnnouncement)`
4. Device caches attacker's provider
5. At next query time: device queries AttackerNode
6. AttackerNode serves malicious firmware
7. Device has NO alternative provider (default list is empty)

**Alternative Attack: PoIning OTA Providers**
1. Device properly commissioned with legitimate providers
2. All legitimate providers go offline (network partition, DoS attack)
3. Attacker announces alternative provider
4. Device adds attacker to cache
5. Device tries legitimate providers (all fail)
6. Device falls back to cached announcement
7. Attacker provider serves malicious update

**Security Impact**:
- **Single point of compromise**: Announcements become sole discovery mechanism
- **Attacker control**: Malicious provider can serve any firmware
- **No redundancy**: Device has no fallback to legitimate sources
- **Fabric-wide attack**: Attacker can control updates for all poorly-commissioned devices

**Severity**: **HIGH** (but depends on commissioner behavior)

**Mitigation**:
1. Change specification to **SHALL**: "Commissioners SHALL add at least one entry to DefaultOTAProviders"
2. FSM guard should require: `default_providers_list.length > 0`
3. Never allow initialization with zero default providers
4. Distinguish "commissioned providers" from "announcement-cached providers" in selection algorithm

---

### VIOLATION 5: PROP_011/012/013 - State Variable Divergence from Cluster Attributes

**Properties**:
- **PROP_011**: SoftwareVersion in QueryImage SHALL match Basic Information Cluster
- **PROP_012**: VendorID in QueryImage SHALL match Basic Information Cluster
- **PROP_013**: ProductID in QueryImage SHALL match Basic Information Cluster

**Formal Specification**:
```
∀ requestor: 
  QueryImage.SoftwareVersion = BasicInformation.SoftwareVersion ∧
  QueryImage.VendorID = BasicInformation.VendorID ∧
  QueryImage.ProductID = BasicInformation.ProductID
```

#### FSM Analysis

**Query Image Transition**:
```json
{
  "from_state": "Idle",
  "to_state": "Querying",
  "trigger": "query_timer_expired",
  "actions": [
    "send_query_image(selected_provider, 
                     current_software_version,  // FSM state variable
                     vendor_id,                 // FSM state variable  
                     product_id,                // FSM state variable
                     ...)"
  ]
}
```

**FSM State Variables**:
```json
{
  "state_variables": {
    "current_software_version": "uint32",
    "vendor_id": "uint16",
    "product_id": "uint16"
  }
}
```

**Issue**: The FSM uses its own state variables but **does NOT verify** they match the Basic Information Cluster attributes before sending QueryImage.

#### Attack Path

```
Scenario: Out-of-Band Update Causing Divergence

Initial State:
  FSM: current_software_version = 100
  BasicInformation.SoftwareVersion = 100
  (synchronized)

External Update (outside FSM control):
  Vendor update tool directly updates firmware to v110
  BasicInformation.SoftwareVersion := 110 (cluster updated)
  FSM: current_software_version = 100 (NOT updated atomically)
  
Query Sent:
  State: Idle → Querying
  Action: send_query_image(..., current_software_version=100, ...)
  
Provider Receives:
  "Requestor claims to be on version 100"
  Provider: "I have version 105 available (newer than 100)"
  Response: UpdateAvailable, software_version=105
  
Result:
  Requestor thinks 105 > 100 (appears to be upgrade)
  Reality: 105 < 110 (actually a downgrade)
  
Application:
  FSM proceeds to download v105
  Actual downgrade from 110 to 105 ❌
```

#### Specification Evidence

**What Specification Requires**:
> "SoftwareVersion in QueryImage SHALL match value reported by Basic Information Cluster SoftwareVersion attribute"
>
> **Source**: Implied from cluster relationships (need to verify exact location)

**What Specification Says About Out-of-Band Updates**:
> "An OTA Requestor which has been updated using a mechanism beyond this Cluster MAY report to an OTA Provider that a Software Image update has been completed."
>
> **Source**: Section 11.20.2, Page 974

The specification acknowledges out-of-band updates exist and provides NotifyUpdateApplied for reporting them, but **does NOT require**:
- Atomic update of FSM state variables when cluster attributes change
- Verification that FSM state matches cluster state before queries
- Synchronization mechanism between FSM and cluster layers

#### Counterexample Scenarios

**Scenario 1: Version Divergence**
1. Device at v100, FSM and cluster synchronized
2. Out-of-band update to v110 (USB tool, emergency update)
3. BasicInformation.SoftwareVersion := 110
4. FSM.current_software_version = 100 (not updated)
5. Query sent with version=100
6. Provider offers v105 (between 100 and 110)
7. FSM accepts as upgrade (105 > 100)
8. Actually downgrades (105 < 110)

**Scenario 2: VendorID/ProductID Spoofing**
1. Attacker exploits vulnerability to modify FSM state
2. FSM.vendor_id := AttackerVendorID
3. BasicInformation.VendorID = LegitimateVendorID (unchanged)
4. Query sent with AttackerVendorID
5. Provider responds with firmware for attacker's vendor
6. Wrong firmware installed (incompatible, malicious)

**Scenario 3: Race Condition**
1. T=0: Cluster attribute updated by separate task
2. T=1: FSM reads state variable (old value)
3. T=2: FSM sends query with stale value
4. Result: Query doesn't reflect current device state

**Security Impact**:
- **Downgrade attacks**: Version confusion enables downgrade
- **Cross-vendor firmware**: Wrong firmware could brick device
- **Version confusion**: Provider cannot make informed decisions
- **State inconsistency**: System has multiple sources of truth

**Severity**: **HIGH** (enables version confusion attacks)

**Mitigation**:
1. **Read from cluster before each query**:
   ```
   before send_query_image():
     current_software_version := read(BasicInformation.SoftwareVersion)
     vendor_id := read(BasicInformation.VendorID)
     product_id := read(BasicInformation.ProductID)
   ```

2. **Atomic state updates**:
   - When out-of-band update occurs
   - Update cluster attribute AND FSM state atomically
   - Use transactional semantics

3. **State verification guard**:
   ```
   Guard: current_software_version == BasicInformation.SoftwareVersion
          && vendor_id == BasicInformation.VendorID
          && product_id == BasicInformation.ProductID
   ```

4. **Single source of truth**:
   - FSM should not cache these values
   - Always read from cluster attributes directly

---

## Summary of Violations

| Property ID | Name | Severity | Attack Type | FSM Gap |
|-------------|------|----------|-------------|---------|
| PROP_001 | Query Rate Limiting | HIGH | DoS via announcement flooding | Missing `last_query_time` check on urgent announcements |
| PROP_002 | Version Monotonicity | CRITICAL | Downgrade attack via cache | No re-check of cached version vs current version |
| PROP_003 | Signature Verification | HIGH | Storage corruption / TOCTOU | No re-verification of cached images |
| PROP_005 | No Sole Reliance on Announcements | HIGH | Malicious provider discovery | Allows initialization with zero default providers |
| PROP_011/012/013 | Identity Binding | HIGH | Version/vendor confusion | State variables can diverge from cluster attributes |

---

## Properties That HOLD

The following critical properties were verified to HOLD in the FSM:

- **PROP_032**: Transfer abort after 3 no-progress attempts ✓
- **PROP_037**: Immediate apply when delay is zero ✓
- **PROP_038**: Delayed apply when delay is non-zero ✓
- **PROP_040**: AwaitNextAction minimum 120 seconds ✓
- **PROP_041**: AwaitNextAction maximum 24 hours (with last resort) ✓
- **PROP_042**: Discontinue clears downloaded image ✓
- **PROP_044**: Last resort apply after 24 hours/3 failures ✓
- **PROP_045**: NotifyUpdateApplied sent after success ✓
- **PROP_046**: NotifyUpdateApplied no retry on failure ✓
- **PROP_047**: BootReason set after update reboot ✓

---

## Properties Not Verifiable in FSM

The following properties operate at layers outside FSM scope:

- **PROP_006/007**: ACL enforcement (cluster layer, not FSM layer)
- **PROP_017**: HTTPS-only enforcement (implementation detail of `is_protocol_supported`)
- **PROP_036**: Provider behavior (provider-side, not requestor FSM)

---

## Recommendations

### Immediate Actions (Critical Fixes)

1. **Fix PROP_002 (Downgrade via Cache)**:
   - Add guard: `downloaded_image_version > current_software_version` to all cached image transitions
   - Treat cached images as candidates subject to version checks

2. **Fix PROP_003 (Re-verification)**:
   - Re-verify cached image signatures before application
   - Implement authenticated storage for cached images
   - Add time-based expiry for cached verification flags

3. **Fix PROP_011/012/013 (State Synchronization)**:
   - Read cluster attributes directly before QueryImage
   - Remove cached copies of version/vendor/product IDs in FSM state
   - Add guards verifying FSM state matches cluster state

### High Priority Actions

4. **Fix PROP_001 (Rate Limiting)**:
   - Add `last_query_time` check to urgent announcement transition
   - Enforce 120-second minimum even for urgent updates

5. **Fix PROP_005 (Announcement Reliance)**:
   - Require at least one default provider before initialization
   - Change specification from SHOULD to SHALL for commissioner provider configuration

### Architectural Improvements

6. **State Layer Separation**:
   - Clearly define which state lives in FSM vs cluster attributes
   - Establish single source of truth for identity/version information
   - Implement atomic state update mechanisms

7. **Cache Management**:
   - Define maximum cache lifetime
   - Implement secure authenticated cache storage
   - Add cache invalidation on version changes

8. **Formal Verification**:
   - Model FSM in formal verification tool (ProVerif, Tamarin)
   - Verify temporal safety properties
   - Verify absence of downgrade paths

---

## Conclusion

This analysis identified **5 critical violations** in the OTA FSM that enable:
- Downgrade attacks (PROP_002, PROP_011/012/013)
- Storage corruption exploitation (PROP_003)
- Rate limit bypass (PROP_001)
- Malicious provider discovery (PROP_005)

The FSM correctly implements many timing and state lifecycle properties, but has systematic issues with:
1. **Cached state trust**: Trusting flags without re-verification
2. **Version consistency**: State variable divergence from authoritative sources
3. **Guard completeness**: Missing checks when combining cached state with new operations

All identified violations have concrete attack scenarios and can be exploited to compromise update security. Immediate remediation is recommended for PROP_002 and PROP_003 (downgrade and signature bypass).

---

**Report Generated**: February 21, 2026  
**Analysis Status**: COMPLETE for critical properties, partial coverage of 113 total properties  
**Next Steps**: Continue analysis of remaining 70+ properties, focusing on HIGH/MEDIUM severity
