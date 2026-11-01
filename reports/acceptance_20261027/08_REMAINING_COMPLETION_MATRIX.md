# Remaining-task acceptance matrix — 27 October 2026

Read the full Remaining Tasks Completion and Verification Master Directive,
attachment 2444c8cf-0418-491f-bd5f-3e7842df7c82. This is a current gap report,
not a declaration that the project is complete. Prior user revocation of AGENTS
remains; the attachment's generic instruction does not restore revoked rules.
Training/pooling remain prohibited under the latest explicit instructions.

Status applies to the stated acceptance scope, not every possible use of a module.

| Task | Status | Evidence and remaining acceptance / exact next step |
| --- | --- | --- |
| Baseline 2D/3D workflow smoke check | COMPLETE_VERIFIED | Fresh public cases completed actual checkpoints and artifact retrieval; `../fresh_cases_20261027T084950Z/VERIFICATION.md`. No reference-mask accuracy claim. |
| Attention U-Net implementation | IMPLEMENTED_NOT_VALIDATED | Separate research code, eleven synthetic checks; full research suite previously 110 passed. No checkpoint. |
| Attention training | TRAINING_PENDING_AUTHORIZATION | Training freeze active; exact remote inputs, patient/source gates and free quota also unresolved. Lift restriction before any optimizer execution. |
| Matched Attention comparison | EVALUATION_PENDING | Research `ATTENTION_ARCADE_COMPARISON_20261027.md` pins baseline and candidate contracts; case manifest/preprocessing must be finalized and candidate measured. |
| ARCADE compatibility | EVALUATION_PENDING | Historical 2,400-pair technical audit reused; complete syntax polygon correspondence, remote release/hash linkage, patient/overlap and rights gates on Kaggle. |
| Compatible pooling | BLOCKED_MISSING_DATA | No approved full source/patient/rights contract. No ARCADE lesion-mask/artery target conflation. |
| Tiny-hole improvement | REJECTED | Kaggle run 362745762 v1, 200 cases, gain below .001; FP +62, FN -46. Baseline retained; never rerun unchanged. |
| Stenosis lesion-level evaluation | EVALUATION_PENDING | Existing 2D predictions and historical metrics are not a new reproduced lesion evaluation. Fix original threshold/matching, eligible cohort and per-case FP/misses before remote execution. |
| Centerline and vessel graph | IMPLEMENTED_NOT_VALIDATED | Synthetic straight, bend, branch, cycle, empty/disconnected tests; real reviewed anatomical references missing. |
| Diameter measurement | IMPLEMENTED_NOT_VALIDATED | Approximate mask widths, not validated lumen diameters. New explicit method/percentile/scope metadata; obtain reviewed reference diameters and report bias/MAE/RMSE. |
| True 2D cross-sectional area | NOT_APPLICABLE | Projected area is not cross-sectional area; current API returns cross-section unavailable. |
| Narrowing arithmetic | IMPLEMENTED_NOT_VALIDATED | Sixteen prior arithmetic/identity/calibration checks; saved reviewed local/reference measurement workflow and real validation still required. |
| Severity classification | BLOCKED_MISSING_DATA | No approved threshold/reference measurement or severity label protocol. Keep NOT_ASSESSABLE/unavailable; do not infer grades from masks. |
| Grad-CAM | EVALUATION_PENDING | Not implemented as a verified case/model-linked pipeline. Training freeze also prohibits backpropagation: resolve authorization for attribution gradients before real execution. Feature gates are not Grad-CAM. |
| Gemini | EVALUATION_PENDING | Deterministic explanations exist; secure SDK service, schema grounding, saved versions and real request/fallback tests not complete. No key requested or exposed here. |
| 3D source geometry and segmentation artifacts | COMPLETE_VERIFIED | Fresh 512x512x321 CTA source mask binary, affine/shape preserved; finite 128-cubed probabilities and three decoded PNGs. Workflow check, not anatomical validation. |
| 3D vessel graph and measurements | EVALUATION_PENDING | Needs dimensionality-specific centerline, spacing-aware graph and synthetic/real reference validation. Do not reuse 2D projected geometry. |
| 3D stenosis and severity | BLOCKED_MISSING_DATA | No verified compatible 3D lesion checkpoint/reference measurements. No silent 2D substitution. |
| 3D complete report workflow | EVALUATION_PENDING | NIfTI/PNG/result JSON verified; 3D run-linked PDF/CSV and downstream unavailable-stage reporting still need implementation/testing. |
| 2D saved report exports | COMPLETE_VERIFIED | Fresh real run JSON/CSV/PDF exports fetched; prior identity/history/RBAC fixture tests. Human review not fabricated. |
| Full application acceptance | EVALUATION_PENDING | Prior 143 passed/5 real-checkpoint opt-ins skipped; later fresh 2D/3D checks supplement only their specific scope. Final security/capacity/recovery acceptance remains. |
| GPU capacity / free Kaggle resources | BLOCKED_RESOURCE | Editor displayed 00:00/30 hrs, disabled Start/Run. No usable free quota confirmed; recheck without allocating resources early. |
| Container runtime | BLOCKED_RESOURCE | Docker unavailable; static checks are not clean build/start proof. |

## Changes in this increment

`backend/app/analysis_model.py` adds explicit global-width method, sampling,
percentile semantics, missing uncertainty/reference validation and
`suitable_for_automatic_severity=false`. Existing numeric results are unchanged;
historical saved runs are not rewritten. No clinical measurement claim follows.
`test_vessel_centerline.py` checks these disclosures on the synthetic tube.

Verification: `.venv/bin/python -m pytest tests/test_vessel_centerline.py
tests/test_narrowing.py tests/test_standard_pipelines.py -q` from backend:
**34 passed in 2.04 seconds**, one existing Starlette/httpx deprecation warning.
These are software tests, not model/anatomical validation.

The research experiment code/test hashes were verified in the preceding gate
report; unchanged checks and completed source audits were not repeated. No
new candidate score, checkpoint, training job, research inference, protected-test
access, pooling, activation, deployment or Git push occurred.

## Dependency order

First complete permitted Attention source/contract preparation; train only after
authorization, compatibility and remote resource/budget gates. Then reproduce
stenosis evaluation separately. Geometry reference validation and measurement
workflow software can proceed without claiming anatomical accuracy. Severity
stays blocked if references cannot be established. Explainability and 3D each
need independent run/model identity and failure-state tests before full acceptance.
