# Validation status — 14 November 2026

The current measurement, local diameter, narrowing, reference collection, severity reference, volume geometry, volume reporting and review reporting suites passed 55 tests. The run recorded one Starlette test-client deprecation warning. These checks exercise software behavior.

## Evidence dependencies

| Task | Current evidence | Remaining dependency |
| --- | --- | --- |
| Physical vessel measurement error | Experimental mask widths and synthetic geometry checks | Independent calibrated measurements. The saved reference lock receipt contains zero independently measured cases and zero verified calibrations. |
| Expert severity agreement | Executable research grading rules | Matched expert grades and a locked grading protocol |
| Unseen cohort evaluation | CARDIAG intake and grouping plan | Frozen-checkpoint exposure comparison and cleared patient/study manifest |
| Attribution faithfulness | Synthetic integrity checks and prepared occlusion protocol | Bound frozen checkpoint, development inputs, actual perturbation maps and quantitative controls |
| Normal/abnormal classification | Saved candidate predictions | Verified case-level negatives and positives |
| Ensemble benefit | DCA two-model protocol | Both pinned checkpoint packages and matched source-grid predictions. A readiness-folder filename search found neither prepared checkpoint. |
| Dataset pooling | Source-specific release audits | Completed annotation, geometry, license and overlap compatibility review |
| Clean deployment capacity | Historical local API latency checks | Docker runtime and clean inference resource measurements. Docker was unavailable in the current environment check. |

## Existing application demonstration

The fresh 2D case has saved mask-width estimates and experimental categories from Gharshitha's percentile/ring rules. The fresh 3D case has saved segmentation, slice previews and report exports. Their saved local verification receipt is `storage/fresh_demo_proof.json` in the project workspace. Neither demonstration supplies independent reference accuracy or expert agreement metrics.

## Reproduce the focused software checks

From the application backend, run `.venv/bin/python -m pytest -q tests/test_automatic_measurement_pipeline.py tests/test_local_diameters.py tests/test_narrowing.py tests/test_reference_collection.py tests/test_severity_reference.py tests/test_volume_geometry.py tests/test_volume_reporting.py tests/test_review_reporting.py`.
