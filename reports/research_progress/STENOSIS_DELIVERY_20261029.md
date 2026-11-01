# Stenosis engine implementation and acceptance — 29 October 2026

## Delivered software

- Existing preserved trained stenosis Mask R-CNN executed through the real
  application job pipeline. Candidate mask/region extraction, prepared/source
  bounds, polygons, raw instance scores, overlays and saved explanations exist.
- New append-only `stenosis_measurements` SQL table links reviewer evidence to
  case, image, saved analysis, candidate, reviewer, timestamp and content hash.
  No prediction, clinical assessment or historical report is rewritten.
- New authenticated GET/POST case endpoints reject cross-case/run identity,
  unknown candidates, non-reviewer writes, inconsistent diameters, nonfinite
  values and missing/false calibration/reference attestations.
- Image Analysis includes reviewed measurement history and a clinician-only
  evidence form. It requests local/reference mm, same-frame and segment identity,
  measurement protocol, calibration evidence and reviewed locations. Inputs are
  reviewer attestations, not independently certified or automatic measurements.
- Narrowing is 100*(reference-minimum)/reference, never confidence or global
  mask width. Measurements are separate from the original model severity.
- Research severity classification engine validates a complete nonoverlapping
  protocol partition and exact boundaries. No default clinical cutoffs exist.
  `STENOSIS_SEVERITY_PROTOCOL` may point to a trusted referenced JSON protocol
  with id/version/reference/approved_by/status=approved_for_research and bands
  containing lower/upper/label, fully covering 0..100. Protocol bytes are hashed
  in each measurement snapshot. This config does not itself prove clinical
  validation. No real approved protocol has been supplied/configured, so real
  severity remains not_assessable. Fixture bands are only tests, never defaults.
- New report snapshots include the run's reviewed records in JSON, CSV and PDF.
  Later measurements do not change already saved reports.
- Existing deterministic explanation and localization/score overlays use actual
  saved evidence. These are not a verified Grad-CAM pipeline or Gemini service.

## Actual running model proof

Command: `backend/.venv/bin/python scripts/demo_code_to_outputs.py`.
Job c8b43fbd-1c1f-49d4-a2a1-2189c9ba9ff9 completed.
Event 9568e91f-8f0d-4661-8f2c-41d2b30f0031.
Image 7b62cf5c-7deb-4a38-bfa7-e8bcfafa5ac6.
Saved artifacts: `reports/live_code_demo_aa0c852f/`.

One real model candidate C1, category26; 833 predicted stenosis pixels;
prepared and source bbox [178,156,208,204], saved polygon and raw score
0.9964673519134521. This score is uncalibrated, not disease probability.
Source reference truth was not supplied, so no case accuracy is claimed.
Real severity remains insufficient_evidence. Live authenticated reviewed-record
GET returned HTTP200 and empty list; no fabricated patient measurement was saved.
Application available at http://127.0.0.1:8000 . No queued/running 2D, 3D or
task-specific inference jobs were present before starting the updated API.

## Verification

Focused backend suite: test_stenosis_measurements, test_narrowing,
test_review_reporting, test_integration_pipeline, test_analysis: 30 passed in
8.97s before final stricter boolean/config validation; final rerun recorded below.
Final rerun after stricter validation: 30 passed in 8.75s, one existing
Starlette/httpx deprecation warning. No active inference jobs before final API
restart; latest validation changes loaded into the running application.
Tests include synthetic percent boundaries/invalid protocols, ownership/RBAC,
candidate/run identity, separate immutable histories, exports and saved evidence.
No fixture measurement is inserted in real application records.
Frontend TypeScript/Vite production build passed; existing bundle-size warning
(742KB minified). Browser rendering has not been visually verified because this
chat exposes no browser-control tool. Git whitespace check passed.

## Not completed / exact blockers

New stenosis training is explicitly requested, but no new training or research
evaluation ran. Existing historical trained weights are retained. Kaggle-only
free compute, 900s/one-per-24h/one-job limits, source/reference and exposure gates
still apply. This chat lacks authenticated Chrome control; source-specific
immutable inputs/protocol and usable resources must be verified before dispatch.
Do not substitute local training or invent a gain. Train218 exclusion and
unknown empty annotations remain intact.

Automatic lesion-local diameter extraction, real measurement validation and
clinical severity validation remain incomplete. They require calibrated local
and reference diameters plus an approved referenced grading protocol/cohort.
No clinical thresholds, healthy labels or diagnoses were inferred from masks.
Grad-CAM/other attribution faithfulness and any LLM explanation need separate
actual model-linked implementation/verification; existing overlays do not clear
those tasks. Overall project is not declared complete.
