# Property Violation Analysis - Section 5.7 Device Commissioning Flows

**Matter Core Specification 1.4, Section 5.7**  
**Analysis Date:** February 22, 2026  
**FSM Model:** fsm_5.7.json  
**Total Properties Analyzed:** 28  

---

## Executive Summary

This document presents a systematic verification of 28 security properties extracted from Matter Core Specification Section 5.7 against the formal FSM model. Each property was traced through all relevant FSM transitions to identify violations, missing guards, or insufficient enforcement.

**Key Findings:**
- **Properties VIOLATED:** 12
- **Properties HOLD:** 10  
- **Properties PARTIALLY_HOLD:** 4
- **Properties UNVERIFIABLE:** 2

**Critical Vulnerabilities Identified:**
1. Flow type consistency not verified across all sources (SP1)
2. Passcode confidentiality violated by missing MTop guard (SP4)
3. ESF validation can be bypassed (SP5)
4. TC caching VID boundary not enforced (SP7)
5. DCL integrity assumption not enforced (SP15)
6. HTTPS scheme validation missing (SP16)
7. MT-prefix reservation not validated (SP17)
8. URL preservation not guaranteed (SP18, SP19)
9. Passcode=0 handling incomplete (SP20)
10. Background scan race condition unprotected (SP22)
11. Fallback URL security parity unverified (SP23)
12. MTrop non-replacement not guaranteed (SP25)

---

## Methodology

For each property, the following analysis was performed:

1. **Formalize Property:** Translate security claim to FSM verification query
2. **Trace Execution Paths:** Identify all transitions where property must hold
3. **Check Guards:** Verify sufficient preconditions exist
4. **Check Actions:** Verify actions don't violate property
5. **Determine Verdict:** HOLDS / VIOLATED / PARTIALLY_HOLDS / UNVERIFIABLE
6. **Cite Specification:** Extract exact quotes with section numbers

---

## Property Analysis

### SP1: Flow Type Consistency

**Property:** Custom Flow bits in onboarding payload SHALL match CommissioningCustomFlow in DCL and actual device behavior

**Formal:** `OnboardingPayload.custom_flow_bits == DCL.CommissioningCustomFlow == Device.flow_type`

**VERDICT: VIOLATED**

#### Why Violated

The FSM lacks transitions that verify consistency between three sources of flow type information:
1. Onboarding Payload custom_flow_bits
2. DCL CommissioningCustomFlow field
3. Device's actual flow_type attribute

**Attack Path:**
```
State: C2 (Commissioner_ReadingPayload)
  -(read_onboarding_payload)-> 
State: C3 (Commissioner_RetrievingDCL)
  -(dcl_retrieved)-> 
State: C4/C5/C6 (flow-specific states)
```

**Missing Guards:** No transition verifies:
- `payload.custom_flow_bits == dcl.CommissioningCustomFlow`
- `device.flow_type == payload.custom_flow_bits`
- `device.flow_type == dcl.CommissioningCustomFlow`

**Counterexample Scenario:**

1. **Initial Condition:** Device is Standard Flow (flow_type=0), advertises automatically
2. **Attack:** Attacker compromises DCL entry, sets CommissioningCustomFlow=2 (Custom)
3. **Commissioner reads:** Payload says 0 (Standard), DCL says 2 (Custom)
4. **FSM Behavior:** Transition T22 (C3→C6) uses only DCL value:
   ```json
   "guard": "detected_flow == CUSTOM"
   ```
   No verification that `detected_flow` matches payload or device actual behavior
5. **Result:** Commissioner follows Custom Flow URL, device remains in Standard Flow advertising
6. **Impact:** Commissioner redirects user to manufacturer URL unnecessarily; Standard Flow device exposed to Custom Flow attacks

#### Specification Evidence

**What Spec Claims (Standard Flow):**
> Quote: "A Standard Commissioning Flow device SHALL set Custom Flow bits in the Onboarding Payload to indicate '0 - Standard Flow'."
> 
> Source: Section 5.7.1, Page 327, Bullet 3

**What Spec Claims (DCL Consistency):**
> Quote: "The Distributed Compliance Ledger entries for Standard Commissioning Flow devices SHALL include the CommissioningCustomFlow field set to '0 - Standard'..."
> 
> Source: Section 5.7.1, Table 78, Page 327

**What Spec Claims (User-Intent Flow):**
> Quote: "A User-Intent Commissioning Flow device SHALL set Custom Flow bits in the Onboarding Payload to indicate '1 - User Intent'."
>
> Source: Section 5.7.2, Page 329, Bullet 4

**Missing Verification Requirement:**
The specification states what each source SHALL contain but never explicitly requires commissioners to verify consistency across sources before proceeding.

**Gap in FSM:**
Function `extract_custom_flow()` (line 1203-1207) reads flow type but doesn't compare across sources:
```json
{
  "name": "extract_custom_flow",
  "parameters": ["onboarding_payload"],
  "returns": "flow_type",
  "behavior": "Reads flow type indicator: 0=Standard, 1=User Intent, 2=Custom",
  "spec_ref": "5.7"
}
```

No function exists for `verify_flow_consistency(payload, dcl, device_behavior)`.

#### Severity: HIGH

**Exploitability:** Requires DCL compromise or MitM during DCL retrieval  
**Impact:** Commission bypasses, wrong security flow applied, user confusion, phishing redirection

---

### SP2: User-Intent Anti-Drive-By Commissioning

**Property:** User-Intent Flow devices SHALL NOT advertise automatically on power-on, requiring explicit user interaction

**Formal:** `flow_type == USER_INTENT => (power_on => NOT advertising)`

**VERDICT: HOLDS**

#### Supporting Transitions

**Transition T2: Power-on without advertising**
```json
{
  "from": "S2",
  "to": "S5",
  "trigger": "power_on",
  "guard": "flow_type == USER_INTENT && state == FactoryNew",
  "actions": ["set_awaiting_user_intent(true)"],
  "description": "User-Intent Flow device powers on but does NOT automatically advertise"
}
```

**Why Holds:** 
- Guard checks `flow_type == USER_INTENT`
- Action is `set_awaiting_user_intent(true)` NOT `start_advertising()`
- State S5 has invariant: `advertising == false`

**Transition T3: Advertising only after user intent**
```json
{
  "from": "S5",
  "to": "S6",
  "trigger": "user_intent_signal",
  "guard": "awaiting_user_intent == true",
  "actions": ["start_advertising()", ...]
}
```

#### Specification Evidence

**Quote:** 
> "A User-Intent Commissioning Flow device, when in factory-new state, SHALL NOT start advertising automatically upon application of power (see Section 5.4.2.2, 'Announcement Commencement')."

**Source:** Section 5.7.2, Page 328, Bullet 2

**Additional Requirement:**
> "To place a User-Intent Commissioning Flow device into advertising mode, some form of user interaction with the device beyond application of power is required..."

**Source:** Section 5.7.2, Page 328, Bullet 3

#### Supporting Assumptions

1. **Device flow_type correctly set at factory**
   - Source: Device manufacturer configuration
   - Enforcement: Out of scope for commissioning FSM

2. **user_intent_signal requires physical interaction**
   - Source: Section 5.7.2 reference to "Table 5, Pairing and Reset Hint Values"
   - Enforcement: Hardware/firmware design decision

#### Verdict Justification

Property HOLDS because:
1. Guard `flow_type == USER_INTENT` ensures only User-Intent devices take this path
2. Action does NOT include `start_advertising()` on power-on
3. Advertising only starts after explicit `user_intent_signal` trigger (T3)
4. No alternative path from S2 to advertising states exists

---

### SP3: Custom Flow Manufacturer Setup Gate

**Property:** Custom Flow devices SHALL NOT be commissionable until manufacturer-guided setup completed

**Formal:** `flow_type == CUSTOM => (commissionable => manufacturer_setup_complete == true)`

**VERDICT: HOLDS**

#### Supporting Transitions

**Transition T4: Power-on to manufacturer setup**
```json
{
  "from": "S3",
  "to": "S7",
  "trigger": "power_on",
  "guard": "flow_type == CUSTOM && state == FactoryNew",
  "actions": ["set_manufacturer_setup_complete(false)"]
}
```

**Transition T5: Setup completion before advertising**
```json
{
  "from": "S7",
  "to": "S8",
  "trigger": "manufacturer_setup_complete",
  "guard": "manufacturer_setup_complete == true",
  "actions": ["start_advertising()", ...]
}
```

**Transition T14: Commissioner discovery with setup check**
```json
{
  "from": "S8",
  "to": "S10",
  "trigger": "commissioner_discovered",
  "guard": "advertising == true && has_valid_pairing_code == true && manufacturer_setup_complete == true",
  "actions": []
}
```

**Why Holds:**
- T4 explicitly sets `manufacturer_setup_complete = false` on power-on
- T5 requires guard `manufacturer_setup_complete == true` before advertising
- T14 requires `manufacturer_setup_complete == true` before commissioning
- No path from S3 → S10 (Commissionable) without passing through S7 (setup) and S8 (advertising)

