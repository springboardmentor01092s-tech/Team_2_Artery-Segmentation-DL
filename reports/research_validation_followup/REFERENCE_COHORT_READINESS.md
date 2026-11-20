# Reference cohort readiness

Rechecked 11 November 2026 after reconnection: the previously recorded external pilot path is accessible:

`/Volumes/One Touch/execution_readiness_20261030/corovision_severity_reference_pilot_20261110`

All 43 listed package files passed SHA-256 verification on reconnection. The worksheet contains 20 rows and zero completed MLD/RVD pairs. Independently measured references remain zero. Calibration remains unverified, and the cohort is unlocked.

Next executable steps:

1. Keep the verified external volume available for annotation; preserve the original images and manifest.
2. A blinded reviewer completes the source-pixel MLD/RVD worksheet, original locations, method and exclusions.
3. Validate the completed rows and image hashes before freezing a new cohort version.
4. Resolve checkpoint exposure before claiming external-test independence.
5. Obtain the guide's actual protocol decision using `GRADING_PROTOCOL_APPROVAL_REQUEST.md`.

The existing automatic code computes ordered mask-width profiles using a distance transform. It does not establish candidate-local lumen boundaries or select an RVD reference segment. Automatic MLD/RVD accuracy and severity agreement therefore remain unavailable.
