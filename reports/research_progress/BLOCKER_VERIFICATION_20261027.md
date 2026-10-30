# Blocked-task investigation — 27 October 2026

## Newly implemented and verified

Research diameter-reduction arithmetic in `backend/app/narrowing.py`:
requires finite consistent minimum/reference diameters in mm, explicit frame,
candidate/reference/protocol identity, calibration and reviewed reference
selection. Returns no clinical category. Does not extract measurements, verify
attestations independently, mutate saved predictions or bypass missing evidence.
This helper is not yet connected to an authenticated persisted reviewed-measurement
workflow; current analysis results correctly remain insufficient evidence.

Command from backend:
`.venv/bin/python -m pytest tests/test_narrowing.py tests/test_integration_pipeline.py tests/test_dashboard_model_registry.py tests/test_trained_release.py -q`

**32 passed, 1 skipped in 9.87 seconds.** The optional real-checkpoint parity
check was skipped; synthetic adapter/fixture tests are not model performance.
These cover arithmetic/rejection, job identity/idempotency, failed/revoked or
changed-input jobs, skipped empty-mask downstream stages, no inferred severity
from global diameters, registry gating/history and adapter semantics.

## Healthy versus abnormal and unseen-data evidence

The original CADICA v4 release documents patient/video IDs and explicit
lesion/non-lesion selected-video files:
https://data.mendeley.com/datasets/p9bpx9ctcv/4
It lists CC BY 4.0. This is release-specific public evidence, not proof our local
copy is that version or that all its negatives were included by our adapter.
The local connected-drive CADICA corrected manifest contains explicit `group`
and `video` fields. No new pixel scan, group-count computation, split rewrite or
holdout evaluation was run locally. Next: match release/content hashes and inspect
the selected frozen model's complete source exposure on Kaggle; audit positive/
negative annotation completeness and patient/split separation before evaluation.

The local file named `cadica_metadata.json` is a generic search response including
unrelated scientific datasets, NOT trusted CADICA release/license verification.
Do not use it to clear rights. Preserve it as historical evidence; no deletion.

ARCADE's existing patient assessment records missing patient identifiers in COCO
exports; no new mapping found in this source inspection. Official Zenodo release
confirms image/category annotations, not a patient-disjoint holdout:
https://zenodo.org/records/10390295
The article endpoint redirected to an inaccessible identity service; PMC showed
a browser check. No security bypass or unsupported license clearance occurred.
ImageCAS/X prior cross-source exposure remains unresolved for independence.

## Pooling

One public release's license cannot clear a multi-source pool. Match exact local
source versions and reviewed semantics, patients, duplicate/exposure manifests
first. Keep artery masks, lesion masks, boxes and source grades separate. No
pooling, weight updates, protected-test access or trained-model evaluation occurred.

## Containers and deployment

Dockerfile and Compose already exist. Added static contract tests for non-root
runtime, healthcheck, one worker, frontend packaging, loopback binding, read-only
model mount, secret requirement and excluded credential/data/checkpoint patterns.
Static text checks do not validate a Docker build or full configuration semantics.
`command -v docker` found no executable. Do not claim container runtime verified
or install/start a deployment without its prerequisites.

Command: `.venv/bin/python -m pytest tests/test_container_contract.py tests/test_operations.py tests/test_operational_policy.py tests/test_notification_bulk.py -q`

**9 passed, 11 warnings in 5.74 seconds.** Includes three static container checks
and six operational/notification access, readiness and mutation-scope checks.
No real model inference, training or Docker runtime involved.

Clinical severity remains blocked by missing validated measurement protocol and
approved reference categories. Arithmetic alone is not clinical validation.
