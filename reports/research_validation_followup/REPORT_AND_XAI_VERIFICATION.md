# Report and xai verification

The Evidence ZIP uses the existing authenticated saved-report endpoint. It contains report.json, report.csv, report.pdf and a versioned manifest with case, image, run and report IDs, byte lengths and SHA-256 hashes. It adds a download control in Reports & Exports. It uses the existing case PDF renderer. API tests check snapshot equality, ZIP manifest hashes, access denial and immutable history.

## Browser verification - 10 November 2026

The Evidence ZIP was downloaded from the actual local Reports & Exports UI for saved report v2 of case `DEMO-DCA1-003-20261109`. The archive contained exactly `manifest.json`, `report.json`, `report.csv` and `report.pdf`. All manifest byte lengths and SHA-256 hashes matched. Report, case, image and analysis-run identifiers matched across the manifest, JSON and CSV. The PDF reopened as an unencrypted two-page document. An unauthenticated request was denied with HTTP 401 and the viewer role was denied with HTTP 403. The integration test also exercises an authenticated user without case access and expects HTTP 404.

The first browser attempt exposed a stale-runtime deployment issue: an older backend process rejected the `zip` format with HTTP 422 even though the current frontend showed the button. Restarting the backend from the current checkout resolved the mismatch. The frontend error parser was corrected so structured API failures no longer render as `[object Object]`. Evidence is recorded in `EVIDENCE_ZIP_BROWSER_RECEIPT.json` and `EVIDENCE_ZIP_BROWSER.jpg`.

Targeted verification: 10 backend tests passed in `test_review_reporting.py` and `test_width_profiles.py`. No model training or checkpoint update occurred.

Existing XAI routes bind maps to saved events. The legacy stenosis U-Net Grad-CAM path records its target. The preserved Mask R-CNN adapter records attribution unavailable. Probability and attention artifacts require separate interpretation. No new trained-checkpoint attribution, faithfulness score, Gemini exchange or real-case grading was performed in this pass. The forward-only protocol remains in the One Touch execution-readiness folder. Research operations require a locked input and eligible cohort, current shared ledger and exclusive ownership, and verified free Kaggle quota.

Case 60 [browser proof](../public_reference_closeout_20261110/CASE60_BROWSER_RECEIPT.json) covers existing candidate downloads. The new ZIP has API and frontend build verification. It has no new browser-click receipt in this pass.

Verification on base revision `a8faf5b` with working changes

- From `backend`, `.venv/bin/python -m pytest -q` returned 232 passed and 5 skipped.
- From `frontend`, `npm run build` succeeded with a Vite chunk-size warning.
- `git diff --check` passed.

The checked-in `pdfs/Project_Documentation.pdf` has three pages. The 28-page specification referenced by the request was not located in this checkout, so the scope table uses the repository PRD and prior milestone evidence.

Expected restoration path: `docs/reference/Artery_Segmentation_and_Stenosis_Detection_Official_28_Page_Specification.pdf`. Until the original file is supplied there (or its authoritative repository path is identified), the 17-module comparison remains indirect and must not be described as a completed source-to-implementation trace.

## Five skipped tests

The five skips are explicit opt-in integration checks rather than skipped unit requirements:

1. Public ARCADE image with installed weights - requires `CV_PUBLIC_HANDOFF_IMAGE` and the connected public fixture.
2. Additional 2D checkpoints - requires `CV_VERIFY_TASK_MODELS=1`; execution smoke only, not a benchmark.
3. Original 3D checkpoints - requires `CV_VERIFY_TASK_MODELS=1`; synthetic nonmedical-volume smoke only.
4. Installed trained release - requires `CV_TEST_REAL_TRAINED_RELEASE=1` and installed checkpoint assets.
5. Installed real 3D checkpoint - requires `CV_TEST_REAL_3D=1` and the real checkpoint.

These skips represent unavailable or intentionally opt-in external checkpoint/fixture infrastructure. They do not justify a scientific-performance claim, and they remain open integration evidence until run with eligible assets.
