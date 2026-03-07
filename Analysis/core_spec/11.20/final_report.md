# Final Report — Section 11.20 OTA Software Update (Matter v1.5)

Date: 2026

Executive summary
- Two of the three reported specification gaps are confirmed as implementation vulnerabilities in the SDK: PROP_002 (Cached Image Downgrade) and PROP_003 (Cached Image Integrity Re-verification). PROP_001 (Query rate limiting bypass via urgent announcements) is a design trade-off and is valid by design.

Findings

- PROP_002 — Cached Image Downgrade Attack (CRITICAL)
	- Verdict: CONFIRMED in implementation.
	- Evidence: SDK performs version comparison only at Query/Download time (see DefaultOTARequestor.cpp), but no version comparison is performed in `ApplyUpdate()` before calling the image processor. The requestor's driver calls `mImageProcessor->Apply()` without an apply-time version check. See detailed traces in [11.20/COMPREHENSIVE_TESTING_REPORT.md](11.20/COMPREHENSIVE_TESTING_REPORT.md).
	- Impact: Remote or local downgrade of a device from a newer running version to an older cached image, reintroducing patched vulnerabilities.

- PROP_003 — Cached Image Integrity Re-verification Gap (HIGH)
	- Verdict: CONFIRMED in implementation.
	- Evidence: `OTAImageProcessorInterface` exposes `Apply()` but lacks a mandatory re-verification API (e.g., `VerifyIntegrityBeforeApply()`), so cached images are applied without re-checking signature/integrity at apply time. See interface notes in [11.20/COMPREHENSIVE_TESTING_REPORT.md](11.20/COMPREHENSIVE_TESTING_REPORT.md).
	- Impact: TOCTOU and storage-tampering attacks can result in execution of modified firmware.

- PROP_001 — Query Rate Limiting Bypass (LOW-MEDIUM)
	- Verdict: VALID BY DESIGN.
	- Rationale: The specification intentionally allows urgent announcements to reduce jitter (1s) for critical updates. The defense analysis documents the design trade-off and ACL-based mitigations; no implementation bug was found. See [11.20/defense_summary.md](11.20/defense_summary.md).

Implementation test highlights

- Unit tests created: 13 tests in `TestSection11_20_OTASecurity.cpp` covering version-check flows, cached-image application, interface coverage, and rate-limit behavior.
- Attack simulations run: Downgrade and TOCTOU simulations reproduced the issues (downgrade v100→v95; modified cached image applied). See attack logs and payloads in `attack_simulation_ota.py` and `attack_payloads/` (detailed in the comprehensive testing report).

Recommended fixes (short)

- Specification: Require an explicit apply-time version check and require re-verification of cached image integrity before apply. Example spec language additions were proposed in the testing report and defense summary.
- SDK: Add an apply-time version comparison in `DefaultOTARequestor::ApplyUpdate()` and extend `OTAImageProcessorInterface` with `VerifyIntegrityBeforeApply()` and `GetCachedImageVersion()` so `ApplyUpdate()` can enforce both version monotonicity and integrity re-check.

Summary table

| Property | Verdict | Severity | Location (implementation) |
|---|---:|---:|---|
| PROP_002 | CONFIRMED | CRITICAL | `src/app/clusters/ota-requestor/DefaultOTARequestor.cpp` (ApplyUpdate path) |
| PROP_003 | CONFIRMED | HIGH | `src/include/platform/OTAImageProcessor.h` (interface missing re-verify) |
| PROP_001 | VALID BY DESIGN | LOW-MEDIUM | `src/app/clusters/ota-requestor/DefaultOTARequestorDriver.cpp` (announcement timing constants) |

Appendix / References

- Comprehensive test details and full logs: [11.20/COMPREHENSIVE_TESTING_REPORT.md](11.20/COMPREHENSIVE_TESTING_REPORT.md)
- Specification defense analysis: [11.20/defense_summary.md](11.20/defense_summary.md)

