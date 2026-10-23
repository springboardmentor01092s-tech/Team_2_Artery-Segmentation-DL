# Training execution and readiness — 14 October 2026

Training all datasets is **not complete**. This report distinguishes executed
validation from prepared GPU workflows. No new epoch, checkpoint or new model
evaluation score was observed during this turn.

## Executed local checks

| Dataset | Observed local data | Outcome / next gate |
|---|---|---|
| ARCADE | Original COCO source; separate syntax/stenosis pipelines and Colab notebooks already exist | 21 targeted tests pass, including original annotation loader, preprocessing, CADICA loader and split logic. Live Colab connection timed out twice; current epoch/checkpoint cannot be verified. |
| CADICA | 6,126 selected frames, 42 patients, seven source box classes, 6,161 boxes | All selected-frame references and box bounds pass. Experimental patient split: 30/6/6 patients and 4,461/982/683 frames train/validation/test. No exact decoded-pixel duplicates across partitions. Ready for GPU execution, not completed. |
| MSD Task08 | 303 training image/label pairs; 140 test volumes | All training voxel arrays read; finite intensities and labels in {0,1,2}. Two tiny header rounding differences (<0.001 per affine element), recorded without changing originals. Source JSON lists 139 test volumes despite declaring 140; `hepaticvessel_247.nii.gz` is present but unlisted. No test images enter fitting. |
| Mendeley stenosis | 8,325 BMP/XML pairs in nested source ZIP; original train/test CSVs | All image decodes, dimensions, XML boxes and CSV membership checks pass. 7,492 train / 833 test frames. 63 shared filename group tokens are **not verified patient IDs**; clarify grouping and box-coordinate convention before training claims. |
| DCA1 | 134 PGM image/mask pairs | All pairs decode and match dimensions. Licence and patient grouping remain unverified; no stenosis labels assumed. |
| ICA | Previously prepared 616 image/mask pairs | Source masks retained; 122 contain intermediate mask values. Reuse terms, mask semantics and patient grouping remain unresolved. No arbitrary thresholding or training claim. |

CADICA and Mendeley release pages identify CC BY 4.0:
https://data.mendeley.com/datasets/p9bpx9ctcv/5 and
https://data.mendeley.com/datasets/ydrm75xywg/3.
MSD source metadata identifies CC BY-SA 4.0. ICA repository does not expose a
clear dataset licence. A public download alone is not licence verification.

## Prepared separate GPU workflows

- `colab/CADICA_individual.ipynb` and `colab/CADICA_individual_training_bundle.zip`:
  source selected images and annotations retained, clinical spreadsheet omitted,
  SHA-256 and CRC gate, patient-disjoint manifest, pretrained Faster R-CNN,
  validation mAP@[.50:.95] selection, per-class AP/recall, AdamW, mild photometric
  augmentation, LR reduction, early stopping, best/last checkpoints and history.
  Test data is partitioned but not evaluated during model selection. Final test
  evaluation is still required after freezing the chosen experiment.
- `colab/MSD_HepaticVessel_individual.ipynb`: dedicated 3D nnU-Net workflow,
  full-volume audit, lossless source-layout adapter, framework integrity checks,
  CT-specific preprocessing/planning, five-fold full-resolution training and
  out-of-fold configuration/postprocessing selection. Vessel and tumour classes
  remain separate. Not run on a GPU yet. Requires upload of existing original
  tar, substantial disk space and checkpoint persistence between sessions.
- ARCADE notebooks remain separate per anatomy/stenosis task. Test images are
  excluded from fitting and selection; exact training/validation duplicate
  filtering retains original source files. Patient independence is not proven.

These notebooks are prepared artifacts, **not evidence of successful execution**.
No CT tensor is merged with X-ray. No raw source file is modified by the new
audits or preparation scripts. CT preprocessing does not blindly apply 2D CLAHE,
registration or vessel cropping: these may alter calibrated intensities or
discard targets. nnU-Net tracks geometry for resampling and prediction recovery.

## Existing baseline results — not new experiments

`models/segmentation/test_report.json` contains older Attention U-Net test pixel
Dice 0.6690 (syntax) and 0.2844 (stenosis). These reports already consumed the
official test labels, so subsequent experiments on the same test set are not a
fresh blinded benchmark. Preserve this provenance; do not repeatedly tune to
these test scores. They are not clinical validation or state-of-the-art claims.

## Execution blocker and handoff

The project Torch environment reports CUDA=False and MPS=False. Chrome/Colab
control timed out twice. GPU experiments therefore could not be launched or
verified this turn. Reconnect the Chrome control extension and the existing
Colab GPU session, or run the prepared notebooks manually; save checkpoints
before free-session expiry. No paid compute, session termination, or wider
cloud permissions were requested.

For defensible metric improvements, use validation-only architecture/loss/LR
comparisons, imbalance-aware sampling, anatomically justified augmentation,
multiple fixed seeds, and validation-selected ensembles. Report per-case
metrics and uncertainty. High background pixel accuracy is not evidence of good
stenosis detection. No method guarantees the highest evaluation metrics.

Machine-readable evidence: `reports/local_training_intake.json`,
`reports/mendeley_stenosis_audit.json`, `reports/msd_volume_audit.json`, and
`models/individual/cadica/split_manifest.json`.