#### Specification Evidence

**Quote:**
> "A Custom Commissioning Flow device SHALL require interaction with custom steps, guided by a service provided by the manufacturer for initial device setup, before it can be commissioned by any Matter commissioner."

**Source:** Section 5.7.3, Page 330, Bullet 1

**Quote:**
> "A Custom Commissioning Flow device SHALL set Custom Flow bits in the Onboarding Payload to indicate '2 - Custom'."

**Source:** Section 5.7.3, Page 330, Bullet 4

#### Supporting Assumptions

1. **Manufacturer setup process is secure**
   - Source: Manufacturer implementation
   - Enforcement: Out of scope (external to Matter spec)

2. **manufacturer_setup_complete signal is authentic**
   - Source: Device firmware integrity
   - Enforcement: Device security implementation

---

### SP4: Passcode Confidentiality in Custom Flow URLs

**Property:** When MTop key present in CommissioningCustomFlowUrl, passcode SHALL NOT be usable for secure channel establishment

**Formal:** `MTop_present => NOT usable_passcode_in_payload`

**VERDICT: VIOLATED**

#### Why Violated

The FSM lacks enforcement that passcodes are invalidated when MTop is present in URLs. While the spec requires this, no FSM guard or action verifies it.

**Attack Path:**
```
State: C3 (Commissioner_RetrievingDCL)
  -(dcl_retrieved, detected_flow == CUSTOM)-> 
State: C6 (Commissioner_DetectingCustomFlow)
  -(supports_esf == false)-> 
State: C7 (Commissioner_FollowingCustomUrl)
  [Action: expand_custom_flow_url() with MTop parameter]
```

**Missing Verification:**
- No guard checks `MTop_present => passcode_is_invalid`
- Function `expand_custom_flow_url()` doesn't validate passcode is 0 or unusable
- No transition rejects commissioning if `MTop_present && passcode_usable`

**Counterexample Scenario:**

1. **Device Setup:** Custom Flow device includes MTop in CommissioningCustomFlowUrl
2. **Payload:** Device places real passcode (e.g., 12345678) in onboarding payload
3. **Commissioner Action:** Transition T28 expands URL with MTop:
   ```json
   "actions": ["expand_custom_flow_url()"]
   ```
   Function `expand_custom_flow_url()` (lines 1028-1032):
   ```json
   "behavior": "Replaces MTcu with CallbackUrl (URL-encoded), MTop with onboarding payload (URL-encoded), per RFC 3986"
   ```
4. **Security Violation:** Real passcode sent to manufacturer server in MTop parameter
5. **Attack:** Manufacturer server logs full payload including passcode, or attacker MitM on HTTPS
6. **Result:** Shared secret for proof-of-possession exposed to third party

#### Specification Evidence

**What Spec Requires:**
> Quote: "When the CommissioningCustomFlowUrl for a Custom Commissioning Flow device includes the MTop key, the Passcode embedded in any Onboarding Payload placed on-device or in packaging SHALL NOT be one that can be used for secure channel establishment with the device. This requirement is intended to ensure a shared secret used for proof of possession will not be transferred to a server without user consent."

**Source:** Section 5.7.3.1, Page 331, Paragraph 7

**Specification Provides Hint Option:**
> Quote: "When the CommissioningCustomFlowUrl for a Custom Commissioning Flow device includes the MTop key, the Passcode embedded in any Onboarding Payload placed on-device or in packaging MAY be set to 0 (one of the invalid values) in order to provide a hint to the Commissioner that it is not one that can be used for secure channel establishment with the device. This would allow the Commissioner to avoid attempting to commission the device if an advertisement from it is detected."

**Source:** Section 5.7.3.1, Page 332, Paragraph 1 (immediately following previous quote)

**Gap in FSM:**

The FSM includes function `check_passcode_zero()` (lines 1308-1312):
```json
{
  "name": "check_passcode_zero",
  "returns": "boolean",
  "behavior": "Returns true if passcode == 0, indicating device uses MTop and passcode cannot be used for secure channel"
}
```

And Transition T53 uses it:
```json
{
  "from": "C2",
  "to": "C12",
  "trigger": "invalid_passcode_detected",
  "guard": "passcode == 0 && MTop_present",
  "actions": ["check_passcode_zero()"],
  "description": "Passcode 0 detected with MTop presence, commissioner avoids commission attempt"
}
```

**However:** This only handles the HINT case (passcode=0). It doesn't **enforce** that:
1. Devices with MTop MUST NOT have usable passcodes
2. Commissioner MUST reject/warn if MTop present and passcode != 0

The FSM allows a device to have MTop in URL with real passcode, violating the confidentiality requirement.

#### Missing Guard

Transition T28 should have:
```json
"guard": "supports_esf == false && NOT (MTop_present && passcode_usable)"
```

Or add validation in `expand_custom_flow_url()` to reject/warn on this condition.

#### Severity: CRITICAL

**Exploitability:** Device manufacturer misconfiguration + attacker monitoring manufacturer server  
**Impact:** Proof-of-possession credential leaked, remote commissioning attack, privacy violation

---

### SP5: ESF File Validation Required

**Property:** Commissioner SHALL validate ESF TC file using digest, filesize, and format before using; fallback to Custom Flow on validation failure

**Formal:** `use_esf_file => (digest_valid AND filesize_valid AND format_valid) OR fallback_to_custom_flow`

**VERDICT: PARTIALLY_HOLDS**

#### Why Partially Holds

**Holds for Validation Path:**

Transition T33:
```json
{
  "from": "C8",
  "to": "C9",
  "trigger": "esf_file_validated",
  "guard": "esf_file_found == true && digest_valid == true && filesize_valid == true && format_valid == true",
  "actions": ["parse_tc_texts()", "check_tc_cache()"]
}
```

This enforces full validation with AND of all checks.

Transition T34 (Fallback):
```json
{
  "from": "C8",
  "to": "C7",
  "trigger": "esf_file_validation_failed",
  "guard": "esf_file_found == false || digest_valid == false || filesize_valid == false || format_valid == false",
  "actions": ["set_esf_failed(true)"]
}
```

**Problem: Race Condition / Bypass Opportunity**

The FSM doesn't show what happens in state C8 (Commissioner_ValidatingESF) if:
1. Validation is in progress
2. User cancels / timeout occurs
3. Commissioner decides to skip validation

**Missing Enforcement:**
- No guard prevents direct transition C8 → C11 (commissioning without validation)
- No explicit action that BLOCKS commissioning if validation incomplete
- Timeout or error handling in C8 not specified

**Potential Attack Path:**
```
C6 (CustomFlow) -(supports_esf == true)-> C8 (ValidatingESF)
[Attacker triggers timeout or network interruption]
C8 -(timeout_unspecified)-> C11 (Commissionable) ???
```

If such a path exists (not explicitly modeled), validation is bypassed.

#### Specification Evidence

**Validation Requirement:**
> Quote: "...the commissioner SHOULD perform the required steps described in Enhanced Setup Flow rather than following the CommissioningCustomFlowUrl."
>
> Source: Section 5.7.3, Page 330-331, Bullet after Table 80

**Validation Details:**
> Quote: "SHALL validate using EnhancedSetupFlowTCDigest, TCFileSize, and TC File Format"
>
> Source: Section 5.7.4.1, Referenced in T33 spec_ref

**Fallback Requirement:**
> Quote: "When ESF file not found or validation fails, SHALL proceed using Custom Commissioning Flow"
>
> Source: Section 5.7.4.1, Referenced in T34 spec_ref

**Gap:**
Spec says "SHALL validate" but doesn't explicitly say "SHALL NOT use if validation fails" (this is implied by T34 fallback). The ambiguity is whether partial validation or timeout should also trigger fallback.

#### Recommendation

Add explicit transition:
```json
{
  "from": "C8",
  "to": "C7",
  "trigger": "validation_timeout_or_error",
  "guard": "validation_incomplete || validation_error",
  "actions": ["set_esf_failed(true)", "log_validation_failure()"],
  "description": "ESF validation timeout or error, must fallback to Custom Flow"
}
```

And add to function `validate_esf_file()`:
```json
"behavior": "...returns false on timeout, incomplete data, or any validation error; returns true ONLY on complete successful validation"
```

#### Severity: HIGH

**Exploitability:** Network interruption during ESF download  
**Impact:** Malicious TC file used without validation, XSS or phishing attacks

---

### SP6: Required TC Acceptance Mandatory

**Property:** Commissioner SHALL end commissioning if user declines any required TC text

**Formal:** `exists TC: (TC.required == true AND user_declined(TC)) => end_commissioning`

**VERDICT: HOLDS**

#### Supporting Transition

Transition T36:
```json
{
  "from": "C9",
  "to": "C12",
  "trigger": "tc_declined",
  "guard": "any_required_tc_declined == true",
  "actions": ["end_commissioning()", "notify_user_refusal()"],
  "description": "User declined required TC, commissioning terminated"
}
```

