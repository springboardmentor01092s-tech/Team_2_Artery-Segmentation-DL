# End-to-end integration phase report — 23 October 2026

Starting application commit: `4a89e82`, branch `lingareddy-dhanush`. The supplied master prompt was read, existing source/training definitions inspected, then the four audit documents were created before implementation changes. The repository-specific reusable prompt is `docs/MASTER_INTEGRATION_PROMPT.md`.

## Implemented and verified

- Existing two-mask release reused without retraining, architecture/threshold changes, purchases, new compute jobs or checkpoint replacement. Artery ResNet34 U-Net SHA `ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c`; ARCADE stenosis Mask R-CNN SHA `f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`.
- Persistent analysis job table/API, database-enforced active-image uniqueness and caller/image request-key idempotency; single-process sequential worker, pending recovery, expired-queue and interrupted-run failures. Execution rechecks account/case permissions, saved input and model version. Results and completed job state commit together. Internal errors are sanitized.
- Versioned validated research result document with input hashes/transforms, model identity, stage status, private artifacts, candidates, measurements, evidence/limitations and human-review state. Non-finite values/invalid prediction shape/range fail closed. Empty artery masks skip meaningful vessel measurements. No validated automatic severity protocol exists, so percentage/category remain null with insufficient_evidence.
- Saved artery/stenosis mask PNGs and float score NPZ, protected by event-specific access checks. Raw scores retain their uncalibrated interpretation. Candidate mask bounds/polygons use the prepared frame, with separately mapped original-image bounds and padding/ROI warnings. No vessel association is fabricated.
- Six deterministic explanation sections refer to saved evidence fields. Workbench and report reuse the same saved explanation/candidate component. Existing report snapshots include the versioned result through event serialization. Historical results are not regenerated using new weights or current validation. Startup no longer invents a duplicate event for an already represented latest overlay.
- Frontend requests jobs, displays/polls state, recovers recent image jobs and preserves uncertain-submit request keys. Existing masks/centerlines/history/reviewer permissions remain. No external LLM or fake diagnosis/training control is introduced.

## Tests and evidence

Final full backend command: `PYTHONPATH=backend CV_TEST_REAL_TRAINED_RELEASE=1 python -m pytest backend/tests -q --tb=no --disable-warnings` in the application environment: **72 passed, 1 skipped, 2 failed**, 93 warnings, 50.39 seconds. The same pre-existing failures remain: `test_admin_operational_grants_cannot_be_self_approved_or_bypass_resources` and `test_5_roles_permission_matrix`. They reproduced on untouched original commit `14d74e8`; access policy was not changed to hide them. The training-only dataset test skips because its runner belongs to the separate training workspace.

The installed-checkpoint test exercises real inference through an actual background thread, authorized job/result/artifact retrieval, private mask and raw-score shape/content, correct SHA binding and unrelated-user denial. Synthetic adapter tests cover repeated keys/new keys, active duplicate suppression, immutable history and restart behavior, revoked account, changed input/model, inference failure, coordinate transforms, missing severity and source-linked explanations. Input format/volume/role tests remain in the existing suite. These are software checks, not clinical validation.

Frontend `npm run build` passes (8414 transformed modules); Vite retains its existing >500 kB bundle-size warning. No dependency upgrade was made to conceal it. Browser automation could not initialize (`failed to write kernel assets`, system path unavailable); **visual browser acceptance is not claimed**.

Source-to-application numerical parity was repeated using the local, unpublished training-reference checker on one existing development frame: both score maps and binary masks bit-identical, artery 6999 px, stenosis 3366 px, 3 retained mask instances. Thresholds .5/.1/.5 unchanged. Evidence in ignored local `output/integration/pipeline_parity.json`; no test set or new performance estimate.

Live localhost synthetic-case smoke check: persistent POST returned HTTP 202 in approximately .203 seconds, duplicate key returned the same job, background execution completed, both mask/raw-score/overlay downloads returned 200, six saved explanation sections present, severity blocked. Evidence in ignored local `output/integration/live_job_api.json`. This input returned zero retained candidate instances; it is not a healthy-case claim. Candidate-coordinate transforms are separately tested and the development parity input has three actual retained instances.

## Preserved model evidence

Artery: 200 development-exposed ARCADE validation frames, mean per-image Dice .8272773139 / IoU .7122207163. Stenosis: 200 development-exposed ARCADE validation frames, pooled union Dice .5643920877 / IoU .3931380448. Aggregations and tasks differ; these remain historical model-validation evidence, not current-image accuracy or independent clinical/final-test results. Other 10 catalogued dataset/tasks and ImageCAS/ImageCAS-X score studies remain offline research evidence; no new deployment is asserted.

## Incomplete and external acceptance

3D inference approval/adapters/native inverse geometry; validated candidate-to-vessel association; reference-diameter severity; patient confidence calibration; governed training/approval service; multi-process worker leases/hard per-job process timeout; production security/retention/monitoring; visual representative-image review and actual other-laptop install/performance remain incomplete. Basic DICOM checks do not establish complete de-identification. The existing permission-policy disagreement requires separate resolution. Detailed manual steps are in INTEGRATION_PLAN.md and INFERENCE_JOB_DEPLOYMENT.md.

Local app remains loopback-only on ports 5173/8000. Checkpoints, archives, login/environment files, databases and uploads are excluded from Git. Prior GitHub publishing was denied by both CLI identity and connected integration; this phase preserves a local commit and does not retry through another account or touch main.
