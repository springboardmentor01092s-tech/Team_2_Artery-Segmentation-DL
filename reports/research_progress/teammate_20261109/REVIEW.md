# Teammate research handoff | 9 November 2026

Source: artery_app_share.zip. Results below are historical metrics supplied in the archive. They await independent reproduction and checkpoint-to-cohort verification.

| Reported ARCADE test task, 256 × 256, threshold 0.5 | U-Net Dice | Attention U-Net Dice |
| --- | ---: | ---: |
| SYNTAX artery segmentation | 0.7597 | 0.7509 |
| Stenosis mask segmentation | 0.4888 | 0.4780 |

The binary crop classifier reports 350 TP, 122 FP, 648 TN and 36 FN at threshold 0.5 across 1,156 crops. Its reported F1 is 0.8159 and ROC AUC is 0.9315. These values describe classification of prepared crops. Full-frame lesion localization requires evaluating proposal coverage and matching predicted lesions to references. Patient/study grouping, crop exposure and exact input versions still need verification.

The source implements a segmentation-to-candidate pipeline, crop classification, candidate visualization and classifier Grad-CAM. Selected source is archived under experiments/teammate_artery_app_20261109 in the research workspace. Its intake manifest records the archive and checkpoint hashes. The original ZIP retains the notebooks, documents and checkpoint files.

The source estimates narrowing from local and reference widths derived from a predicted mask. CoroVision's reviewed measurement and severity workflow remains the appropriate path for calibrated outputs. The teammate's automatic severity grades and Grad-CAM have no validated reference or faithfulness receipt in this intake. No teammate checkpoint was loaded, installed or evaluated. Application evidence is available under Research Progress → Source evidence.

## Stenosis follow-up

The sgharshitha branch at `e01dbed529e2bc58d4e55601222a56a3b00a3094` contains the 256-square binary mask model and its reported segmentation metrics. The more complete detector workflow is in the separate ZIP. It builds connected components from the stenosis mask, rejects components with less than 30% predicted artery overlap, and runs a 64-square crop CNN on the remaining candidates. The crop builder gets positives from reference boxes and samples negatives away from those boxes on images that have at least one annotated stenosis. Its crop F1 therefore does not measure detection of lesions in a full image or the handling of real detector false positives.

The candidate-level CNN is the most relevant research contribution for CoroVision's false-positive problem. Use the archived classifier hash `cfabbd5ffb1355cb35182d1bc8745efa2423b15762e03a43b9f9f5b01f6be4af` and bind its preprocessing and original crop exposure before considering a trial. Compare scores on the retained detector's existing, matched and unmatched proposals on an eligible development cohort. Report performance before and after any separately predeclared candidate rule. Record the true positives lost by the classifier and the artery-overlap screen separately. No hard artery-overlap filter is justified by the crop result. A filter alone cannot recover lesions absent from the proposal list. The archived Grad-CAM explains the crop classifier and would need its own attribution verification.

This was a static source and saved-results review. No checkpoint was loaded, no new metrics were generated, and the active detector was retained.

### S. Gharshitha’s severity grading

The archived `backend/app/stenosis_pipeline.py` implements grading in `localize_candidates` and `severity_from_pct`. It estimates local width from the 10th percentile of predicted mask widths inside the candidate box and reference width from the 75th percentile of widths in a nearby ring on the same connected component. It calculates percentage narrowing from their ratio and assigns a threshold-based grade.

A connected component can contain branches, so the ring can sample a different branch. The percentiles are sensitive to mask errors and box placement. The archive provides segmentation metrics but no matched expert diameter or severity validation for this method. During the demonstration, show the saved candidate and mask-width profile, then show the separate measurement and severity fields and their evidence status.