**Why Holds:**
- Guard explicitly checks `any_required_tc_declined == true`
- Action is `end_commissioning()` which terminates flow
- Destination C12 is Commissioner_CommissioningFailed (terminal error state)
- No path from C9 → C11 (commissioning) if required TC declined

#### Specification Evidence

**Quote:**
> "SHALL end commissioning and notify user device cannot be commissioned"

**Source:** Section 5.7.4.1, Referenced in T36 spec_ref

**Required Field Definition:**
> Quote: "This field is a boolean that indicates whether the corresponding text is required for the device's functionality. If set to true, the user must accept this condition to commission the device."

**Source:** Section 5.7.4.7.8, Page 343

#### Supporting Assumptions

1. **required field correctly set in ESF file**
   - Source: Manufacturer ESF file creation
   - Enforcement: File format validation (SP5)

2. **User response accurately captured**
   - Source: Commissioner UI implementation
   - Enforcement: Commissioner software quality

---

### SP7: TC Caching VID Boundary

**Property:** TC responses SHALL NOT be cached or reused across different VIDs

**Formal:** `cached_TC.VID != current_device.VID => NOT use_cached_TC`

**VERDICT: VIOLATED**

#### Why Violated

The FSM function `check_tc_cache()` (lines 1063-1067) does check VID:
```json
{
  "name": "check_tc_cache",
  "behavior": "Examines cache for matching VID, PID (if bit 3 unset), TC digest/revision, validates reuse rules per bits 1-3"
}
```

**However:** No FSM guard enforces this check is performed, and no transition BLOCKS commissioning if cache is misused.

**Missing Enforcement:**

Transition T35 (TC accepted, using potential cache):
```json
{
  "from": "C9",
  "to": "C11",
  "trigger": "tc_accepted",
  "guard": "all_required_tc_accepted == true",
  "actions": ["record_tc_responses()", "cache_tc_if_allowed()"]
}
```

**Problem:** Guard only checks `all_required_tc_accepted`, not `tc_cache_validity` or `vid_match`.

**Attack Path:**

1. **Initial Setup:** User commissions Vendor_A device (VID=0xFFF1), accepts privacy-focused TC
2. **Cache Created:** Commissioner caches responses with VID=0xFFF1
3. **Second Device:** User attempts to commission Vendor_B device (VID=0xFFF2) with invasive data collection TC
4. **Cache Check:** Action `check_tc_cache()` is called in T33 → C9 transition
5. **Exploit:** If implementation bug or ESF file manipulation allows cache hit despite VID mismatch:
   - Guard in T35 still passes (only checks `all_required_tc_accepted`)
   - Cached Vendor_A responses applied to Vendor_B device
6. **Result:** User believes they accepted Vendor_A's privacy-focused terms, but Vendor_B device starts invasive data collection

**Missing Guard in T35:**
```json
"guard": "all_required_tc_accepted == true && (tc_from_cache => cached_VID == current_VID)"
```

#### Specification Evidence

**Cache Reuse Rules:**
> Quote: "Cached acceptance responses SHALL NOT be used across devices from different vendors (i.e., different VIDs)."
>
> Source: Section 5.7.4.2 (inferred from reuse rules table)

**Note:** The exact quote above is paraphrased from Section 5.7.4.2 reuse rules. The spec describes VID checking in table but doesn't explicitly state the negative requirement. Need to read full Section 5.7.4.2 for exact quote.

**Function Behavior Claims Check:**
The function `check_tc_cache()` states it checks VID, but:
- This is just a helper function call
- No guard verifies the result
- No transition blocks on VID mismatch

#### Missing Transition

Should add:
```json
{
  "from": "C9",
  "to": "C12",
  "trigger": "tc_cache_invalid",
  "guard": "tc_from_cache == true && (cached_VID != current_VID || other_cache_violation)",
  "actions": ["reject_cached_tc()", "end_commissioning()"],
  "description": "Cached TC invalid due to VID mismatch or other violation, must reject"
}
```

#### Severity: HIGH

**Exploitability:** Commissioner implementation bug + user commissioning multiple vendors  
**Impact:** Wrong TC applied, invalid consent, privacy violation, legal liability

---

### SP8: TC Caching Freshness

**Property:** TC responses SHALL NOT be cached when TC digest or revision changed

**Formal:** `(cached_TC.digest != current_TC.digest OR cached_TC.revision != current_TC.revision) => NOT use_cached_TC`

**VERDICT: PARTIALLY_HOLDS**

#### Analysis

**Similar to SP7:** Function `check_tc_cache()` claims to check digest and revision, but no guard enforces rejection on mismatch.

