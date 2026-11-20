# Current rebuild security triage — 20 November 2026

## Scope

This record concerns only local image `git-publish-app:latest`, image ID
`sha256:e0db8cd02d2cf20ed92887f99c8d8678be58e9678a8afef1574a018d373bfe16`.
It is not a hosted-deployment assessment or a risk acceptance.

The retained offline Trivy scan, `current_rebuild_scan.json`, reports **3
critical** and **65 high** findings (68 high-or-critical total). Five reports
have a scanner-listed fixed version; 63 do not.

## Scanner layers versus running runtime

The scan reports old Python installation layers for `setuptools`, `urllib3`,
and `msgpack`. Direct inspection of the running service shows:

| Package | Scan finding | Running version | Disposition |
| --- | --- | --- | --- |
| setuptools | CVE-2025-47273, scan layer 70.3.0, fixed 78.1.1 | 84.2.1 | Not a live installed version; retain scan history, but do not count as a runtime exposure. |
| urllib3 | two scan-layer high findings, version 2.7.0 | not installed | Not a runtime dependency. |
| msgpack | two scan-layer high findings, version 1.1.2 | not installed | Not a runtime dependency. |

This is scanner-layer triage only. It does not make the image security-cleared.

## Critical findings: live runtime exposure

| CVE | Package / running version | Fixed version in scan | Runtime exposure | Disposition |
| --- | --- | --- | --- | --- |
| CVE-2026-58016 | libglib2.0-0 2.74.6-2+deb12u9 | none | Image and DICOM parsing paths use Pillow and pydicom on untrusted uploads. | **UNRESOLVED_RELEASE_BLOCKER**; select a maintained base with a vendor fix or obtain vendor remediation evidence. |
| CVE-2025-7458 | libsqlite3-0 3.40.1-2+deb12u2 | none | Default production configuration stores application data in SQLite. | **UNRESOLVED_RELEASE_BLOCKER**; no version-only remediation is available from this scan. |
| CVE-2023-45853 | zlib1g 1:1.2.13.dfsg-1 | none | ZIP intake/export and image processing use compression through Python and native libraries. | **UNRESOLVED_RELEASE_BLOCKER**; do not rely on input bounds alone as a complete mitigation. |

## Required next action

Build and scan a specifically selected maintained runtime base, compare both
vulnerability sets, then repeat startup, authentication, upload and export
regressions. Do not publish, deploy, or risk-accept this image while any
critical finding remains unresolved.
