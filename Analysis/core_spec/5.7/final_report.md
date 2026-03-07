# Final Report – Section 5.7 Security Gaps and Implementation Findings

This document merges the specification‑level gaps identified during the analysis of
property violations with the concrete results obtained from the comprehensive
implementation testing report.  Only the violations or gaps themselves are
recorded; details include the spec reference, impact, and whether the gap is
exploitable in the current SDK.

---

## SP4 – Passcode Confidentiality in Custom Flow URLs

- **Spec reference:** Section 5.7.3.1, p. 331.
- **Specification gap:** The text requires that when a CommissioningCustomFlowUrl
  contains an `MTop` key the passcode embedded in any onboarding payload
  SHALL NOT be usable.  No normative requirement or mechanism is provided for
  commissioners to verify this.  A MAY hint to set `passcode=0` is insufficient
  to satisfy the SHALL, permitting non‑compliant devices to leak credentials.
- **Impact:** A malicious manufacturer or compromised DCL can harvest user
  passcodes via the `MTop` parameter, defeating proof‑of‑possession and
  enabling device takeover.  Severity: **High.**
- **Implementation status:** The SDK code implements `IsValidSetupPIN()` and
  `SetupPayload::isValidQRCodePayload()` with no awareness of the commissioning
  flow; it accepts a usable passcode even when an `MTop`‑style URL is present.
  The comprehensive testing report demonstrated the vulnerability by
  exfiltrating a valid passcode (`20202021`).  No protection exists in the
  implementation because the spec fails to require it.  ➤ **Vulnerable.**

---

## SP7 – Terms & Conditions VID Boundary

- **Spec reference:** Section 5.7.4.2 introduction, p. 339.
- **Specification gap:** The prohibition on re‑using cached acknowledgements
  across different Vendor IDs is expressed only in prose; neither the
  `SetTCAcknowledgements` command nor the `TermsAndConditions` structure
  includes a VendorID field.  Implementations therefore have no means to
  perform the required check.
- **Impact:** Consent recorded for one vendor may be applied to another, allowing
  privacy‑invasive policies to take effect without user awareness.  Severity:
  **Medium.**
- **Implementation status:** The SDK’s `TermsAndConditions` struct omits a
  VendorID and the command handler stores values accordingly; tests showed a
  cross‑vendor consent bypass.  The issue is in the spec, not an SDK coding
  error, thus the implementation faithfully reproduces the gap.  ➤ **Vulnerable.**

---

## SP16 – HTTPS‑Only URL Scheme (Ambiguity)

- **Spec reference:** Section 5.7.3.3 examples.
- **Specification gap:** While the example URLs are marked invalid when using
  `http://`, the normative text never contains a SHALL to mandate an HTTPS
  scheme.  This ambiguity could lead to inconsistent interpretations by
  implementers.
- **Impact:** In theory, a commissioner might admit HTTP URLs if it believes the
  example is non‑normative; such a device could expose unencrypted data.  The
  note in the defense summary states that the SDK already enforces HTTPS.
- **Implementation status:** `HTTPSRequest.cpp` contains a hard check requiring
  the `https://` prefix, and the comprehensive tests confirmed that HTTP URLs
  are rejected.  No exploit was found in the code itself; the only problem lies
  in the lack of explicit normative language.  ➤ **Protected in implementation;
  spec ambiguity remains.**

---

*End of final report.*
