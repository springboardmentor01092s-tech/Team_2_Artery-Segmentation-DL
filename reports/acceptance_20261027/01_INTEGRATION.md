# Phase 1 — Integration test report

The full regression suite tests upload/validation/preprocessing, queued analysis,
stored result identity, mask/overlay artifacts, vessel algorithms, candidate
coordinates, deterministic saved-result explanations, human review and exports.
Evidence: `backend-junit.xml`; key suites include test_integration_pipeline,
test_review_reporting, test_standard_pipelines, test_preserved_input_contract,
test_case_history_preprocessing, test_volume_preprocessing and test_task_inference.

Verified behavior includes idempotent job submission, preserved case/image/run
and model identity, immutable history, scoped artifacts, explicit missing output,
failed jobs without fabricated completed results, revoked access and changed
input/model failures. Synthetic geometry checks verify centerlines/branches.
Reports exercise PDF/CSV/JSON outputs and unavailable measurements.

Tests use the isolated legacy/fixture provider unless explicitly opted into
installed weights. They do not prove current real-checkpoint accuracy or native
3D parity. These five opt-ins were skipped:

- Known public ARCADE image with installed weights.
- All additional 2D checkpoints executing.
- Original 3D checkpoints without substitution.
- Real case upload/analysis/access with installed release.
- Real 3D checkpoint execution and persisted geometry.

No raw patient information was supplied for these tests. Synthetic output bytes
are fixture evidence, not predictions to present as patient findings. Temporary
test storage is intentionally cleaned; JUnit records assertions, not a persistent
native-model output bundle. Existing saved Kaggle per-case artifacts remain
separate research evidence. Full trained upload-to-report acceptance therefore
remains pending real-checkpoint smoke and matched outputs.

Severity correctly remains insufficient evidence without reviewed candidate-local
measurements. The arithmetic helper is not connected to a persisted measurement
entry workflow. Explanations are deterministic; no Gemini request was tested.
