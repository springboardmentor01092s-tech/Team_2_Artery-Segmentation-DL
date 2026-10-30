# Frozen-model integration increment — 27 October 2026

User requested finishing remaining stenosis/severity/explainability/3D work while
keeping training paused. This increment does not complete that broad objective.

## Implemented

- `backend/app/volume_reporting.py`: deterministic saved-run explanation and
  stage availability; source/run/case/model/checkpoint/preprocessing/geometry
  provenance; stable snapshot hash; no fake local diameters, severity or human
  assessment; CSV formula escaping. No model execution or external AI request.
- Authenticated `/api/cases/{case_id}/volumes/analyses/{run_id}/report/{json|csv}`
  endpoint checks report permission, case access, exact run association and
  completed-result state. No source records are rewritten. Exports are derived
  read-only documents, not new persisted/approved clinical report revisions.
- Existing React 3D section displays explanation, stage reasons and export
  controls; selected run changes clear prior report, failed access is explicit,
  layer changes do not run models or external explanation calls.

UI/UX skill guidance favored explicit text states, error feedback and progressive
disclosure within existing layout. Browser tools are unavailable, so actual
rendered controls were not visually verified; only build/API behavior confirmed.

## Verification

`pytest tests/test_volume_reporting.py tests/test_volume_inference.py -q`:
**12 passed, 1 skipped** (opt-in real-checkpoint run), one existing Starlette
deprecation warning. Covers no source mutation, missing evidence, stable/run-bound
hash, incomplete runs, CSV escaping, authentication, outsider/cross-case denial
and completed/failed status. An initial test setup failed before app startup;
corrected to initialize the test application's isolated database first.

`npm run build`: passed; existing >500kB chunk warning remains.
`git diff --check`: passed.

Live backend restarted only after zero active analysis jobs, PID 6132. Existing
saved FRESH-3D-fdbe28 run d0fbbf42-e090-4fb5-a586-65eaab605321 fetched through
authenticated real localhost requests: JSON HTTP200/3412bytes, CSV HTTP200/
1399bytes. Correct case/run and ImageCAS model identity asserted. Exports saved
under `reports/fresh_cases_20261027T084950Z/volume-stage-report.{json,csv}`.
No inference was rerun. Chrome open requested; no UI automation claim.

## Outstanding work, not disguised as complete

Existing 2D stenosis model/overlays run; fresh lesion-level matched evaluation is
still pending remote eligibility/protocol. Clinical severity requires validated
local/reference diameter evidence and approved standards. No compatible 3D
stenosis output, validated 3D graph or cross-sectional diameter exists for these
saved runs. New report marks these unavailable/not assessable, not healthy/zero.
Gemini SDK/service/credentials and real grounded request/fallback testing are not
implemented by this increment. Grad-CAM needs a supported target and explicit
resolution of current no-backpropagation restriction. No heatmap is fabricated.
3D PDF/versioned human-review snapshots remain unimplemented. Full clinical or
anatomical validation is not established by these software tests.

Training stays paused. No checkpoints, original splits, predictions or human
assessments changed; no activation, deployment, remote job or Git push occurred.
