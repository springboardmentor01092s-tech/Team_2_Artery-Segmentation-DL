# Verified research result: stenosis threshold comparison

Kaggle `mokshagnamannam/corovision-stenosis-frozen-threshold-20261031`, version3/run364196526 completed. Original COCO input/raster contract passed200 development cases. Restoring source-compatible FrozenBatchNorm2d epsilon0 reproduced all five frozen baseline metrics exactly before evaluating the candidate.

| Development measure | Baseline threshold0.25 | Candidate threshold0.15 |
|---|---:|---:|
| Instance F1 at IoU0.5 | 0.4020618557 | 0.3863432165 |
| True positives | 195 | 215 |
| False positives | 369 | 492 |
| False negatives | 211 | 191 |

Candidate rejected: F1 gain, precision non-regression and false-positive growth gates failed. Precision decreased0.0416428421; false positives increased0.615/frame. Recall gain did not satisfy the complete acceptance rule. Retain the baseline. No activation, checkpoint replacement or new training occurred in this comparison.

Evidence is preserved outside this application snapshot at `reports/execution_readiness_20261030/stenosis_run364196526/`: `RESULT_ASSESSMENT.json`, `ARCHIVE_VERIFICATION.json`, and the original provider result bundle containing parity, alignment, decision, per-case metrics and200 masks plus200 probability files per arm. The819-member archive passed CRC and SHA checks. Archive SHA256: `88d563c55237f7ac2a88ad95098633f4ceef9596ad68f62024127f95ab4511f7`.

This is a research evidence document. It does not establish an application inference event, dashboard rendering proof, expert anatomical alignment, independent validation or clinical severity performance. The normalization correction establishes reproducibility, not an improvement in model accuracy. Advanced U-Net++ training remains a separate reserved, not yet verified executed, trial at the time this document was written.
