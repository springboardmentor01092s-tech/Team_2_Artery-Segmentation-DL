# CoroVision-DL

Model-only codebase refactored from the uploaded Kaggle notebook.

## Contents
- `src/model.py`: exact `Small3DUNet` architecture from the notebook
- `src/losses.py`: notebook's BCE + soft Dice loss
- `src/preprocessing.py`: CT normalization and CT/mask checks
- `src/dataset.py`: manifest-driven random 3D patches
- `src/train.py`: fine-tuning from the existing checkpoint
- `src/inference.py`: overlapping sliding-window inference
- `src/metrics.py`: Dice, IoU, precision, recall and voxel counts
- `src/evaluate.py`: full-volume evaluation and mask export
- `data/manifest_template.csv`: required manifest columns

## Setup
Use a Python environment with a PyTorch build appropriate for the intended hardware.

```bash
python -m pip install -r requirements.txt
```

Run commands from the `CoroVision-DL` root directory.

## 1. Verify architecture
```bash
python -m src.model
```
Expected parameter count: 48,673.

## 2. Prepare the manifest
Copy `data/manifest_template.csv` to `data/manifest.csv` and add one row per case:

- `case_id`: unique patient/case identifier
- `image_path`: path to the notebook's **normalized** CT volume
- `mask_path`: path to the verified corrected binary mask
- `split`: `train`, `val`, or `test`

Paths may be absolute or relative to `data/manifest.csv`. Do not use example paths. Keep duplicate scans in the same split. Never train and test on duplicate cases.

The notebook reads normalized CT files named like `Anev_01_image_normalized.nii` and masks named like `Anev_01_mask_reversed.nii.gz`. The mask reversal was a candidate correction; verify alignment anatomically before using those masks.

## 3. Checkpoint placement
Copy the actual extracted `.pth` file to:
`checkpoints/best_corovision_3d_unet.pth`

The checkpoint must contain `model_state_dict` or be a raw state dictionary compatible with the model. Strict loading is used to catch incompatible weights.

## 4. Evaluate a full volume before training
For a manifest with a held-out test split:
```bash
python -m src.evaluate --manifest data/manifest.csv --checkpoint checkpoints/best_corovision_3d_unet.pth --split test --output-dir results/baseline
```
The default expects normalized CT input, as in the notebook. For raw HU CT volumes, add `--raw-ct`.

## 5. Fine-tune only after baseline verification
```bash
python -m src.train --manifest data/manifest.csv --checkpoint checkpoints/best_corovision_3d_unet.pth --output checkpoints/corovision_finetuned_best.pth --epochs 5 --lr 5e-5
```
This writes a new checkpoint and does not overwrite the original. The training loop uses random training patches and fixed-seed validation patch sampling; patch Dice is not a substitute for full-volume evaluation.

## 6. Inference on one CT
```bash
python -m src.inference --image "path/to/normalized_ct.nii.gz" --checkpoint checkpoints/corovision_finetuned_best.pth --output results/predicted_mask.nii.gz
```
Use `--raw-ct` for an input image containing raw HU values.

## Important
- Model output is logits; sigmoid is applied for probability predictions.
- The input patch dimensions should be divisible by four.
- The code does not automatically reverse or resample masks.
- AortaSeg-60 provides aortic masks, not coronary stenosis labels.
- Validate anatomical alignment and full-volume results before reporting performance.
