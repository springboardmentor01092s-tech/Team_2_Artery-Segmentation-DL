# 2D implementation audit — 14 November 2026

The full backend command `.venv/bin/python -m pytest -q --disable-warnings --maxfail=3` passed 298 tests and skipped five opt-in integration tests in 69.05 seconds. Three warnings were recorded. The installed-checkpoint, public image and real task-model tests require explicit fixture/environment configuration. Their skipped results supply no new inference evidence.

After the export changes, `.venv/bin/python -m pytest -q tests/test_review_reporting.py tests/test_automatic_measurement_pipeline.py tests/test_narrowing.py tests/test_severity_reference.py tests/test_reference_collection.py` passed 36 tests with one test-client deprecation warning. `npm run build` passed, with Vite's large-chunk warning.

## Current behavior

The previously skipped installed-checkpoint workflow was then executed explicitly with `CV_TEST_REAL_TRAINED_RELEASE=1 .venv/bin/python -m pytest -q tests/test_trained_release.py::test_real_case_upload_analysis_and_access_control`. It passed in 6.85 seconds with five dependency deprecation warnings. This verifies actual preserved-checkpoint upload, inference and resource access behavior on the test's synthetic image. It supplies no new medical accuracy metric.

The existing upload, preprocessing, inverse geometry, frozen segmentation, detector candidates, centerline profiles, manual reference collection, reviewed measurements, experiment registry and report routes are preserved. Candidate measurements remain bound to case/image/run/candidate identities.

Historical automatic assessments now return newest first. Exploratory Gharshitha percentile/ring estimates require a recorded researcher-authorized protocol and explicitly carry the failed cross-section assessment, exploratory quality status, unquantified uncertainty and exclusion from reference validation. The PDF includes those fields.

The 2D ZIP now includes available saved original/processed images, artery mask, centerline and overlay together with candidate JSON, measurement JSON, provenance, JSON/CSV/PDF reports and a checksum manifest. The report integration test verifies member identity and checksums.

## Remaining acceptance dependencies

- Checkpoint-specific attribution and faithfulness execution remain pending. The preserved detector has no verified saved Grad-CAM target artifact.
- Browser use was disabled at the most recent direct access check. Current browser end-to-end behavior and exact downloads remain unverified.
- Independent calibrated measurements, matched expert grades and exposure-cleared unseen-patient evaluation remain unavailable.
- Exploratory percentile grading does not satisfy the strict candidate-local quality/uncertainty acceptance criteria. Strict abstentions remain available in the saved record.
- Controlled difficult-case and nine-phantom historical evidence must be retained. No new phantom benchmark metric was calculated in this audit.
- Training remains paused. No weights or dataset splits changed.

## Resume order

Configure the opt-in installed-checkpoint/public-image fixtures and run their integration tests. Verify API ZIP exports against the newly deployed backend. Restore browser access, then perform upload, select candidate, inspect strict/exploratory measurement evidence, save, refresh, reopen and download all formats. Next establish a fixed detector attribution target and execute the frozen-model faithfulness controls on eligible development inputs.
