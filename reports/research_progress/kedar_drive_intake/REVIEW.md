# Kedar DCA1 handoff

[Shared CoroVision folder](https://drive.google.com/drive/folders/1hHm0tzm41R5p5gZicBUHYNwDUgd-kEF0)

## Milestone 2 · Segmentation and vessel profiles

The per-image CSV reproduced the earlier Drive results on the same 21 declared evaluation image IDs for each model. The split manifest declares 93 training, 20 validation and 21 evaluation image IDs with no ID overlap. Patient grouping and checkpoint exposure remain unverified. The folder's README gives a different pair of Dice scores. The table uses the CSV and its accompanying metrics JSON.

| Model | Mean Dice | Mean recall | Mean per-image width (px) | Mean centerline length (px) |
|---|---:|---:|---:|---:|
| Baseline U-Net | 0.7572 | 0.8036 | 5.90 | 847.95 |
| Attention ResUNet | 0.7595 | 0.7669 | 5.51 | 827.43 |

The 0.0023 Dice difference accompanies a 0.0367 drop in recall. These are source-specific comparisons. Pixel measurements summarize the teammate's processed masks and centerlines. Clinical width validation requires calibrated segment-matched references.

## Milestone 3 · Candidate localization and research grading

The source extracts candidate patches along a mask-derived centerline and scores them with a CNN. The CNN's patch labels are derived from mask geometry and a local caliber-drop rule. Retention also uses the computed narrowing, so a candidate can survive on the geometry rule alone. The source uses pixel measurements, local reference caliber and threshold bands.

The lesion CSV and case summaries reconcile to 457 candidate rows over 21 images. The mean reported narrowing across candidates is 50.86%. The per-candidate rule bins contain 153 mild, 253 moderate and 51 severe outputs. These labels describe the teammate's rule output. All 21 images had at least one retained candidate. This count supplies no estimate of disease prevalence, lesion accuracy or severity accuracy. Independent expert lesion locations and calibrated reference measurements are required for those claims.

## Integration decision

Expose the reviewed aggregate results and source receipt through Model Evaluation → Research progress. Keep these data separate from case predictions, approved severity protocols and matched acceptance experiments. The shared dataset, visualizations and checkpoint files were inventoried through Drive listings. This intake reviewed selected source text and output tables and did not execute the teammate's code or load checkpoint bytes. File SHA-256 values in the receipt identify the downloaded artifacts.

## Application verification

The selected backend suite passed 12 tests using `.venv/bin/python -m pytest -q tests/test_research_progress.py tests/test_stenosis_research_evidence.py` from the backend directory. A Chrome Playwright session opened Model Evaluation → Research progress, verified the recorded work entry, and downloaded the receipt. Unauthenticated and viewer requests returned 401 and 403 respectively. The existing model selection was preserved.
