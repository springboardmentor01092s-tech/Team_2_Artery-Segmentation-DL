# Segmentation performance comparison — 29 October 2026

Saved historical results only. No new training, inference or accuracy evaluation.

| Task | Model | Dice | IoU | Precision | Recall | Reported task F1 |
| --- | --- | --- | --- | --- | --- | --- |
| syntax | maskrcnn_resnet50_fpn | 0.743180 | 0.591318 | 0.829673 | 0.673018 | 0.183910 |
| syntax | maskrcnn_resnet50_fpn_v2 | 0.725700 | 0.569489 | 0.846553 | 0.635042 | 0.202518 |
| stenosis | maskrcnn_resnet50_fpn | 0.571355 | 0.399928 | 0.539545 | 0.607151 | 0.439394 |
| stenosis | maskrcnn_resnet50_fpn_v2 | 0.554794 | 0.383886 | 0.553914 | 0.555677 | 0.422106 |

## Interpretation and limits

Syntax v1 has higher union Dice; v2 has higher reported task F1. Checkpoint selection used task F1, so a Dice-only ranking would misrepresent selection. Stenosis v1 has higher reported union Dice and task F1 than v2.
The task F1 is a saved local port of ARCADE rules, not a fresh official challenge score. Union-mask metrics differ from anatomical instance metrics. Both pairs declare 200 validation cases, matching labels/input/thresholds, but exact per-case identity and patient independence are not independently reproduced here. No paired significance or gain claim follows from these historical aggregates.

## Verified paired frozen postprocessing trial

Kaggle run 362745762 v1: 200 paired cases. Dice 0.827277313893 → 0.827278985642; delta 0.000001671748; FP +62, FN -46. Decision: rejected_baseline_retained. This is one checkpoint with postprocessing, not a multi-model ensemble.
Recomputed aggregate means and TP/FP/FN from saved per-case records match the saved summary. Source comparison and plan SHA256 verified. paired_cases.csv contains all 200 differences. No trial rerun.

Advanced Attention U-Net, U-Net++ and 3D prototypes have no trained comparison result. Their performance remains unavailable. Do not rank binary baseline 0.827277 against instance-model union scores without matching reference/grid/protocol evidence.

External HP SSD was not mounted during this export; local Kaggle backup reports were used. Historical checkpoint hashes remain historical integrity evidence, not a fresh checkpoint verification. Original reports/models/splits are unchanged.

## Source integrity

- CoroVision_Kaggle_Offline_20261024/runs/mokshagnamannam/corovision-arcade-syntax-training/v2/corovision_syntax/models/syntax/comparison_report.json — SHA256 77b039f24cc27425740d4e258eadf4da130923c119ff09b7ebf5311e10363c11
- CoroVision_Kaggle_Offline_20261024/runs/mokshagnamannam/corovision-arcade-stenosis-training/v2/corovision_stenosis/models/stenosis/comparison_report.json — SHA256 36839c5ed25a1afd5bef16b2e65969027186a7fed2e6c2e908fc68d9daabe749
- reports/research_live/kaggle/run_362745762_v1/arcade_frozen_holes_20261027/comparison.json — SHA256 c6b1c57d4e27da2ed2485b7884e6617614e18af327e2c4d7ce07acf4e96f8212
- reports/research_live/kaggle/run_362745762_v1/arcade_frozen_holes_20261027/plan.json — SHA256 2ad13023be6b494b2190d0923013b2fd942a1340fac54fa7e3c728a7e295d613
