# Teammate research handoff | 9 November 2026

Source: artery_app_share.zip. Results below are historical metrics supplied in the archive. They await independent reproduction and checkpoint-to-cohort verification.

| Reported ARCADE test task, 256 × 256, threshold 0.5 | U-Net Dice | Attention U-Net Dice |
| --- | ---: | ---: |
| SYNTAX artery segmentation | 0.7597 | 0.7509 |
| Stenosis mask segmentation | 0.4888 | 0.4780 |

The binary crop classifier reports 350 TP, 122 FP, 648 TN and 36 FN at threshold 0.5 across 1,156 crops. Its reported F1 is 0.8159 and ROC AUC is 0.9315. These values describe classification of prepared crops. Full-frame lesion localization requires evaluating proposal coverage and matching predicted lesions to references. Patient/study grouping, crop exposure and exact input versions still need verification.

The source implements a segmentation-to-candidate pipeline, crop classification, candidate visualization and classifier Grad-CAM. Selected source is archived under experiments/teammate_artery_app_20261109 in the research workspace. Its intake manifest records the archive and checkpoint hashes. The original ZIP retains the notebooks, documents and checkpoint files.

The source estimates narrowing from local and reference widths derived from a predicted mask. CoroVision's reviewed measurement and severity workflow remains the appropriate path for calibrated outputs. The teammate's automatic severity grades and Grad-CAM have no validated reference or faithfulness receipt in this intake. No teammate checkpoint was loaded, installed or evaluated. Application evidence is available under Research Progress → Source evidence.
