# Severity classification evaluation

## Current result

The category engine is software tested with a synthetic two-band fixture only. No active five-category protocol and no eligible independent lesion-level severity reference cohort exist. Consequently the following metrics are unavailable and must not be displayed as zero:

- accuracy and macro F1;
- per-class sensitivity/recall;
- weighted Cohen's kappa;
- confusion matrix;
- high-severity sensitivity and false-negative count;
- indeterminate and missing-data rates on an independent cohort.

`backend/app/severity_reference.py` now implements confusion matrix, accuracy, macro F1, class-wise recall and quadratic weighted kappa for already paired independent labels. It deliberately refuses empty, mismatched or unknown-category inputs. This is evaluation readiness, not a project severity result.

## Learned models

Ordinal regression, XGBoost, ResNet/EfficientNet and feature MLP comparisons are design candidates only. No new weights were trained. Synthetic or CoroVision-derived grades must not be recycled as independent ground truth.

## Acceptance state

| Evidence level | State |
|---|---|
| Implemented | Yes - measurement-to-protocol engine |
| Software tested | Yes |
| Development benchmark evaluated | No eligible severity-label benchmark |
| Independent benchmark evaluated | No |
| Qualified-reference validated | No |
| Accepted for clinical severity | No |

