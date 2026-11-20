# Stenosis detector threshold sweep and decision: 20 November 2026

**Decision: keep the current operating point.** The Mask R-CNN ResNet50-FPN checkpoint (`f0bc898c…`) stays at score threshold **0.25** with pixel threshold 0.5. No alternative threshold passed the acceptance gates that were set before the sweep ran. This configuration is now frozen for any later protected test evaluation.

## Run

- Kaggle notebook `mokshagnamannam/corovision-stenosis-validation-sweep-20261113`, version 2.
- Completed in 231.5 s on a free GPU T4 ×2, return code 0.
- 200 ARCADE stenosis **validation** images. The protected test split was not loaded, no training ran, and no weights changed.
- Checkpoint, runner and annotation SHA-256 values are recorded in `decision.json`.
- The 0.25 baseline reproduces the previously recorded result exactly (instance F1 0.4021, 369 false positives, official F1 0.4394).
- An earlier note said this run had no usable output. In fact the complete results were printed to the notebook log; they are captured here.

## Results

| Score threshold | Official ARCADE F1 | Instance F1 (IoU 0.5) | Precision | Recall | False positives (per image) | Pixel Dice | Pixel AUC-ROC | All gates passed? |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0.15 | 0.4504 | 0.3863 | 0.304 | 0.530 | 492 (2.46) | 0.5715 | 0.879 | No |
| 0.20 | 0.4423 | 0.3842 | 0.315 | 0.493 | 435 (2.18) | 0.5702 | 0.870 | No |
| **0.25 (current)** | **0.4394** | **0.4021** | **0.346** | **0.480** | **369 (1.85)** | **0.5714** | **0.857** | Baseline |
| 0.30 | 0.4320 | 0.4107 | 0.363 | 0.473 | 337 (1.69) | 0.5712 | 0.852 | No |
| 0.35 | 0.4267 | 0.4097 | 0.372 | 0.456 | 312 (1.56) | 0.5632 | 0.842 | No |
| 0.40 | 0.4275 | 0.4069 | 0.383 | 0.433 | 283 (1.42) | 0.5642 | 0.833 | No |

## Predeclared acceptance gates, relative to 0.25

- Official ARCADE F1 must improve by at least +0.02. **No threshold reached this.** The best was 0.15, at +0.011.
- Recall must not fall, and precision must not fall by more than 0.02.
- False positives per image must not rise by more than 0.1.
- Pixel Dice must not fall.

Lower thresholds find more lesions but add many false positives; 0.15 adds about 0.6 per image. Higher thresholds reduce false positives but lose recall and official F1. The current 0.25 is the best-balanced option under these rules.

## Context

- Published ARCADE 2023 stenosis results range from about 0.39 (5th place) to 0.535 (2nd and 3rd place) on the hidden test set. This development-validation official F1 of 0.44 sits within that range. It is not a leaderboard result.
- This is development-validation evidence only. It is not independent, patient-level or clinical validation.
