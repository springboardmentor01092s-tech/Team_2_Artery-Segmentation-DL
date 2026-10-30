# Roadmap increment: geometry calibration and software proof

Date: 27 October 2026.
Request: Complete Implementation and Research Roadmap, supplied attachment
`bd7ee1ba-94ad-4f08-a23d-27e7788f472d/Pasted text.txt` (983 lines).

The request retains frozen-only evaluation. No training, model inference,
dataset-quality computation, pooling, checkpoint modification, model activation,
deployment or Git publication occurred in this increment.

## Implemented and checked

`backend/app/analysis_model.py` now accepts physical spacing only when it is a
finite positive two-element numeric vector. Malformed, zero, negative, NaN and
infinite spacing falls back to pixels with `invalid_physical_spacing` review
flag. Previously positive infinity could be treated as physical calibration.

`backend/tests/test_vessel_centerline.py` adds deterministic software fixtures:

- A 31-pixel straight centerline has 30 pixel-to-pixel edges: with spacing
  (row=2 mm, column=0.5 mm), horizontal length is 15 mm and vertical length 60 mm.
- A right-angle centerline has path length 40 px and tortuosity sqrt(2), rather
  than confusing endpoint distance with path length.
- An 8-pixel-wide rectangular tube has approximate width within 1 pixel of 8;
  isotropic half-scale calibration halves length/width and quarters area.
- Six invalid-spacing forms retain pixel units and a review warning.
- Existing empty-mask, bifurcation, cycle, disconnected-region and overlay tests
  remain in place.

Results: geometry suite **14 passed**; combined geometry and narrowing suite
**30 passed**. These are synthetic software checks, not patient-level validation,
Kaggle model evaluations or evidence of improved model accuracy.

Related regression suites `test_analysis.py`, `test_integration_pipeline.py`
and `test_standard_pipelines.py`: **13 passed**, one existing Starlette/httpx
deprecation warning. Total distinct checks for this increment: **43 passed**.
`git diff --check` passed. No real checkpoint execution was requested by these
commands.

One attempted regression command referenced nonexistent
`tests/test_analysis_pipeline.py`; pytest collected no tests. It was corrected to
the actual repository test names; do not count that failed command as coverage.

## Remaining acceptance gates

This does not complete roadmap workstream C or the 28-item project checklist.
Real-image reference diameter errors, curved-tube reference validation,
narrowing-profile validation, 3D centerlines and true cross-sectional areas still
need their own evidence. The width estimate remains twice the nearest background
pixel-center distance, not an exact physical lumen diameter; reported minimum
and maximum fields remain 10th/90th percentiles, not literal extrema.

Existing acceptance reports 01–06, task proof registry and research ledgers
remain authoritative for previously checked work. Independent generalization,
clinical severity grading, Gemini service validation, representative GPU/3D
capacity and Docker runtime acceptance must not be inferred from these tests.

Research execution remains Kaggle-only and subject to the existing shared trial
gate; the rejected 200-case hole-filling trial must not be repeated. No new trial
was launched.
