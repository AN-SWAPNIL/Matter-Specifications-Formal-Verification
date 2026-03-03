# OTA Security Property Violation Analysis - Working Document

## Analysis Metadata
- **Specification**: Matter Core Specification v1.5, Section 11.20 (OTA Software Update)
- **FSM Model**: ota_fsm_model.json (12 states, 71 transitions, 41 functions)
- **Total Properties**: 113
- **Analysis Date**: 2026-02-21
- **Status**: IN PROGRESS

---

## Methodology
For each property:
1. Formalize the property in FSM terms
2. Trace all relevant FSM transitions
3. Identify attack paths that violate the property
4. Find specification evidence (claims and gaps)
5. Document verdict with counterexample if violated

---

## CRITICAL Properties Analysis

### PROP_001: Query_Rate_Limiting_120_Seconds

**Claim**: OTA Requestor SHALL NOT query any single OTA Provider more frequently than once every 120 seconds

**FSM Analysis**:

Transitions involving QueryImage:
1. Idle → Querying (query_timer_expired)
   - Guard: `time_now >= next_query_time && selected_provider != null && (time_now - last_query_time >= 120 || last_query_time == null)`
   - **120-second check present** ✓

2. Idle → Querying (announce_ota_provider_received) 
   - Guard: `announcement_reason == UrgentUpdateAvailable && random_jitter_elapsed == true`
   - **NO 120-second check** ❌

3. DelayedOnQuery → Querying (delay_timer_expired)
   - Guard: `time_now >= (delay_start_time + delay_duration) && retry_same_provider == true`
   - Delay enforced via timer, but initial delay is `max(120, response.delayed_action_time)`
   - **120-second minimum enforced** ✓

**Attack Path Found**:
```
State: Idle
Trigger: announce_ota_provider_received (UrgentUpdateAvailable)
Guard: announcement_reason == UrgentUpdateAvailable && random_jitter_elapsed == true
Action: send_query_image()
Result: Query sent without checking last_query_time for this provider
```

**Violation**: If an attacker sends multiple UrgentUpdateAvailable announcements with 1-600 second random jitter, the requestor will query the same provider multiple times within 120 seconds.

**Specification Evidence**:

*Claim (what should hold)*:
> "OTA Requestor SHALL NOT query any single OTA Provider more frequently than once every 120 seconds"
> Source: Section 11.20.3, need to verify exact location

