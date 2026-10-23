# Preserved training release integration — 23 October 2026

The application now connects the verified binary artery ResNet34 U-Net and ARCADE stenosis Mask R-CNN ResNet50-FPN baselines through its existing authenticated case-analysis, overlay, centerline and history routes. The Models workspace shows their checkpoint hashes, architectures, frozen validation thresholds and correctly distinguished validation aggregation. It also shows the12task training-evidence roster and separate ImageCAS/ImageCAS-X cross-fitted voxel-score studies as research evidence, without enabling their calibrators or3Dvolume inference.

Artery: SHA256`ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c`, mean per-image Dice0.827277 on200development-validation frames. ARCADE stenosis masks: SHA256`f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`, pooled unionDice0.564392 on200development-validation frames. The archive lesion-box detector is a distinct task and is not substituted for a mask. No rejected experiment or incompatible architecture replaces these preserved weights. Historical tests remain bound to their original artifacts.

## Verification

- Frontend TypeScript/Vite production build passes.
- Hash-tamper fail-closed behavior, legacy-provider rollback, mask/instance semantics and optional installed-checkpoint API integration tests pass.
- On one existing development image, the application and original pinned training implementations produced bit-identical artery probabilities/masks and stenosis probabilities/masks:6999artery pixels,3366stenosis pixels,3stenosis instances. This verifies one integration input, not a new performance estimate.
- A separate synthetic-image live test passed login, model readiness, case creation, upload, real-checkpoint analysis, saved overlay and history through FastAPI. The Vite API proxy and backend health both return200. A second user cannot analyze or read the first user's case artifacts in the integration test.
- Original branch baseline:66passed,1skipped,2failed. Integrated default suite:69passed,2skipped,2failed; the additional installed-model test is opt-in. The same two failures reproduce from an untouched archive of commit`14d74e87d0a92495b240e6817e153b9893743d31`: `test_admin_operational_grants_cannot_be_self_approved_or_bypass_resources` and `test_5_roles_permission_matrix`. They concern existing role-policy behavior; this integration does not change that policy or claim a clean full suite.

## Local operation and transfer

Local frontend:http://127.0.0.1:5173; backend:http://127.0.0.1:8000. Both bind to loopback only. A local synthetic integration case exists for inspection; it is not patient data. Private login configuration, JWT secrets, databases, uploads, model files and archives are ignored and must not be committed. No personal credentials appear in this report.

The application-specific artifact is`CoroVision_application_mask_models_v1.zip`, containing only the two pinned checkpoints and release contract. Use `scripts/install_trained_release.py` on the other laptop as described in`docs/TRAINED_RELEASE_INTEGRATION.md`. Weights are not pushed to GitHub. Target-laptop installation/performance and actual application acceptance there remain unverified. The earlier standalone three-model handoff is a different artifact and cannot be installed as this two-mask release.

No training job is launched by the application. The source release catalog distinguishes deployed2Dmasks from offline anatomical, DCA, CADICA, hepatic, Aorta and ImageCAS research tasks. Residual misses/false positives, source overlap, lack of independent clinical negatives and incomplete patient-confidence validation remain. Application integration does not establish clinical reliability or complete every project module.

After incorporating the application-only cleanup at f71e91b: full backend suite with installed-model integration enabled reports 61 passed, 1 skipped, and the same 2 existing permission-policy failures. The retained training-dataset test now skips when its deliberately removed training runner is unavailable; no training code was restored. The frontend production build and live readiness check pass.