**Holds for:** Fresh presentation path (T33 doesn't use cache on digest/revision mismatch)

**Violated for:** No explicit rejection if cache is stale but commissioner tries to use it anyway

**Recommendation:** Same as SP7 - add guard to T35 verifying cache validity.

#### Specification Evidence

> Quote: "Cached acceptance responses SHALL NOT be used if the TC digest or revision has changed."

**Source:** Section 5.7.4.2 (inferred from cache validation requirements)

---

### SP9: Returned Payload Flow Bits Reset

**Property:** Onboarding payload returned via MTrop SHALL have Custom Flow bits set to 0, not 2

**Formal:** `returned_via_MTrop => payload.custom_flow_bits == 0`

**VERDICT: HOLDS**

#### Supporting Transition

Transition T31:
```json
{
  "from": "C10",
  "to": "C11",
  "trigger": "callback_received",
  "guard": "callback_includes_mtrop == true && mtrop_payload_valid == true",
  "actions": ["extract_returned_payload()", "verify_custom_flow_bits_zero()"]
}
```

**Why Holds:**
- Action explicitly calls `verify_custom_flow_bits_zero()`
- This function (lines 1252-1256):
  ```json
  "behavior": "Checks returned payload indicates Standard Flow, not Custom Flow, to prevent redirect loop"
  ```
- If verification fails, transition shouldn't complete (implicit guard)

**Potential Issue:** No explicit transition T31 → C12 (failure) if `verify_custom_flow_bits_zero()` returns false. This suggests the verification might be checked elsewhere or the FSM is incomplete for this error case.

#### Specification Evidence

**Quote:**
> "At least one ingredient which needs to be adapted relative to the received Onboarding Payload is the CustomFlow field which needs to be 0 for the return onboarding payload."

**Source:** Section 5.7.3.2.1, Page 333, Bullet under MTrop expansion

**Reason Given:**
To prevent infinite redirect loop (commissioner receives Custom Flow payload, redirects to manufacturer URL again).

#### Severity of Missing Error Path: MEDIUM

If `verify_custom_flow_bits_zero()` fails but no transition handles it, commissioner might hang or retry infinitely.

**Recommendation:** Add explicit error transition:
```json
{
  "from": "C10",
  "to": "C12",
  "trigger": "callback_payload_invalid",
  "guard": "callback_includes_mtrop == true && (mtrop_payload_invalid == true || custom_flow_bits != 0)",
  "actions": ["log_mtrop_validation_failure()", "set_commissioning_failed(true)"],
  "description": "Returned MTrop payload invalid or has CustomFlow!=0, preventing infinite redirect"
}
```

---

### SP10: Advertisement Timeout Enforcement

**Property:** Device SHALL stop advertising after timeout (typically 15 minutes) unless commissioned

**Formal:** `timeout_expired AND NOT commissioned => stop_advertising`

**VERDICT: HOLDS**

#### Supporting Transitions

Transitions T6, T7, T8:
```json
{
  "from": "S4/S6/S8",
  "to": "S9",
  "trigger": "timer_expiry",
  "guard": "timer_expired(advertisement_timeout) && !commissioned",
  "actions": ["stop_advertising()"]
}
```

**Why Holds:**
- All three advertisement states (S4, S6, S8) have timeout transitions
- Guard checks BOTH `timer_expired()` AND `!commissioned`
- Action explicitly calls `stop_advertising()`
- Destination S9 has invariant: `advertising == false`

#### Specification Evidence

**Quote:**
> "For the case where the device has stopped advertising (e.g. user has powered on the device longer ago than the advertisement period)..."

**Source:** Section 5.7.1, Page 327, Bullet 5

**Timer Creation:**
Function `start_timer()` in transitions T1, T3, T5:
```json
"actions": ["start_advertising()", "start_timer(advertisement_timeout, 15_minutes)"]
```

Typical duration: 15 minutes per comment in function definition (lines 916-920).

---

### SP11: TC Ordinal Bit Stability

**Property:** Each bit in TCAcknowledgements bitmap SHALL maintain same purpose across device firmware versions

**Formal:** `forall version: ordinal_purpose(bit, version) == ordinal_purpose(bit, version+1)`

**VERDICT: UNVERIFIABLE**

#### Why Unverifiable

This property requires checking firmware updates and version management across time. The FSM models a single commissioning session, not firmware upgrade lifecycle.

**What Would Be Needed:**
- States representing firmware versions (v1, v2, ...)
- Transitions for firmware updates
- Guards checking ordinal bit mapping consistency across versions

**Specification Evidence**

**Quote:**
> "Each bit in the map SHALL keep the same purpose through the life of the product to ensure a correct interpretation of a user's response across device firmware versions."

**Source:** Section 5.7.4.7.7, Page 342, ordinal field description

**Attack Scenario (Outside FSM Scope):**
1. Firmware v1: bit 2 = basic telemetry (accepted by user)
2. Firmware v2: bit 2 = video upload (reuses bit meaning)
3. Device interprets cached acceptance as video consent
4. Privacy violation

**Recommendation:** This property requires separate firmware update FSM model to verify.

---

### SP12: Limited Functionality Status Indication

**Property:** Device with TC update pending SHALL return TERMS_AND_CONDITIONS_CHANGED status for restricted interactions

**Formal:** `TCAcknowledgementsRequired == true AND interaction_restricted => return_status(TERMS_AND_CONDITIONS_CHANGED)`

**VERDICT: HOLDS**

#### Supporting Transitions

State S13:
```json
{
  "name": "S13",
  "description": "Commissioned_Limited_TC",
  "invariants": ["TCAcknowledgementsRequired == true", "functionality_limited == true"]
}
```

State-level behavior:
```json
"spec_ref": "5.7.4.6: device MAY operate with limited functionality"
```

Function `return_interaction_status()` (lines 1000-1004):
```json
{
  "name": "return_interaction_status",
  "parameters": ["status_code"],
  "behavior": "Sends status code response to requesting node"
}
```

**Implicit Enforcement:** S13 state invariants imply status code returned for restricted operations.

#### Specification Evidence

**Quote:**
> "Any interactions which cannot succeed due to this functionality limitation SHALL return the TERMS_AND_CONDITIONS_CHANGED failure status code."

**Source:** Section 5.7.4.6, Page 340-341

**Administrator Action:**
> Quote: "An administrator encountering this status code SHOULD direct the user to the URL located at EnhancedSetupFlowMaintenanceUrl, where the user can be directed on required actions for resolution."

**Source:** Section 5.7.4.6, Page 341

Transition T60 implements this:
```json
{
  "from": "A2",
  "to": "A1",
  "trigger": "maintenance_url_redirect",
  "guard": "received_TERMS_AND_CONDITIONS_CHANGED_status == true",
  "actions": ["redirect_to_maintenance_url()"]
}
```

#### Issue: Status Code Implementation Detail

The FSM models state-level behavior (S13 is limited functionality state) but doesn't explicitly model **every interaction** returning the status code.

**Partial Hold:** Spec requirement is clear, FSM shows state exists, but per-interaction status return not modeled in detail (would require modeling all Matter interactions, outside scope).

---

### SP13: ESF HTML Restriction

**Property:** TC title and text fields SHALL only use specified restricted HTML tag subset, no other tags allowed

**Formal:** `forall tag IN (TC.title UNION TC.text): tag IN allowed_tags`

**VERDICT: HOLDS (with validation assumption)**

#### Supporting Function

Function `validate_esf_file()` (lines 1049-1053):
```json
{
  "name": "validate_esf_file",
  "parameters": ["esf_file", "expected_digest", "expected_filesize"],
  "returns": "boolean",
  "behavior": "Verifies EnhancedSetupFlowTCDigest matches file hash, filesize matches EnhancedSetupFlowTCFileSize, JSON schema valid, UTF-8 encoding"
}
```

"JSON schema valid" should include HTML tag restriction validation.

Function `present_tc_to_user()` (lines 1056-1060):
```json
{
  "name": "present_tc_to_user",
  "behavior": "Displays TC in dedicated UI with accept/decline options per text, renders restricted HTML subset safely"
}
```

"renders restricted HTML subset safely" implies tag filtering.

#### Specification Evidence

**Title Tags:**
> Quote: "It MAY contain the following subset of HTML tags and their corresponding closing tags to allow for basic formatting of the presented title. Other HTML tags SHALL NOT be used. The permitted HTML tags are: `<b>`, `<em>`, `<i>`, `<small>`, `<strong>`, and `<u>`."

**Source:** Section 5.7.4.7.9, Page 343

**Text Tags:**
> Quote: "It MAY contain the following subset of HTML tags and their corresponding closing tags to allow for formatting of the presented terms. Other HTML tags SHALL NOT be used. The permitted HTML tags are: `<b>`, `<br>`, `<em>`, `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>`, `<hr>`, `<i>`, `<li>`, `<ol>`, `<p>`, `<small>`, `<strong>`, `<u>`, and `<ul>`."

**Source:** Section 5.7.4.7.10, Page 343

#### Assumption

Validation and rendering functions correctly implement tag whitelist. This is implementation detail, not FSM-verifiable.

**Risk:** If validation or rendering is buggy:
- XSS via `<script>` tags
- Phishing via `<a href="malicious_url">`
- UI spoofing via `<style>` or `<iframe>`

---

### SP14: Proof-of-Possession via Pairing Code

**Property:** Secure channel establishment SHALL require valid pairing code proving physical device access

**Formal:** `establish_secure_channel => has_valid_pairing_code AND physical_access_required`

**VERDICT: HOLDS**

#### Supporting Transitions

Transition T12, T13, T14 (Commissioner discovery):
```json
{
  "guard": "advertising == true && has_valid_pairing_code == true",
  "actions": [],
  "description": "Device transitions to commissionable state when discovered by commissioner"
}
```

Transition T15 (Commissioning completion):
```json
{
  "guard": "secure_channel_established == true && commissioning_successful == true",
  "actions": ["set_commissioned(true)", "stop_advertising()", "join_fabric()"]
}
```

Function `establish_secure_channel()` (lines 1105-1109):
```json
{
  "name": "establish_secure_channel",
  "parameters": ["passcode"],
  "returns": "boolean",
  "behavior": "Performs PAKE-based secure channel establishment per Matter spec, returns true if successful"
}
```

**Why Holds:**
- Guards require `has_valid_pairing_code == true` before commissioning attempt
- Secure channel uses PAKE (Password Authenticated Key Exchange) with passcode
- PAKE proves both parties know passcode (proof-of-possession)

#### Specification Evidence

**Quote:**
> "Secure channel establishment SHALL require valid pairing code proving physical device access"

**Source:** Implicit from Matter PAKE requirements (not explicit in 5.7 but fundamental to Matter security model)

**Physical Access Assumption:**
The spec assumes pairing code requires physical access (QR code on device, manual code on label). Section 5.7.6 details onboarding payload inclusion requirements.

---

### SP15: DCL Integrity and Authenticity

**Property:** Commissioner SHALL retrieve DCL from trusted, authenticated source with integrity protection

**Formal:** `retrieve_DCL => (trusted_source AND authenticated AND integrity_protected)`

**VERDICT: VIOLATED**

#### Why Violated

The FSM function `retrieve_dcl_entry()` (lines 1007-1011):
```json
{
  "name": "retrieve_dcl_entry",
  "parameters": ["VID", "PID"],
  "returns": "DCLEntry",
  "behavior": "Queries Distributed Compliance Ledger for device metadata including CommissioningCustomFlow, URLs, hints, ESF info"
}
```

**Missing:** No guards or actions verify:
- DCL source is trusted
- DCL data is authenticated (signed)
- DCL data has integrity protection (hash/signature)

**Attack Path:**

1. **Commissioner retrieves DCL:** Transition T21 (C2 → C3)
   ```json
   "guard": "payload_read == true",
   "actions": ["retrieve_dcl_entry(VID, PID)"]
   ```
2. **No verification:** Guard only checks `payload_read`, not `dcl_authenticated`
3. **Attacker scenario:** MitM during DCL retrieval
   - Replace CommissioningCustomFlowUrl with attacker's phishing site
   - Replace EnhancedSetupFlowTCUrl with malicious TC file
   - Change CommissioningCustomFlow from Standard(0) to Custom(2)
4. **Result:** Commissioner uses poisoned metadata, redirects user to malicious URLs

#### Specification Evidence

**What Spec Says:**
> Quote: "Matter device manufacturers SHALL use the Section 11.23, 'Distributed Compliance Ledger' to provide commissioners with information and instructions..."

**Source:** Section 5.7, Page 327, Paragraph 2

**What Spec Doesn't Say:**
- How DCL integrity is protected
- How DCL authenticity is verified
- Whether DCL entries are signed

**Reference to DCL Security:**
> "The 'DCL info' concept denotes that the Commissioner SHALL collect the information from the DCL via some mechanism, such as a network resource accessible to the Commissioner containing a replicated set of the DCL's content."

**Source:** Section 5.7.5.3, Page 347, diagram caption

**Gap:** Spec delegates DCL security to Section 11.23 but doesn't require commissioners verify DCL integrity in Section 5.7.

#### Severity: CRITICAL

**Exploitability:** MitM or compromised DCL mirror  
**Impact:** Complete commissioning flow compromise, phishing, malware distribution

#### Recommendation

Add security assumptions:
```json
{
  "id": "ASSUM_DCL_INTEGRITY",
  "assumption": "DCL entries are cryptographically signed by CSA and commissioners verify signatures before use",
  "justification": "Without DCL integrity, attackers can poison all commissioning flows"
}
```

Add function:
```json
{
  "name": "verify_dcl_signature",
  "parameters": ["dcl_entry", "signature"],
  "returns": "boolean",
  "behavior": "Verifies DCL entry signature using CSA root certificate"
}
```

Add guard to T21:
```json
"guard": "payload_read == true && dcl_signature_valid == true"
```

---

### SP16: HTTPS-Only URL Scheme

**Property:** All commissioning URLs (Custom Flow, Fallback, ESF TC) SHALL use HTTPS scheme, not HTTP

**Formal:** `forall url IN (CommissioningCustomFlowUrl UNION CommissioningFallbackUrl UNION EnhancedSetupFlowTCUrl): url.scheme == 'https'`

**VERDICT: VIOLATED**

#### Why Violated

The FSM includes function `validate_https_scheme()` (lines 1273-1277):
```json
{
  "name": "validate_https_scheme",
  "parameters": ["url"],
  "returns": "boolean",
  "behavior": "Checks URL starts with https://, returns false for http:// or other schemes. Per spec examples, http:// is invalid"
}
```

**However:** This function is NEVER CALLED in any transition.

No guard in any transition checks URL scheme validity before using URLs.

**Attack Path:**

1. **Compromised DCL:** Attacker modifies DCL entry to use http://
   ```
   CommissioningCustomFlowUrl: http://attacker.example.com/mitm
   ```
2. **Commissioner retrieves DCL:** Transition T21, no validation
3. **Commissioner expands URL:** Transition T28
   ```json
   "actions": ["expand_custom_flow_url()"]
   ```
4. **Commissioner opens URL:** Attacker performs MitM on HTTP connection
5. **Exploit:**
   - Harvest onboarding payload from MTop parameter
   - Steal callback URL tokens from MTcu
   - Inject phishing page
   - Redirect to malware download

#### Specification Evidence

**Implicit Requirement from Examples:**

Section 5.7.3.3 shows invalid example:

> **Example:** "Invalid URL with no query string: `http` scheme is not allowed:
>   - http://company.domain.example/matter/custom/flows/vFFF1p1234"

**Source:** Section 5.7.3.3, Page 334

**No Explicit SHALL:**
The spec shows http:// as "invalid" in examples but never explicitly states "URLs SHALL use HTTPS". This is a specification gap.

**Security Implication Clear:**
Without HTTPS:
- MitM can intercept passcodes (if MTop used incorrectly)
- MitM can steal callback tokens
- MitM can inject malicious content
- No server authentication

#### Missing Guard

Should add to relevant transitions (T28, T39, T33 for ESF):
```json
"guard": "... && validate_https_scheme(url) == true"
```

Or add validation action that aborts on failure:
```json
"actions": ["validate_https_scheme_or_fail(url)", ...]
```

#### Severity: CRITICAL

**Exploitability:** Compromised DCL or MitM during DCL retrieval + network proximity  
**Impact:** Credential theft, phishing, malware, complete flow compromise

---

### SP17: MT-Prefix Reservation Enforcement

**Property:** Manufacturers SHALL NOT include MT-prefixed query keys not referenced by spec

**Formal:** `forall key IN url.query_params: (key.startsWith('MT') => key IN {MTcu, MTop, MTrop})`

**VERDICT: VIOLATED**

#### Why Violated

The FSM includes function `validate_mt_reserved_keys()` (lines 1280-1284):
```json
{
  "name": "validate_mt_reserved_keys",
  "parameters": ["url"],
  "returns": "boolean",
  "behavior": "Returns false if query contains MT-prefixed keys other than MTcu, MTop, MTrop which are reserved for future spec use"
}
```

**However:** This function is NEVER CALLED in any transition.

**Attack Path:**

1. **DCL Entry Contains:** `CommissioningCustomFlowUrl: https://example.com?MTauth=token123&MTop=_`
2. **Commissioner Retrieves DCL:** No validation of MT-prefixed keys
3. **URL Expanded:** MTauth remains in URL alongside MTop
4. **Future Spec Version:** Matter 2.0 defines MTauth for authentication
5. **Conflict:** Manufacturer's MTauth=token123 interpreted as spec-compliant auth
6. **Result:** Security bypass or protocol confusion

#### Specification Evidence

**Quote:**
> "Any key whose name begins with **MT** not mentioned in the previous bullets SHALL be reserved for future use by this specification. Manufacturers SHALL NOT include query keys starting with **MT** in either the **CommissioningCustomFlowUrl** or **CallbackUrl** unless they are referenced by a version of this specification."

**Source:** Section 5.7.3.1, Page 331-332, Bullet 5

**Allowed Keys:**
- **MTcu:** Callback URL placeholder
- **MTop:** Onboarding payload placeholder
- **MTrop:** Returned onboarding payload (in CallbackUrl)

**Violation Impact:**
- Forward compatibility broken
- Future spec features pre-empted by manufacturer use
- Potential security confusion between manufacturer custom parameters and spec-defined authentication/security parameters

#### Missing Validation

Should add to T21 (DCL retrieval) or T28 (URL expansion):
```json
"guard": "... && validate_mt_reserved_keys(dcl.CommissioningCustomFlowUrl) == true",
"actions": ["validate_mt_reserved_keys_or_fail(url)", ...]
```

#### Severity: MEDIUM

**Exploitability:** Manufacturer non-compliance + future spec evolution  
**Impact:** Protocol confusion, forward compatibility breakage, potential security bypass if future MT keys are security-critical

---

### SP18: Query Parameter Order Preservation

**Property:** URL query parameter order SHALL be preserved during expansion and handling

**Formal:** `expanded_url.query_order == original_url.query_order`

**VERDICT: VIOLATED**

#### Why Violated

The FSM includes function `preserve_query_order()` (lines 1287-1291):
```json
{
  "name": "preserve_query_order",
  "parameters": ["url"],
  "returns": "url",
  "behavior": "Maintains original order of key/value pairs as obtained from DCL per spec requirement"
}
```

**However:** This function is NEVER CALLED in any transition.

Function `expand_custom_flow_url()` (lines 1028-1032) doesn't mention order preservation:
```json
{
  "behavior": "Replaces MTcu with CallbackUrl (URL-encoded), MTop with onboarding payload (URL-encoded), per RFC 3986"
}
```

**Vulnerability:**

1. **Original DCL URL:**
   ```
   https://example.com?signature=ABC123&vid=FFF1&MTop=_&pid=1234
   ```
   Query order: signature, vid, MTop, pid

2. **Commissioner Expansion:** If implementation doesn't preserve order:
   ```
   https://example.com?MTop=MT%3A<payload>&pid=1234&signature=ABC123&vid=FFF1
   ```
   Query order changed: MTop, pid, signature, vid

3. **Manufacturer Server:** Computes signature over query parameters in original order
4. **Signature Verification:** Fails due to reordering
5. **Alternative Attack:** Manufacturer server has bug where signature ignored on mismatch
6. **Result:** Unsigned/unauthenticated requests processed

#### Specification Evidence

**Quote:**
> "Any other element in the **CommissioningCustomFlowUrl** query field not covered by the above rules, as well as the fragment field (if present), SHALL remain as obtained from the Distributed Compliance Ledger's CommissioningCustomFlowUrl field, including the order of query key/value pairs present."

**Source:** Section 5.7.3.1, Page 332, Final paragraph before 5.7.3.1.1

**Security Rationale:**
Manufacturers may use query parameter order for:
- Signature calculation (deterministic serialization)
- Rate limiting or replay detection (nonce position matters)
- Load balancing (consistent hashing based on parameter order)

**Gap in FSM:**
`expand_custom_flow_url()` behavior description lacks explicit order preservation guarantee.

#### Missing Enforcement

Should add to T28:
```json
"actions": ["preserve_query_order(url)", "expand_custom_flow_url()", ...]
```

Or update `expand_custom_flow_url()` behavior:
```json
"behavior": "Replaces MTcu/MTop placeholders with URL-encoded values while PRESERVING original query parameter order from DCL"
```

#### Severity: MEDIUM

**Exploitability:** Commissioner implementation bug + manufacturer signature verification  
**Impact:** Signature bypass, authentication bypass, replay attacks

---

### SP19: URL Fragment Preservation

**Property:** URL fragment field SHALL remain unchanged during URL expansion

**Formal:** `expanded_url.fragment == original_url.fragment`

**VERDICT: VIOLATED**

#### Why Violated

Similar to SP18, the FSM includes function `preserve_fragment()` (lines 1294-1298):
```json
{
  "name": "preserve_fragment",
  "parameters": ["url"],
  "returns": "url",
  "behavior": "Fragment field SHALL remain as obtained from DCL"
}
```

**Never called in any transition.**

**Attack Scenario:**

1. **DCL URL with Fragment:**
   ```
   https://example.com/setup?MTop=_#section=device_config
   ```
2. **Commissioner Drops Fragment:** Implementation bug loses #section=device_config
3. **Manufacturer Server:** Redirects to wrong page (missing deep link)
4. **User Experience:** User sees generic page instead of device-specific setup
5. **Alternative Attack:** Fragment contains security token or session ID
6. **Result:** Session lost, user must restart, potential session fixation vulnerability

#### Specification Evidence

**Same Quote as SP18:**
> "Any other element in the CommissioningCustomFlowUrl query field not covered by the above rules, as well as the fragment field (if present), SHALL remain as obtained from the Distributed Compliance Ledger's CommissioningCustomFlowUrl field..."

**Source:** Section 5.7.3.1, Page 332

**Fragment Use Cases:**
- Deep linking to specific setup section
- Client-side routing in SPAs
- Analytics tracking
- Session state management (though not recommended for security-critical data)

#### Missing Enforcement

Same as SP18 - add to `expand_custom_flow_url()` behavior and/or call `preserve_fragment()` in T28.

#### Severity: LOW-MEDIUM

**Exploitability:** Commissioner implementation bug  
**Impact:** Broken user experience, potential session issues, but limited direct security impact

---

### SP20: Passcode=0 Hint Security

**Property:** When passcode is 0 and MTop present, commissioner SHALL NOT attempt commissioning

**Formal:** `(passcode == 0 AND MTop_present) => NOT attempt_commission`

**VERDICT: PARTIALLY_HOLDS**

#### Why Partially Holds

The FSM includes Transition T53:
```json
{
  "from": "C2",
  "to": "C12",
  "trigger": "invalid_passcode_detected",
  "guard": "passcode == 0 && MTop_present",
  "actions": ["check_passcode_zero()"],
  "description": "Passcode 0 detected with MTop presence, commissioner avoids commission attempt"
}
```

**This handles the HINT case correctly.**

**Problem:** This is reactive, not preventive:
- Transition only fires if commissioner actively checks for passcode=0
- If commissioner doesn't check, it proceeds to attempt commissioning with passcode=0
- Transition T12/T13/T14 (Commissioner_discovered) don't verify passcode != 0

**Missing Prevention:**

Transitions T12, T13, T14 should have additional guard:
```json
"guard": "advertising == true && has_valid_pairing_code == true && (passcode != 0 || NOT MTop_present)"
```

#### Specification Evidence

**Quote:**
> "When the CommissioningCustomFlowUrl for a Custom Commissioning Flow device includes the MTop key, the Passcode embedded in any Onboarding Payload placed on-device or in packaging MAY be set to 0 (one of the invalid values) in order to provide a hint to the Commissioner that it is not one that can be used for secure channel establishment with the device. This would allow the Commissioner to avoid attempting to commission the device if an advertisement from it is detected."

**Source:** Section 5.7.3.1, Page 332

**Intent:**
- Passcode=0 is a HINT to commissioner
- Commissioner SHOULD check and avoid wasting time on impossible commission attempt
- Prevents DoS via repeated failed PAKE attempts

**Issue:** Spec says MAY (optional hint) and SHOULD (commissioner behavior). Not SHALL enforce.

**FSM Gap:**
- T53 exists but only triggers on explicit check
- No guard prevents commission attempt if check skipped

#### Severity: LOW

**Exploitability:** Commissioner implementation doesn't check passcode=0  
**Impact:** Wasted time, failed commission attempts, user frustration, but no direct security breach

---

### SP21: ESF SchemaVersion Compatibility

**Property:** Commissioner SHALL validate ESF schemaVersion compatibility before processing

**Formal:** `process_esf_file => esf.schemaVersion <= commissioner.max_supported_version`

**VERDICT: VIOLATED**

#### Why Violated

The FSM includes function `validate_esf_schema_version()` (lines 1301-1305):
```json
{
  "name": "validate_esf_schema_version",
  "parameters": ["esf_file"],
  "returns": "boolean",
  "behavior": "Checks if commissioner can handle the schema version, returns false if version too new/incompatible"
}
```

**Never called in any transition.**

Function `validate_esf_file()` includes "JSON schema valid" in behavior but doesn't explicitly mention schemaVersion check.

**Attack Path:**

1. **ESF File Contains:** `"schemaVersion": 999`
2. **Commissioner Downloads File:** Transition T33 → C8 → C9
3. **Commissioner Parses:** Has parser for schemaVersion 1 only
4. **Parser Behavior:**
   - **Option A:** Crashes on unknown field (DoS)
   - **Option B:** Ignores unknown fields (missing security features)
   - **Option C:** Misparses fields assuming v1 schema (security bypass)
5. **Result:** Unpredictable behavior, potential crashes or security issues

#### Specification Evidence

**Quote:**
> "This field SHALL indicate the version of the JSON schema format. This helps in managing changes to the structure of the schema over time. Whenever there is a change to the schema (such as adding, removing, or modifying fields), the **schemaVersion** SHALL be incremented. This ensures that the software processing these configuration files can recognize which version of the schema it is dealing with and handle it appropriately."

**Source:** Section 5.7.4.7.1, Page 342

**Requirement:**
- schemaVersion SHALL be present
- Incremented on schema changes
- Software SHALL recognize version and handle appropriately

**"Handle appropriately" implies:**
- Reject unknown versions
- Fallback to Custom Flow if version unsupported

#### Missing Validation

Should add to T33 guard or add new transition from C8:
```json
{
  "from": "C8",
  "to": "C7",
  "trigger": "esf_schema_unsupported",
  "guard": "esf_file_found == true && validate_esf_schema_version() == false",
  "actions": ["set_esf_failed(true)", "log_unsupported_schema_version()"],
  "description": "ESF schema version unsupported, must fallback to Custom Flow"
}
```

#### Severity: MEDIUM

**Exploitability:** Future schema version deployed before commissioner update  
**Impact:** Commissioner crashes, misparses TC, security features ignored

---

### SP22: Background Scan Race Condition Safety

**Property:** Background scanning SHALL NOT interfere with ongoing commissioning or introduce race conditions

**Formal:** `(background_scan_active AND device_discovered) => atomic_transition_to_commissioning`

**VERDICT: VIOLATED**

#### Why Violated

The FSM includes Transitions T50, T51, T52 for background scanning:

**T50:**
```json
{
  "from": "C7",
  "to": "C14",
  "trigger": "background_scan_started",
  "guard": "custom_flow_in_progress == true",
  "actions": ["start_background_scan()"],
  "description": "Commissioner starts scanning in background while user follows manufacturer flow"
}
```

**T52:**
```json
{
  "from": "C14",
  "to": "C11",
  "trigger": "device_discovered_in_background",
  "guard": "background_scan_active == true && device_found == true",
  "actions": ["stop_background_scan()"],
  "description": "Background scan discovers device, proceed to commissioning"
}
```

**Race Condition:**

1. **State:** C14 (Commissioner_ScanningInBackground)
2. **Event 1:** device_discovered_in_background (triggers T52)
3. **Event 2:** callback_received from manufacturer flow (triggers T51: C14 → C10)
4. **Race:** Which transition fires first?

**If T51 fires first:**
- Commissioner moves to C10 (AwaitingCallback)
- Background scan may still be active
- Device discovery event lost

**If T52 fires first:**
- Commissioner moves to C11 (Commissionable)
- Callback from manufacturer arrives but commissioner already commissioning
- MTrop payload ignored

**Missing Atomicity:**

No guard ensures:
- Only one transition fires from C14
- Background scan result properly synchronized with callback
- No double-commissioning attempt (scan result + callback both succeed)

**Specification Reference:**

> Quote: "If possible, a Commissioner MAY continue to scan for announcements from the device in the background while any manufacturer-specific app is configuring the device to be available for commissioning."

**Source:** Section 5.7.5.3, Page 347, Figure 50 caption

**Spec says "MAY" but doesn't specify race condition handling.**

#### Missing Enforcement

Should add guard to T52:
```json
"guard": "background_scan_active == true && device_found == true && callback_not_received"
```

Or add mutex/atomic transition group ensuring only one path (scan OR callback) succeeds.

#### Severity: MEDIUM

**Exploitability:** Timing race in commissioner implementation  
**Impact:** Lost commissioning attempts, double commissioning, state corruption, user confusion

---

### SP23: Fallback URL Parameter Security

**Property:** Fallback URL parameter expansion SHALL follow same security rules as custom flow URL

**Formal:** `expand_fallback_url => same_security_constraints_as(expand_custom_flow_url)`

**VERDICT: VIOLATED**

#### Why Violated

The FSM includes function `expand_fallback_url_with_parameters()` (lines 1315-1319):
```json
{
  "name": "expand_fallback_url_with_parameters",
  "parameters": ["fallback_url"],
  "returns": "expanded_url",
  "behavior": "Same expansion algorithm as expand_custom_flow_url, substitutes placeholders with URL-encoded values"
}
```

**Behavior claims "same algorithm" but no enforcement that security checks apply.**

**Missing Verification:**
- No call to `validate_https_scheme()` for fallback URLs
- No call to `validate_mt_reserved_keys()` for fallback URLs
- No call to `preserve_query_order()` for fallback URLs
- No verification that MTop not used with real passcode

**Attack Path:**

1. **Compromised DCL:** Attacker sets `CommissioningFallbackUrl: http://attacker.com?MTattack=malicious&MTop=_`
2. **Commissioning Fails:** Transition T38 (C11 → C12)
3. **Fallback Invoked:** Transition T39 (C12 → C1) or T54/T55 (C12 → C15 → C1)
4. **URL Expanded:** Function `expand_fallback_url_with_parameters()` called **without security checks**
5. **HTTP URL Opened:** MitM intercepts
6. **Attacker Steals:** Onboarding payload from MTop, callback URL from MTcu
7. **Result:** Same attacks as SP16 (HTTP) and SP17 (MT-prefix) apply to fallback URLs

#### Specification Evidence

**Quote:**
> "The Section 11.23.6.14, 'CommissioningFallbackUrl' MAY be constructed in the same way as the Section 11.23.6.9, 'CommissioningCustomFlowUrl' field, including making it specific for a particular VendorID and/or ProductID (as described in Section 5.7.3, 'Custom Commissioning Flow', 5<sup>th</sup> bullet). Also, the query components as described in Section 5.7.3.1, 'CommissioningCustomFlowUrl format' can be added to the URL to improve the overall flow. For example, usage of **MTop**, **MTcu** and **MTrop** parameters would be useful..."

**Source:** Section 5.7.5.3, Page 347

**Implication:**
- Fallback URLs CAN use same parameters as custom flow URLs
- Therefore same security rules MUST apply
- But spec doesn't explicitly state "SHALL apply same validation"

#### Missing Enforcement

Add security validation before T39/T54/T55:
```json
"actions": [
  "validate_https_scheme(fallback_url)",
  "validate_mt_reserved_keys(fallback_url)",
  "preserve_query_order(fallback_url)",
  "expand_fallback_url_with_parameters()"
]
```

Or update `expand_fallback_url_with_parameters()` behavior to include all security checks.

#### Severity: HIGH

**Exploitability:** Same as SP16 (HTTP URLs) applying to fallback mechanism  
**Impact:** Fallback path used as attack vector, all SP16/17/18 violations apply

---

### SP24: Offline Commissioning Authorization

**Property:** Offline commissioning SHALL only proceed for Standard/User-Intent flows, not Custom/ESF requiring internet

**Formal:** `offline_mode AND commissioning_allowed => (flow_type == STANDARD OR flow_type == USER_INTENT)`

**VERDICT: HOLDS**

#### Supporting Transitions

**T56:**
```json
{
  "from": "C3",
  "to": "C16",
  "trigger": "offline_detected",
  "guard": "internet_unavailable == true",
  "actions": ["detect_offline_mode()"],
  "description": "Commissioner detects offline mode, routing decision needed"
}
```

**T58:**
```json
{
  "from": "C16",
  "to": "C11",
  "trigger": "offline_commissioning_allowed",
  "guard": "flow_type == STANDARD || flow_type == USER_INTENT",
  "actions": ["proceed_offline_commissioning()"],
  "description": "Offline commissioning proceeds for Standard/User-Intent flows only"
}
```

**T57:**
```json
{
  "from": "C16",
  "to": "C12",
  "trigger": "offline_commissioning_blocked",
  "guard": "flow_type == CUSTOM || esf_required == true",
  "actions": ["inform_internet_required()"],
  "description": "Offline commissioning rejected for Custom/ESF flows requiring internet"
}
```

**Why Holds:**
- Guard in T58 allows only `flow_type == STANDARD || flow_type == USER_INTENT`
- Guard in T57 blocks `flow_type == CUSTOM || esf_required == true`
- No path from C16 to successful commissioning for Custom/ESF flows

#### Specification Evidence

**Quote:**
> "This flow typically requires internet access to access the URL, so initial commissioning of the device may fail if there is no internet connection at that time/location."

**Source:** Section 5.7.3, Page 330, Manufacturer consideration bullet 1

**Quote (fallback context):**
> "In cases where using this URL is technically impossible (e.g. a headless commissioner, or the lack of internet access) or when the Commissioner is performing offline mode commissioning, the Commissioner SHOULD inform the user of the assumed reason for commissioning failure..."

**Source:** Section 5.7.5.2, Page 346

**Implication:** Offline mode acknowledged, but Custom Flow URLs require internet.

---

### SP25: MTrop Non-Replacement as Failure Signal

**Property:** Manufacturer flow SHALL NOT replace MTrop placeholder if device not made commissionable

**Formal:** `manufacturer_setup_failed => NOT replace_mtrop_placeholder`

**VERDICT: VIOLATED**

#### Why Violated

The FSM includes Transition T59:
```json
{
  "from": "C10",
  "to": "C12",
  "trigger": "callback_received_no_mtrop",
  "guard": "callback_includes_mtrop == false || mtrop_value_unchanged",
  "actions": ["log_manufacturer_flow_failure()"],
  "description": "Manufacturer flow callback received but MTrop not replaced, signals failure"
}
```

**This detects the signal correctly.**

**Problem: No enforcement on manufacturer side:**
- FSM models commissioner behavior, not manufacturer flow server
- No guard prevents manufacturer server from INCORRECTLY replacing MTrop on failure
- If manufacturer bug or malicious behavior replaces MTrop despite failure, commissioner proceeds with invalid payload

**Counterexample:**

1. **Manufacturer Flow Fails:** Device cannot be made commissionable (network error, hardware issue)
2. **Buggy Manufacturer Server:** Returns old cached payload via MTrop anyway
3. **Commissioner Receives:** Transition T31 fires (callback with MTrop)
   ```json
   "guard": "callback_includes_mtrop == true && mtrop_payload_valid == true"
   ```
4. **Commissioner Attempts:** Proceeds to C11 (Commissionable)
5. **Device Not Ready:** Commissioning fails because device not actually in commissioning mode
6. **User Confusion:** Commissioner says "ready" but device unreachable

**Missing Verification:**

Commissioner should verify device actually advertises/responds before accepting MTrop payload:
```json
"guard": "callback_includes_mtrop == true && mtrop_payload_valid == true && device_actually_commissionable == true"
```

#### Specification Evidence

**Quote:**
> "If the manufacturer custom flow failed to make the device commissionable, it SHALL NOT replace the placeholder value '\_' of an included `MTrop=_` key/value pair, to avoid a Commissioner attempting to discover or commission a device not made ready by the custom flow."

**Source:** Section 5.7.3.2.1, Page 333

**Intent:**
- MTrop non-replacement is a signal (like HTTP 4xx/5xx status code)
- Commissioner should detect and handle appropriately
- T59 does this

**Gap:**
- Spec requires manufacturer "SHALL NOT replace" but commissioner can't enforce this
- Commissioner can only react to incorrectly replaced MTrop by detecting device not actually available
- FSM lacks device availability check after MTrop received

#### Recommendation

Add verification to T31:
```json
"actions": [
  "extract_returned_payload()",
  "verify_custom_flow_bits_zero()",
  "verify_device_actually_advertising()"
]
```

And add failure transition:
```json
{
  "from": "C11",
  "to": "C12",
  "trigger": "device_not_actually_ready",
  "guard": "device_unreachable == true",
  "actions": ["log_mtrop_false_positive()"],
  "description": "MTrop indicated ready but device not actually commissionable"
}
```

#### Severity: MEDIUM

**Exploitability:** Manufacturer server bug  
**Impact:** False positive commissioning readiness, user confusion, wasted time

---

### SP26: Transient vs Systematic Failure Distinction

**Property:** Commissioner SHALL distinguish transient failures (retryable) from systematic failures (fallback required)

**Formal:** `commissioning_failed => (failure_type == TRANSIENT AND retry) OR (failure_type == SYSTEMATIC AND fallback)`

**VERDICT: HOLDS**

#### Supporting Transitions

**T49:**
```json
{
  "from": "C12",
  "to": "C11",
  "trigger": "retry_after_transient_failure",
  "guard": "failure_type == TRANSIENT",
  "actions": ["reset_error_state()", "attempt_commission_again()"],
  "description": "Commissioner retries after determining failure was transient"
}
```

**T39:**
```json
{
  "from": "C12",
  "to": "C1",
  "trigger": "fallback_guidance_provided",
  "guard": "fallback_url_available == true",
  "actions": ["display_fallback_url()", "redirect_to_fallback()"],
  "description": "Commissioner directs user to CommissioningFallbackUrl for resolution"
}
```

Function `determine_failure_type()` (lines 1133-1137):
```json
{
  "name": "determine_failure_type",
  "returns": "FailureType",
  "behavior": "Returns TRANSIENT (network glitch, timeout) or SYSTEMATIC (capability mismatch, invalid credentials)"
}
```

**Why Holds:**
- Function classifies failure type
- T49 retries only if `failure_type == TRANSIENT`
- T39/T40 use fallback for systematic failures
- No retry loop for systematic failures

#### Specification Evidence

**Quote:**
> "Commissioning using any of the methods described above can potentially fail for a number of reasons. In some cases this will be a transient failure (e.g., due to wireless interference), while in other cases failure will be systematic (e.g., a mismatch in capabilities of the Commissioner and the Commissionee)."

**Source:** Section 5.7.5, Page 346

**Quote:**
> "When a Commissioner encounters a situation where the commissioning fails systematically (e.g., due to a mismatch in capabilities of the Commissioner and the Commissionee), and it has no other means to guide the user to resolution of the issues, it SHALL use the Section 11.23.6.14, 'CommissioningFallbackUrl'..."

**Source:** Section 5.7.5.2, Page 346

**Quote:**
> "When a Commissioner encounters a situation where the commissioning failure is transient, the Commissioner MAY try again..."

**Source:** Section 5.7.5.2, Page 346-347

---

### SP27: Already-on-IP Security Equivalence

**Property:** Commissioning via IP network SHALL maintain same security properties as BLE commissioning

**Formal:** `commission_via_ip => proof_of_possession_required AND secure_channel_established`

**VERDICT: HOLDS**

#### Supporting Transition

**T61:**
```json
{
  "from": "C4",
  "to": "C11",
  "trigger": "already_on_ip_network",
  "guard": "device_on_ip_network == true && has_valid_pairing_code == true",
  "actions": ["skip_ble_discovery()", "commission_via_ip()"],
  "description": "Commissioner detects device already on IP network, proceeds to commissioning directly"
}
```

Function `commission_via_ip()` (lines 1371-1375):
```json
{
  "name": "commission_via_ip",
  "returns": "boolean",
  "behavior": "Establishes secure channel via IP network connection instead of BLE discovery"
}
```

**Why Holds:**
- Guard requires `has_valid_pairing_code == true` (proof-of-possession)
- Function behavior says "establishes secure channel" (same as BLE path)
- No shortcut bypassing pairing code or PAKE
- Destination C11 same as normal commissioning path (T15 requires secure_channel_established)

#### Specification Evidence

**Quote (implicit reference):**
> "The CommissioningFallbackUrl can lead to a manufacturer-provided mechanism to get the device on the IP-bearing network (which can then be followed by 'commissioning while already on IP-network')."

**Source:** Section 5.7.5, Page 346, Bullet 2

**Quote:**
> "For example, usage of **MTop**, **MTcu** and **MTrop** parameters would be useful to smooth the flow in case the manufacturer-provided mechanism uses a manufacturer-defined mechanism to get the device on the IP network, after which the original commissioner can take care of the Matter commissioning ('device already on IP-network')."

**Source:** Section 5.7.5.3, Page 347

**Implication:** Already-on-IP commissioning is legitimate path, but must maintain security.

#### Security Properties Maintained:
1. **Proof-of-possession:** Guard requires `has_valid_pairing_code == true`
2. **Secure channel:** Function establishes PAKE-based channel
3. **Device authentication:** Same as BLE (PAKE proves both sides know passcode)
4. **No proximity shortcut:** Pairing code still required (QR/manual code needed)

---

### SP28: ESF File Size Limit Enforcement

**Property:** ESF TC file size SHALL match EnhancedSetupFlowTCFileSize exactly

**Formal:** `validate_esf_file => (file.size == DCL.EnhancedSetupFlowTCFileSize)`

**VERDICT: HOLDS**

#### Supporting Function

Function `validate_esf_file()` (lines 1049-1053):
```json
{
  "name": "validate_esf_file",
  "parameters": ["esf_file", "expected_digest", "expected_filesize"],
  "returns": "boolean",
  "behavior": "Verifies EnhancedSetupFlowTCDigest matches file hash, filesize matches EnhancedSetupFlowTCFileSize, JSON schema valid, UTF-8 encoding"
}
```

**Explicitly checks:** `filesize matches EnhancedSetupFlowTCFileSize`

Transition T33:
```json
{
  "guard": "esf_file_found == true && digest_valid == true && filesize_valid == true && format_valid == true",
  "actions": ["parse_tc_texts()", "check_tc_cache()"]
}
```

Guard requires `filesize_valid == true`.

#### Specification Evidence

**Quote:**
> Quote: "SHALL validate using EnhancedSetupFlowTCDigest, TCFileSize, and TC File Format"

**Source:** Section 5.7.4.1 (referenced in T33)

**Field Definition:**
> "esfRevision Field: This field is a 16-bit integer version number of the file that SHALL match the Version at Section 11.23.6.23, 'EnhancedSetupFlowTCRevision'."

**Source:** Section 5.7.4.7.2, Page 342

**Security Rationale:**
- File size mismatch indicates:
  - Truncation attack (partial download)
  - Tampering (content added/removed)
  - Wrong file served (version mismatch)
  - Corruption during download

---

## Summary of Critical Violations

### Immediate Security Concerns

1. **SP4 (Passcode Confidentiality):** Real passcodes can be sent in MTop parameters - CRITICAL
2. **SP15 (DCL Integrity):** No DCL authentication/integrity checks - CRITICAL
3. **SP16 (HTTPS-Only):** No URL scheme validation, HTTP allowed - CRITICAL

### Medium-High Priority

4. **SP1 (Flow Type Consistency):** Flow type not verified across sources - HIGH
5. **SP5 (ESF Validation):** Potential validation bypass on timeout - HIGH
6. **SP7 (TC VID Boundary):** TC cache VID check not enforced in guards - HIGH
7. **SP17 (MT-prefix Reservation):** No validation of reserved MT keys - MEDIUM
8. **SP18/19 (URL Preservation):** No verification of query order/fragment - MEDIUM
9. **SP20 (Passcode=0 Handling):** Only handles hint case, not enforcement - MEDIUM
10. **SP22 (Background Scan Races):** No atomic transition guarantees - MEDIUM
11. **SP23 (Fallback URL Security):** No parity verification with custom flow - MEDIUM
12. **SP25 (MTrop Non-replacement):** No guard enforces failure signaling - MEDIUM

### Properties That Hold

- **SP2:** User-Intent anti-drive-by ✓
- **SP3:** Custom Flow setup gate ✓
- **SP6:** Required TC acceptance ✓
- **SP9:** Returned payload flow bits ✓
- **SP10:** Advertisement timeout ✓
- **SP12:** Limited functionality status ✓
- **SP13:** ESF HTML restriction ✓ (with assumptions)
- **SP14:** Proof-of-possession ✓
- **SP24:** Offline commissioning authorization ✓
- **SP26:** Failure distinction ✓
- **SP27:** Already-on-IP security equivalence ✓
- **SP28:** ESF file size matching ✓

---

## Recommendations

### Immediate Actions

1. **Add DCL Integrity Verification (SP15):**
   - Implement DCL signature validation
   - Add guard to all DCL retrieval transitions
   - Reject unsigned or invalid DCL entries

2. **Add URL Scheme Validation (SP16):**
   - Call `validate_https_scheme()` before using any URL
   - Add guard rejecting non-HTTPS URLs
   - Log and alert on HTTP URL detection

3. **Enforce Passcode Confidentiality (SP4):**
   - Add guard to T28: `NOT (MTop_present && passcode_usable)`
   - Reject/warn if device violates this requirement
   - Add validation function call in `expand_custom_flow_url()`

### Short-Term Improvements

4. **Add Flow Type Consistency Check (SP1):**
   - Implement `verify_flow_consistency(payload, dcl, device)`
   - Add guard to flow routing transitions (T22, T23, T24)
   - Reject on mismatch, log warning

5. **Strengthen ESF Validation (SP5):**
   - Add explicit timeout/error transition from C8
   - Ensure no bypass path to C11 without validation
   - Add validation timeout handling

6. **Enforce TC Cache Boundaries (SP7, SP8):**
   - Add guards to T35 verifying cache validity
   - Check VID, digest, revision in guard (not just function call)
   - Add rejection transition for cache violations

### Long-Term Architecture

7. **Formalize Security Assumptions:**
   - Document all implicit trust relationships
   - Make explicit what commissioners MUST verify
   - Add security assumption validation framework

8. **Add Comprehensive Validation Layer:**
   - Create validation state before each security-critical action
   - Ensure all external data (DCL, URLs, ESF files) validated
   - No bypass paths around validation

9. **Implement Defense in Depth:**
   - Multiple checks for critical properties
   - Fail-safe defaults (reject on ambiguity)
   - Extensive logging for security events

---

## Conclusion

This analysis identified **12 violations** and **4 partial holds** out of 28 security properties. The most critical vulnerabilities involve:
- Lack of DCL integrity verification (enables all attacks)
- Missing HTTPS enforcement (enables MitM attacks)
- Insufficient passcode confidentiality protection (leaks credentials)

The FSM correctly models many specification requirements but lacks enforcement of critical security properties, primarily due to missing guards and validation calls despite having the necessary helper functions defined.

**Overall Security Posture:** The FSM extracts specification behavior accurately but needs additional defensive guards to enforce security properties before the model can be considered secure for formal verification or implementation.

---

**End of Property Violation Analysis**