*Gap (what's missing)*:
The specification allows UrgentUpdateAvailable announcements to bypass the 120-second rate limit. The FSM transition for urgent announcements does NOT check `last_query_time`.

**Counterexample**:
1. Time T=0: Requestor queries Provider_A normally
2. Time T=10: Attacker sends AnnounceOTAProvider (UrgentUpdateAvailable) for Provider_A
3. Time T=11-610: Random jitter expires
4. Time T=15: Requestor queries Provider_A again (only 15 seconds since last query)
5. Result: Violated 120-second rate limit

**Verdict**: **VIOLATED**

**Severity**: HIGH (not CRITICAL because urgent announcements are rate-limited themselves to prevent abuse, but still allows violation)

---

### PROP_002: Version_Monotonicity_Upgrade_Only

**Claim**: OTA Requestors SHALL only upgrade to numerically newer versions

**FSM Analysis**:

Transitions checking version:

1. Querying → Downloading
   - Guard: `response.software_version > current_software_version`
   - **Version check present** ✓

2. Querying → Applying (cached image)
   - Guard: `response.software_version == downloaded_image_version && downloaded_image != null && downloaded_image_verified == true`
   - **No check that cached version > current_software_version** ❌

3. Querying → Idle (reject old version)
   - Guard: `response.software_version <= current_software_version`
   - Action: `reject_same_or_older_version()`
   - **Properly rejects old versions** ✓

4. Idle → Applying (query failed, use cache)
   - Guard: `downloaded_image != null && downloaded_image_verified == true && downloaded_image_version > current_software_version`
   - **Version check present** ✓

5. Idle → Idle (out_of_band_update_applied)
   - Guard: `software_updated_externally == true && new_version > previous_version`
   - **Checks new > previous, but previous != current** ⚠️

**Attack Path Found**:
```
State: Idle (current_software_version = 100)
Prior: Downloaded and verified image version 95 (older than current)
Trigger: query_timer_expired
Provider Response: software_version = 95 (matches cached)
Guard: response.software_version == downloaded_image_version && downloaded_image_verified == true
Transition: Querying → Applying
Result: Applying version 95 which is OLDER than current version 100
```

**Violation**: The FSM allows applying a cached image if its version matches the provider's response, WITHOUT re-checking that the cached version is newer than current_software_version. This can happen if:
- Image was downloaded when software_version was 90
- Device was updated to version 100 via out-of-band mechanism  
- Provider still reports version 95 as available
- Requestor applies the cached version 95, downgrading from 100 to 95

**Specification Evidence**:

*Claim*:
> "OTA Requestors SHALL only upgrade to numerically newer versions and OTA Providers SHALL only ever provide a numerically newer Software Image than a Node's current version number"
> Source: Section 11.20.2, Paragraph 4

*Gap*:
The specification doesn't explicitly address what happens when:
1. An image is cached at an earlier time
2. The device software version increases (via out-of-band update)
3. The cached image is now older than current version

**Counterexample**:
1. T=0: Requestor has version 90, downloads and caches version 95 (verified)
2. T=100: Out-of-band update installs version 100
3. T=200: Requestor queries provider
4. T=201: Provider responds with version 95 (matching cached image)
5. T=202: FSM transitions Querying → Applying (cached image)
6. T=203: Downgrade from 100 to 95 occurs

**Verdict**: **VIOLATED**

**Severity**: CRITICAL (enables downgrade attacks)

---

### PROP_003: Mandatory_Image_Signature_Verification

**Claim**: Software Images SHALL be signed and signature SHALL be verified before installation

**FSM Analysis**:

Transitions to Applying state:

1. Downloading → Applying
   - Guard: `verify_image_integrity() == true && verify_image_signature() == true`
   - **Signature verification required** ✓

2. Querying → Applying (cached image)
   - Guard: `downloaded_image_verified == true`
   - Relies on `downloaded_image_verified` flag set during download
   - **Assumes prior verification** ✓

3. Idle → Applying (query failed, use cache)  
   - Guard: `downloaded_image_verified == true`
   - **Assumes prior verification** ✓

4. Querying → Idle → Applying (error path with cache)
   - Guard: `downloaded_image_verified == true`
   - **Assumes prior verification** ✓

**Potential Issue**: All paths to Applying require signature verification EXCEPT:
- What if `downloaded_image_verified` flag is corrupted?
- What if image content changes after verification (if not stored securely)?
- **No re-verification of cached images**

**Attack Path Analysis**:
```
State: Downloading
Action: verify_image_signature(downloaded_image) == true
Action: downloaded_image_verified := true
State: Applying

Later:
State: Idle (image still in cache)
Attacker: Corrupts downloaded_image in storage
Later query:
Guard: downloaded_image_verified == true (flag still true)
Transition: Querying → Applying (corrupted image applied without re-verification)
```

**Specification Evidence**:

*Claim*:
> "Software Images SHALL be signed by vendor private key and signature SHALL be verified using matching public key before installation"
> Source: Implied from security considerations

*Gap*:
Specification doesn't require:
- Re-verification of cached images before application
- Secure storage of images post-verification
- Secure storage of verification flags

**Verdict**: **PARTIALLY VIOLATED**

The FSM properly requires signature verification on download, but:
1. Cached images are not re-verified before application
2. No protection against storage corruption between verification and application
3. Trusted flag (`downloaded_image_verified`) is assumed to remain valid

**Severity**: HIGH (storage corruption could enable malicious image application)

---

### PROP_005: No_Reliance_On_Unsolicited_Announcements

**Claim**: Nodes SHALL NOT rely solely on unsolicited announcements

**FSM Analysis**:

Discovery mechanisms:
1. Unknown → Idle
   - Guard: `default_providers_list != null || commissioners_configured_provider == true`
   - **Requires configured providers before starting** ✓

2. Idle → Querying (timer-based)
   - Guard: `selected_provider != null`
   - Uses `default_providers_list` or `cached_providers_list`
   - **Can use commissioned providers** ✓

3. Idle → Querying (announcement-based)
   - Trigger: `announce_ota_provider_received` (UrgentUpdateAvailable)
   - Action: `selected_provider := announced_provider`
   - **Can query based solely on announcement** ❌

**Attack Path Found**:
```
State: Unknown
Transition: Unknown → Idle
Guard: commissioners_configured_provider == true (but default_providers_list == null)
State: Idle (no default providers, only cached providers from announcements)

Loop:
  Trigger: announce_ota_provider_received
  Action: cache_provider_location(announced_provider)
  Next query: Uses only cached (announced) providers
  
Result: Requestor relies SOLELY on announcements for provider discovery
```

**Violation**: While initialization requires `default_providers_list != null || commissioners_configured_provider == true`, the second part of the OR allows initialization with NO default providers. In this case, the requestor can only discover providers through announcements.

**Specification Evidence**:

*Claim*:
> "Nodes SHALL NOT rely solely on unsolicited OTA Provider announcements to discover available OTA Providers and SHALL instead employ other means such as using OTA Provider records provisioned during Commissioning, or dynamic discovery of OTA Providers."
> Source: Section 11.20.2, Page 975

*Gap*:
The FSM allows initialization with `commissioners_configured_provider == true` but `default_providers_list == null`. This permits a node to operate without any provisioned providers, relying entirely on announcements.

**Counterexample**:
1. Device commissioned with `commissioners_configured_provider = true` but NO providers in `default_providers_list`
2. Device initializes: Unknown → Idle  
3. Attacker announces malicious provider
4. Device caches announced provider
5. Device queries ONLY announced providers (no other discovery mechanism active)
6. Attacker controls all update sources

**Verdict**: **VIOLATED**

**Severity**: HIGH (but implementation-dependent - if commissioners properly configure default providers, violation doesn't occur)

---

### PROP_006: ACL_Required_For_AnnounceOTAProvider

**Claim**: ACL entries SHOULD be installed to enable handling of AnnounceOTAProvider commands

**FSM Analysis**:

The FSM models the announcement handling:
```
Idle → Idle (announce_ota_provider_received)
Idle → Querying (announce_ota_provider_received with UrgentUpdateAvailable)
```

**Issue**: The FSM does NOT model ACL checking. ACL enforcement is assumed to happen at the cluster/command layer, not in the FSM.

**Analysis**:
- FSM assumes announcements are already ACL-filtered
- No guard condition checking ACL
- No transition showing announcement rejection due to missing ACL

**Verdict**: **NOT VERIFIABLE IN FSM**

The FSM abstracts away ACL enforcement. This property must be verified at the implementation level, not FSM level.

**Severity**: N/A (architectural assumption)

---

### PROP_007: ACL_Required_For_QueryImage

**Claim**: ACL entries SHOULD be installed to enable processing of QueryImage commands

**FSM Analysis**:

Same issue as PROP_006. The FSM models `send_query_image()` but doesn't model ACL checking at the provider side.

**Verdict**: **NOT VERIFIABLE IN FSM**

---

### PROP_011: SoftwareVersion_Matching_Basic_Information_Cluster

**Claim**: SoftwareVersion in QueryImage SHALL match value reported by Basic Information Cluster

**FSM Analysis**:

QueryImage sending:
```
Idle → Querying
Action: send_query_image(selected_provider, current_software_version, ...)
```

State variable: `current_software_version: uint32`

**Issue**: The FSM doesn't model the binding between `current_software_version` and the Basic Information Cluster's SoftwareVersion attribute. It assumes they are synchronized.

**Analysis**:
- No guard condition verifying `current_software_version == BasicInformation.SoftwareVersion`
- No function to read from Basic Information Cluster before query
- Assumption: `current_software_version` is always correct

**Potential Attack**:
If `current_software_version` can be manipulated independently of Basic Information Cluster:
```
Attacker: Modifies current_software_version to 1 (very old)
State: Idle → Querying
Action: send_query_image(..., current_software_version=1, ...)
Provider: Sees very old version, offers "upgrade" to version 50
Actual version: 100 (in Basic Information Cluster)
Result: Downgrade from 100 to 50
```

**Verdict**: **VIOLATED** (if state variable can diverge from cluster attribute)

**Specification Evidence**:

*Claim*:
Query SHALL use version from Basic Information Cluster

*Gap*:
FSM doesn't enforce synchronization between FSM state variable and cluster attribute. Out-of-band updates can cause divergence:
- Out-of-band update changes Basic Information Cluster
- FSM's `current_software_version` may not be updated atomically

**Severity**: HIGH (enables version confusion attacks)

---

### PROP_012: VendorID_Matching_Basic_Information_Cluster

**Claim**: VendorID in QueryImage SHALL match Basic Information Cluster

**FSM Analysis**:

Same issue as PROP_011. The FSM uses state variable `vendor_id: uint16` without verifying it matches the cluster attribute.

**Verdict**: **VIOLATED** (if state variable can diverge)

**Severity**: CRITICAL (wrong vendor firmware could brick device)

---

### PROP_013: ProductID_Matching_Basic_Information_Cluster

**Claim**: ProductID in QueryImage SHALL match Basic Information Cluster

**FSM Analysis**:

Same issue as PROP_011/PROP_012.

**Verdict**: **VIOLATED** (if state variable can diverge)

**Severity**: CRITICAL (wrong product firmware could brick device)

---

### PROP_017: Only_HTTPS_Not_HTTP_Allowed

**Claim**: Only HTTP over TLS (HTTPS) is supported; HTTP without TLS SHALL NOT be supported

**FSM Analysis**:

The FSM has a function `is_protocol_supported()` used as guard:
```
Querying → Downloading
Guard: is_protocol_supported(response.image_uri) == true
```

Function definition:
```json
{
  "name": "is_protocol_supported",
  "algorithm": "Extract protocol from URI, check if in protocols_supported list",
  "parameters": ["uri: string"],
  "returns": "boolean",
  "usage_in_fsm": "Guard condition in Querying->Downloading transitions to validate URI protocol"
}
```

**Issue**: The function only checks if protocol is IN the list, but doesn't verify TLS for HTTP. The FSM doesn't enforce that HTTP must use TLS.

**Attack Path**:
```
State: Querying
Response: ImageURI = "http://provider.com/image.bin" (no TLS)
protocols_supported = [BDX, HTTPS, HTTP]  (implementation bug: included HTTP)
is_protocol_supported("http://...") = true (found in list)
Transition: Querying → Downloading
Action: initiate_download("http://...", HTTP)
Result: Transfer over unencrypted HTTP
```

**Specification Evidence**:

*Claim*:
> "Only HTTP over TLS (HTTPS) is supported; HTTP without TLS SHALL NOT be supported"
> Source: Need to verify exact location

*Gap*:
The FSM doesn't distinguish between HTTP and HTTPS at the guard level. The `is_protocol_supported()` function doesn't validate that HTTP URIs use TLS. Implementation could support plain HTTP if it's in the protocols_supported list.

**Verdict**: **VIOLATED** (FSM doesn't enforce TLS requirement for HTTP)

**Severity**: CRITICAL (enables MITM attacks)

---

### PROP_032: Transfer_Abort_After_Three_No_Progress_Attempts

**Claim**: SHALL abort retrying transfer after three attempts with no forward progress

**FSM Analysis**:

Transition:
```
Downloading → DownloadFailed
Trigger: download_error
Guard: retry_count >= 3 && forward_progress_count == 0
Action: abort transfer
```

**Check**: ✓ Property HOLDS

The FSM correctly implements the 3-attempt abort logic when no forward progress is made.

**Verdict**: **HOLDS**

---

### PROP_036: Provider_Must_Not_Deny_Update_For_Invalid_Token

**Claim**: Provider SHALL NOT continuously deny or delay requestor for invalid UpdateToken

**FSM Analysis**:

This is a provider-side requirement, not requestor-side. The requestor FSM shows:
```
Applying → Applying (retry)
Trigger: apply_request_timeout_or_error
Guard: retry_count < 3
Action: retry_apply_update_request()
```

The FSM allows the requestor to retry, but it doesn't model provider behavior.

**Verdict**: **NOT VERIFIABLE IN FSM** (provider-side requirement)

---

### PROP_037: Apply_Without_Additional_Delay_When_Zero

**Claim**: If DelayedActionTime is zero with Proceed, SHALL apply immediately

**FSM Analysis**:

Transition:
```
Applying → Applying
Trigger: apply_update_response_received
Guard: response.action == Proceed && response.delayed_action_time == 0
Action: apply_immediately(downloaded_image)
```

**Check**: ✓ Property HOLDS

The FSM has a specific transition for zero delay that calls `apply_immediately()`.

**Verdict**: **HOLDS**

---

### PROP_038: Apply_After_Delay_When_Non_Zero

**Claim**: If DelayedActionTime is non-zero, SHALL await at least that time

**FSM Analysis**:

Transition:
```
Applying → Applying
Guard: response.action == Proceed && response.delayed_action_time > 0
Action: wait_then_apply(downloaded_image, delay_duration)
```

**Check**: ✓ Property HOLDS (assuming wait_then_apply correctly waits)

**Verdict**: **HOLDS**

---

### PROP_040: AwaitNextAction_Minimum_120_Seconds

**Claim**: For AwaitNextAction, if DelayedActionTime < 120, SHALL assume 120

**FSM Analysis**:

Transition:
```
Applying → DelayedOnApply
Guard: response.action == AwaitNextAction && response.delayed_action_time > 0
Action: delay_duration := max(120, min(response.delayed_action_time, 86400))
```

**Check**: ✓ Property HOLDS

The FSM uses `max(120, ...)` to enforce minimum 120 seconds.

**Verdict**: **HOLDS**

---

### PROP_041: AwaitNextAction_Maximum_24_Hours_Total

**Claim**: AwaitNextAction SHALL NOT cause more than 24 hours total delay

**FSM Analysis**:

Looking at DelayedOnApply transition:
```
Action: delay_duration := max(120, min(response.delayed_action_time, 86400))
Action: total_delay_accumulated := total_delay_accumulated + delay_duration
```

State variable: `total_delay_accumulated`

But there's NO guard checking if `total_delay_accumulated > 86400` to trigger last resort.

**Last Resort Transition**:
```
Applying → Idle
Trigger: apply_request_timeout_or_error
Guard: retry_count >= 3 || time_since_download >= 86400
Action: apply_as_last_resort()
```

**Issue**: The guard checks `time_since_download >= 86400` (total time since download), but doesn't specifically check if the PROVIDER caused the delay via AwaitNextAction.

**Potential Attack Path**:
```
Time T=0: Download complete, apply request sent
Time T=1: AwaitNextAction with 23 hours delay
Time T=23h: Apply request sent again
Time T=23h+1: AwaitNextAction with 23 hours delay
Time T=46h: Apply request sent again
... (provider can delay indefinitely with 23-hour delays)
```

Wait, let me check the logic more carefully. The FSM shows:
- `time_since_download >= 86400` triggers last resort
- This is measured from download completion, not from each delay

Actually, this DOES prevent indefinite delay. After 24 hours total (from download), the last resort applies.

**Verdict**: **HOLDS** (with last resort mechanism)

---

### PROP_042: Discontinue_Action_Clears_Downloaded_Image

**Claim**: On Discontinue, SHOULD clear downloaded image

**FSM Analysis**:

Transition:
```
Applying → ImageDiscontinued
Trigger: apply_update_response_received
Guard: response.action == Discontinue
Action: clear_downloaded_image()
```

**Check**: ✓ Property HOLDS

The FSM calls `clear_downloaded_image()` on Discontinue.

**Verdict**: **HOLDS**

---

### PROP_044: Last_Resort_Apply_After_24_Hours_Failures

**Claim**: After 3 attempts or 24 hours, MAY apply as last resort

**FSM Analysis**:

Multiple transitions showing last resort:
```
Applying → Idle
Guard: retry_count >= 3 || time_since_download >= 86400
Action: apply_as_last_resort()
```

**Check**: ✓ Property HOLDS

The FSM implements last resort mechanism.

**Verdict**: **HOLDS**

---

### PROP_045: NotifyUpdateApplied_Should_Be_Sent

**Claim**: After update, SHOULD send NotifyUpdateApplied

**FSM Analysis**:

Success transitions:
```
Applying → Idle (apply_success_reboot)
Action: send_notify_update_applied(update_token, software_version)

Applying → Idle (apply_success_no_reboot)  
Action: send_notify_update_applied(update_token, software_version)
```

**Check**: ✓ Property HOLDS

Both success paths send notification.

**Verdict**: **HOLDS**

---

### PROP_046: NotifyUpdateApplied_No_Retry_On_No_Response

**Claim**: SHALL NOT retry NotifyUpdateApplied at application level

**FSM Analysis**:

The FSM shows:
```
Action: send_notify_update_applied(update_token, software_version)
```

Function definition:
```json
{
  "name": "send_notify_update_applied",
  "algorithm": "Send NotifyUpdateApplied command to provider with UpdateToken and new version. Do not retry if no response.",
  "usage_in_fsm": "Called after successful update to notify provider"
}
```

**Check**: ✓ Property HOLDS (by function definition)

**Verdict**: **HOLDS**

---

### PROP_047: BootReason_Set_After_Update_Reboot

**Claim**: BootReason SHALL be set to SoftwareUpdateCompleted after update reboot

**FSM Analysis**:

Transition:
```
Applying → Idle (apply_success_reboot)
Action: boot_reason := SoftwareUpdateCompleted
Action: reboot_device()
```

**Check**: ✓ Property HOLDS

The FSM sets boot_reason before reboot.

**Verdict**: **HOLDS**

---

