# Research diameter validation

The benchmark used seven deterministic 120 × 80 binary phantoms, three predefined cross-sections per phantom, and the application width adapter. Twenty of 21 sites were eligible. One branch-adjacent site was excluded. Width MAE was 0 px on the straight, branch-away-from-junction, eccentric and two-lesion fixtures, 1.18 px on the curved fixture, 0.65 px on the tapered fixture and 1.94 px on the boundary-perturbed fixture. The perturbed fixture shifted narrowing by 4.73 percentage points. Repeated execution was identical for each fixture.

```sh
PYTHONPATH=backend backend/.venv/bin/python reports/research_validation_followup/phantom_geometry.py
```

See [per-phantom data](PHANTOM_GEOMETRY_RESULTS.csv) and [generator](phantom_geometry.py). The reference is the declared raster cross-section and the estimate is twice the distance to a background pixel centre. The curved fixture compares against column-wise widths, so orientation can contribute to error. The benchmark supplies paths and masks, so the errors isolate width estimation. No image-based segmentation, automatic path extraction, acquisition-noise robustness or physical calibration was evaluated.

Two follow-up fixtures expand the total to nine, with 26 of 27 sites eligible. Both use Gaussian blur with sigma 1.4 pixels and fixed-seed noise with standard deviation 0.06. A thresholded synthetic contrast of 0.70 produced zero error at the three declared sites. At 0.15 contrast, width MAE was 16 px and narrowing MAE was 16.67 percentage points. All sampled low-contrast paths were accepted by the existing adapter despite the errors. This isolates a limitation of threshold-derived input masks and the sampled quality flags. No trained model or real angiographic acquisition was tested.
