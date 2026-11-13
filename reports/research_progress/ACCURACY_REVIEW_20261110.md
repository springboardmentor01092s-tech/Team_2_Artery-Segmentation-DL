# CoroVision accuracy review · 10 November 2026

## Verified development results

The retained ResNet34 U-Net artery baseline reproduced on 200 ARCADE development images with mean Dice 0.8272773 and IoU 0.7122207. The matched U-Net++ candidate scored Dice 0.7860897. A residual candidate scored 0.8279432 and failed recall and false-negative gates.

The retained Mask R-CNN detector matched masks at IoU 0.5 on 200 development images. Precision is TP / (TP + FP), recall is TP / (TP + FN), and F1 is 2TP / (2TP + FP + FN). These counts do not provide classification accuracy, box AP or clinical performance.

| Recorded detector comparison | TP | FP | FN | Precision | Recall | F1 | FP/image |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Retained research baseline | 195 | 369 | 211 | 0.3457 | 0.4803 | 0.4021 | 1.845 |
| Lower score threshold, run 364196526 v3 | 215 | 492 | 191 | 0.3041 | 0.5296 | 0.3863 | 2.460 |
| ROI-head refinement, run 365244729 | 206 | 383 | 200 | 0.3497 | 0.5074 | 0.4141 | 1.915 |
| Classifier-only refinement, run 365885468 | 196 | 375 | 210 | 0.3433 | 0.4828 | 0.4012 | 1.875 |

Every tested refinement increased false positives. The proposal audit found a box at IoU 0.5 for 199 of 211 missed mask instances among the top 1,000 proposals. It failed the gate for proposal-coverage-driven training. This does not determine which later stage caused the misses.

## Proposed next diagnostic · vessel support

The app generates artery and stenosis predictions independently. Before considering any change based on their agreement, test whether poor artery-mask support is enriched among unmatched detector candidates and how often the artery model fails to cover expert lesion references. A hard artery-mask filter can also remove true positives. It cannot recover missed lesions on its own.

Use the original 200 ARCADE development case IDs only. Bind the retained detector at research score 0.25, both frozen checkpoint hashes, the per-instance predictions and matched references, and same-case artery masks to the identical prepared grid. Require exact baseline TP/FP/FN parity. Verify individual predicted mask artifacts and transforms before starting. A saved per-image union mask is insufficient for instance attribution. Leave the protected test and CARDIAG splits outside the diagnostic.

Predeclare a descriptive comparison of candidate-mask area fraction inside the artery mask for matched and unmatched predictions. Record distributions and sample counts for both groups and the same support fraction for each missed reference. Use the original one-to-one IoU 0.5 matcher. Keep the current threshold and outputs during diagnosis. Only consider a separate candidate if the evidence supports a mechanism and provides a way to protect true lesions. Any subsequent candidate must pass all frozen gates, including the minimum F1 gain, fewer false positives and fewer misses.

## Execution status

Reviewed the published comparison, replay, and proposal-audit receipts. Recomputed the scalar ratios above from saved counts. CARDIAG has grouping metadata for all 645 cases, but its reference alignment and checkpoint exposure checks remain open. It was not scored.

No authenticated Kaggle session, fresh free quota or shared execution lock was available here. The diagnostic is a proposal pending exact artifact binding and resource checks. No new inference, evaluation, training, checkpoint activation or threshold change occurred.
