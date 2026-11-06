# Milestone3 actual evaluation and missing validation

5November2026. These are real matched200case development results, not protected-test or independent-patient performance.

| Arm | TP | FP | FN | Instance F1 at frozen score.25/maskIoU.5 | Decision |
|---|---:|---:|---:|---:|---|
| Retained baseline |195|369|211|.4020618557|Retained|
| ROI-head365244729 |206|383|200|.4140703518|Rejected: gain.0120085 below.02;14moreFP|
| Classifier-only365885468 |196|375|210|.4012282497|Rejected: F1gain/unionDice/taskF1 gates failed|

The classifier reduced1miss and added6FP. All six predeclared paired mask/box cases were visually reviewed; artifacts/checkpoints and failures remain preserved. Current improvement requirement stays EVALUATION_PENDING. No new optimizer run is authorized under the latest supplied training freeze. The RPN proposal is held, unintegrated and unexecuted.

6 November update: frozen proposal audit 366216357, Version 6, completed without training or optimizer updates. On the same 200 development cases / 406 references, top-1,000 proposal box coverage was 394/406 (97.04%) at IoU 0.5 and 203/406 (50.00%) at IoU 0.75. Only 12/211 baseline mask misses (5.69%) lacked an IoU-0.5 proposal, below the predeclared 25% mechanism screen. The missing-coverage rationale does not clear the held RPN-only training proposal. This is a diagnostic finding, not an accepted detector improvement or causal proof of which later stage failed. Baseline counts reproduced 195/369/211, fixed metrics passed their original 1e-6 parity tolerance, and parameter/buffer state hashes and checkpoint bytes remained unchanged. Training remains frozen.

## Metric definitions and scope

The existing instance evaluator matches lesion masks at IoU.5; do not rename this boxAP, image classification accuracy or clinical diagnosis. FP/image is369/200=1.845forbaseline and375/200=1.875forclassifier. There is no natural lesion-level true-negative count; do not fabricate specificity, FPR, accuracy or imageAUC from these TP/FP/FN alone. AUC requires compatible raw continuous scores and a declared evaluation unit. Recall and sensitivity are the same binary quantity.

For segmentation, preserve original per-case/aggregation definitions and empty-denominator handling. Dice and IoU have the stated algebraic relation for one mask pair or consistently pooled counts; transforming a meanIoU is not generally equal to meanDice. Pixel accuracy can be dominated by background and is not enough to judge thin-branch recall.

New boundary/centerline accuracy requires a fixed eligible source/reference cohort and remote computation. Do not calculate clinical diameter or narrowing error without matched independent calibrated expert reference measurements. Severity macro/weightedF1, confusionmatrix and ordinal metrics require compatible source classes and support; no arbitrary five-class clinical mapping is adopted.

## XAI and software performance

Deterministic saved-evidence explanations and probability displays are not actual detector attribution faithfulness proof. A forward-only occlusion adapter/protocol is prepared;6synthetic checks passed, actual maps=0. It still needs integrated immutable provider-bound execution, fresh Kaggle clearance and actual unchanged-weight/sanity/faithfulness receipts. Gradient/backpropagation methods must not run under the current no-backpropagation freeze.

The pasted latency targets are examples, not accepted limits or measured project results. Future authorized benchmarks must record hardware/input/model/batch/precision, warmup, synchronization, repetitions and median/p95. Local software benchmarks must use synthetic/mock fixtures; real medical-image inference/processing stays Kaggle-only. Existing provider walltime is not per-case inference latency or billed quota. No deployment or paid compute is authorized.

Evidence: the two retained run assessment/report folders and `M2_M3_FOLLOWTHROUGH_REPORT_20261105.md` under shared `reports/execution_readiness_20261030`. All reference-dependent metrics remain explicitly pending.
