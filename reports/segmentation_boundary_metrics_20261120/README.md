# Segmentation boundary metrics: 20 November 2026

The specification's segmentation evaluation lists Hausdorff distance and average surface distance alongside Dice and IoU. They are now implemented in `backend/app/segmentation_metrics.py`, with the same module in `research_training/` so future training runs report them too. `scripts/evaluate_saved_mask_pairs.py` re-scores frozen prediction/reference pairs without running a model.

## ARCADE validation, 200 images, 512 × 512 binary artery masks

| Model | Dice | IoU | Precision | Recall | Specificity | Hausdorff (px) | HD95 (px) | ASSD (px) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Retained ResNet34 U-Net (in the app)** | **0.8273** | **0.7122** | 0.8444 | 0.8219 | 0.9943 | 70.53 | **46.53** | **6.05** |
| Attention candidate (rejected) | 0.8280 | 0.7133 | 0.8492 | 0.8191 | 0.9945 | 70.76 | 46.84 | 6.09 |

- Values are means of per-image metrics. All 200 images have defined boundary metrics.
- The retained model's Dice and TP/FP/FN counts reproduce the recorded evaluation exactly, which confirms that predictions and references are paired correctly.
- Distances are in pixels on the 512-pixel grid. ARCADE has no pixel spacing, so millimetre values are not available.
- HD95 is dominated by small disconnected false-positive branches far from the reference tree, while ASSD (about 6 px) shows that most of the boundary lies close to the reference.
- The attention candidate is within 0.001 Dice and has slightly worse boundary distances, which supports keeping the retained model.

Inputs: frozen predictions from run 368489597, SHA-256 recorded in each JSON. This is development-validation evidence, not an independent or clinical result.
