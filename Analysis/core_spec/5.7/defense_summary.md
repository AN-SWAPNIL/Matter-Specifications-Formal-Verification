# Defense Summary - Matter Core Specification Section 5.7

This document now lists only the specification gaps identified during analysis
of the claimed violations in PROPERTY_VIOLATION_ANALYSIS.md.

---

## Specification Gaps

### SP4: Passcode Confidentiality in Custom Flow URLs

- **Spec reference:** Section5.7.3.1, p.331.
- **Issue:** Devices are required to avoid using a usable passcode when the
  Custom Flow URL includes MTop, yet commissioners are given no requirement
  or means to verify this.  The optional hint (MAY set passcode=0) does not
  satisfy the normative SHALL and allows noncompliant devices to leak
  credentials.

- **Impact:** A malicious manufacturer (or compromised DCL) can collect user
  passcodes via the MTop parameter, breaking proofofpossession and enabling
  device takeover.

- **Severity:** High.


### SP7: TermsandConditions VID Boundary

- **Spec reference:** Section5.7.4.2 introduction, p.339.
- **Issue:** The prohibition on reusing cached acknowledgements across different
  Vendor IDs is described in prose but not enforced by any command parameter or
  data structure.  The SetTCAcknowledgements command and the SDKs
  TermsAndConditions struct lack a VendorID field, so implementations cannot
  perform the required check.

- **Impact:** Consent given to one vendors terms may be inadvertently applied to
  another vendors device, allowing privacyinvasive policies to take effect
  without user awareness.

- **Severity:** Medium.


### SP16: HTTPSOnly URL Scheme (Ambiguity)

- **Spec reference:** Section5.7.3.3 examples.
- **Issue:** Although examples label http:// URLs as invalid, the text never
  explicitly mandates an HTTPS scheme with a SHALL.  This leaves room for
  inconsistent interpretation by implementers.

- **Note:** The implementation already enforces HTTPS, so this is an
  ambiguity rather than an exploited gap, but the specification should be
  clarified for completeness.

---

*End of gaps-only summary.*
