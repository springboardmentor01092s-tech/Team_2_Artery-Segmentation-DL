# Severity measurement validation

## Software validation

The focused 10 November 2026 run passed 25 tests across narrowing arithmetic, reviewed measurement persistence, report exports and immutable reporting. Tested conditions include exact 0%, 50%, 75% and 100% reductions; negative/non-finite/boolean values; zero reference diameter; MLD greater than RVD; missing identities; non-millimetre input; missing calibration; unsuitable references; unreviewed boundaries; ambiguous anatomy; unacceptable image quality; RBAC; wrong candidate/run/case; immutable history; JSON/CSV/PDF inclusion; and protocol hashing.

Command from `backend`:

```text
.venv/bin/python -m pytest -q tests/test_narrowing.py tests/test_stenosis_measurements.py tests/test_review_reporting.py
```

## Geometry evidence

The existing deterministic nine-phantom work measures synthetic pixel geometry. Twenty-six of 27 sites were eligible. The low-contrast fixture exposed a 16 px mean absolute width error and 16.67 percentage-point narrowing error despite passing the existing path checks. This is a meaningful failure finding, not patient-image validation.

## Not available

No locked, independently measured real-image MLD/RVD cohort is available. Therefore real-image MAE, RMSE, signed bias, limits of agreement, repeatability across independent readers and physical-millimetre accuracy remain unavailable.

A repository-wide JSON evidence scan on 10 November 2026 found global predicted-mask width summaries and explicit null severity diameters, but no eligible paired independent MLD/RVD records. The saved fields themselves state that their scope is a global mask-width summary rather than a candidate-local lumen/reference measurement and that reference validation is unavailable. They were not imported into the cohort template.

The new independent-reference validator and categorical agreement utility passed 11 dedicated tests. It supports `source_px` references without physical claims and requires calibration provenance for `mm`. It calculates reference narrowing only after provenance, identity, quality, unit, hash and non-circularity checks pass. Agreement metrics remain unexecuted on project data because no eligible paired labels exist.

