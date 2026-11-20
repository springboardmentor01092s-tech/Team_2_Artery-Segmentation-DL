# Candidate-local measurement verification

Executed nine synthetic fixtures on 11 November 2026 using declared synthetic paths and candidate regions. Raw results are in `NINE_PHANTOM_LOCAL_RESULTS.json`. Original adapter outputs are preserved alongside the new estimator.

The estimator computes perpendicular source-grid mask cross-sections inside the candidate and chooses the nearest stable contiguous reference window outside it. It requires explicit vessel association and overlap exclusion. This is an experimental geometry module; automatic anatomical association and real-image uncertainty are unresolved.

| Fixture | Current outcome |
|---|---|
| Straight | 0% measured narrowing |
| Curved constant-width | 4.44% apparent narrowing; unresolved error |
| Tapered | 0% under the declared candidate/reference rule; not a stenosis accuracy claim |
| Branch | Abstained: branch ambiguity in candidate region |
| Eccentric | Abstained: discontinuous supplied centerline |
| Two lesions | 50% for the declared first lesion |
| Boundary perturbation | 56.25%; 6.25 percentage-point error from 50% known truth |
| Blur/noise | 56.25%; 6.25 percentage-point error from 50% known truth |
| Low contrast | Abstained: low boundary contrast |

Three of nine fixtures abstained. The low-contrast fixture's original adapter failure remains preserved (16 px width MAE and 16.67 percentage-point narrowing error). The new contrast gate withholds that measurement. Curvature and perturbed boundaries still produce errors. No automatic severity category is enabled: uncertainty remains unavailable, and the saved application candidates lack verified anatomical association/overlap exclusion. A synthetic path declaration does not validate association on real angiograms.

No model weights were loaded or changed by this geometry experiment. No training or Kaggle execution occurred.
