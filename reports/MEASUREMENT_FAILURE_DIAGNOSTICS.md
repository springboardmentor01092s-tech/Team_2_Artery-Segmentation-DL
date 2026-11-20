# Measurement failure diagnostics — 16 November 2026

The preserved 2D candidates C1–C3 reached source-image lookup, saved-mask lookup, source-coordinate association, centerline/cross-section measurement, persistence and report resolution. The accepted path stopped at `low_local_boundary_contrast`. No cross-run borrowing or coordinate defect was reproduced. Exploratory mask estimates are: C1 7.21/8.49 px (15.02%), C2 8.25/10.00 px (17.54%), C3 7.21/10.00 px (27.89%). None is eligible for accepted severity.

Regression fixtures prove the same implementation yields eligible image-derived measurements when contrast/reference gates pass and abstains for low contrast, missing reference, invalid geometry, disconnected/clipped volume and uncertainty-boundary crossing.

See `SAVED_CASE_MEASUREMENT_DIAGNOSTIC_20261116.md` for immutable hashes and candidate identities.
