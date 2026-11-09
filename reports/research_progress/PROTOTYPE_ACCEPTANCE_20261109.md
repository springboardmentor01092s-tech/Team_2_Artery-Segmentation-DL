# CoroVision research prototype acceptance

A prototype check passes only for the behavior it exercises. Record each result as software verified, reproduced on a named research cohort, independently validated, rejected, or pending. Keep unavailable fields explicit in reports. Keep the original checkpoints, splits and saved results.

## 1. Foundation

Use synthetic accounts and images to verify registration, login, owner case creation, valid and invalid uploads, source/preview identity and DICOM frame selection. Verify that a second account cannot list or download the owner's case, image or artifacts. Repeat the workflow in the current browser build before marking browser acceptance complete.

Use a source-specific dataset manifest. Record publisher, immutable release, license or explicit permission, split, image hash, annotation ID and geometry. Confirm annotation-to-image correspondence through the original identifiers and saved mapping. Unknown patient keys stay unknown. A split can be described as a file-level split if that is what was verified. Keep pooling disabled until the sources pass alignment, rights, compatibility and exposure checks.

## 2. Segmentation and vessel structure

Use the saved baseline replay to demonstrate reproducibility. Run 365494240 v2 reproduced all 200 masks and probability arrays. Keep the trained ResNet34 U-Net as the retained model based on the matched comparison with U-Net++ run 364600841 v7. Dice was 0.8272773 versus 0.7860897. Keep the latter in the report as a rejected candidate.

Use known synthetic shapes for software checks. A straight tube tests centerline placement and width, a bend tests tracking, a bifurcation tests path ambiguity, and an empty mask tests the unavailable state. For saved cases, identify mask, centerline and profile by case, image and run. Verify refresh and compare downloaded bytes against the stored artifacts. Use source pixels for uncalibrated widths. An independent expert comparison needs same-frame masks or centerlines and matched calibrated lumen references.

## 3. Detection, rule-based severity and explainability

Use the saved Mask R-CNN detections to demonstrate candidate extraction and localization. Display candidate IDs, source-image boxes and detector scores. Check source coordinates on synthetic examples with known positions and transforms. Use the saved cohort only for the research claims recorded in its receipt. Expert lesion annotations are required for independent localization accuracy.

For a controlled severity demonstration, supply explicit synthetic lesion and reference diameters in the same frame and unit. Calculate reduction as 100 × (reference − minimum) / reference. For this fixture alone, define band A as [0%, 40%) and band B as [40%, 100%]. A 1 mm synthetic minimum and 4 mm synthetic reference yield 75%, band B. The API records the configured protocol hash, keeps the clinical validation flag false and leaves previously saved reports unchanged. In ordinary use, an absent approved protocol yields no severity category. Clinical evaluation needs calibration, segment-matched expert measurements and approved grading references.

Provide a traceable explanation by showing the source candidate, the reviewed inputs and the arithmetic used. For model attribution, the prepared occlusion protocol compares the original candidate score with its score after masking a fixed region and matched control regions. Keep the occlusion configuration and case selection frozen. A real attribution claim requires saved score deltas, maps, sanity checks and faithfulness results on the pinned checkpoint.

## 4. Reporting and release

Use saved runs to demonstrate exact case/run history, model version and evaluation links, role-based access, and run-linked JSON, CSV and PDF. Use a different account for denied requests. Demonstrate backup and restore with an isolated test database. For release acceptance, capture the browser flow, build, readiness, security and target-hardware capacity receipts. Capture an actual container build and startup when the target runtime is available. Keep 3D artifact exports separate from any unfinished 3D report format.

## Next eligible Kaggle training

Use the existing free workspace and shared execution lock. Freshly verify quota, ledger, idle sessions and the required reserve before submitting. The older One Touch quota and ledger snapshots establish history only. Current authenticated provider state was unavailable in this session.

The next candidate needs an immutable released input binding, aligned references, an eligible development cohort, checkpoint exposure, a reproducible preprocessing and evaluator contract, and a documented diagnosis from existing failures. The existing stenosis proposal audit did not support retraining proposal generation on its stated hypothesis. Keep the failed threshold, head and classifier experiments as rejected. A different candidate must address a documented failure mode and use the same eligible cases and evaluator as the retained model. For segmentation, compare Dice together with IoU, recall and false negatives. For detection, use the frozen lesion matching protocol and require both false positives and misses to improve within the acceptance gates. Keep a finite epoch/runtime budget, validation-only early stopping, and best and last checkpoints. Record training and validation results before selecting a model. Keep the held-out test protected and review any switch separately.

## Current verification

- Frontend: `node --test tests/*.test.mjs && npm run build` passed all 20 tests and built successfully. Vite reported a chunk larger than 500 kB.
- Backend: the first application test run with the project's Python environment had 58 passes and two evidence failures. The archived assessment used CRLF while the checked-out fixture used LF. The contents matched after normalizing line endings. Restored the exact archive bytes and marked that fixture exempt from Git text conversion. SHA-256 is `40f0d76916880a4dc6591cb37daf46cc4a074b35c5250a7d8bef2d51e6f20f6e`. The production SHA check remains in force.
- Local health endpoint returned the research prototype and reported models ready. This was a health probe. Browser acceptance and fresh Kaggle execution require separate receipts.
- The backend rerun passed all 60 selected application tests. The extended synthetic severity protocol check passed both tests in `tests/test_stenosis_measurements.py`, including the API classification, protocol digest and saved report immutability.
- Backend command from the backend directory: `.venv/bin/python -m pytest -q tests/test_milestone1.py tests/test_auth_module.py tests/test_rbac_system.py tests/test_saved_width_profiles.py tests/test_saved_contour_artifact.py tests/test_candidate_path_association.py tests/test_narrowing.py tests/test_stenosis_measurements.py tests/test_xai_integrity.py tests/test_review_reporting.py tests/test_dashboard_model_registry.py tests/test_backup_restore.py tests/test_operations.py tests/test_volume_reporting.py tests/test_stenosis_research_evidence.py`.
- Focused severity command from the backend directory: `.venv/bin/python -m pytest -q tests/test_stenosis_measurements.py`.
