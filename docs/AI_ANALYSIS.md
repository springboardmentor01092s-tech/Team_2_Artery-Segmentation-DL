# CoroVision AI research analysis baseline

The application uses two independent binary neural models: one predicts artery
regions from ARCADE `syntax` masks, and one predicts suspected stenosis regions
from ARCADE `stenosis` masks. The analysis view overlays the two masks on the
uploaded, preprocessed image. It reports model version and validation Dice.
It does **not** calculate percent narrowing, severity, diagnosis, or treatment
advice. Source PNG/COCO records lack physical pixel spacing and patient grouping.

## Train the lightweight baseline

From the project root, after preparing `data/processed/arcade`:

```bash
python3 -m pip install -r backend/requirements.txt scikit-learn
python3 scripts/train_mlp_baseline.py --train-images 1000 --validation-images 200 --iterations 60
```

This baseline uses two hidden layers (32 and 16 units) on local 5×5 pixel
patches. Its weights are stored as safe NumPy arrays. The script default is a
small demonstration subset; the command above uses the full training split.
For a final academic
experiment, increase sample counts and epochs, tune on validation only, and
evaluate once on the untouched test split. The stenosis validation image with
source ID 155 is excluded because it is byte-identical to training image 218.

Training uses 128×128 grayscale model inputs, a validation-selected mask
threshold, AdamW, a fixed random seed, and the official ARCADE train/validation
split. The API returns 503
for analysis until both models are present. All image and overlay routes enforce
the same case ownership rules as the upload route.

## Current local validation result

The full-split local run in `models/baseline/training_report_mlp.json` measured
Dice **0.6187** for artery masks on 200 validation images and **0.2832** for
stenosis masks on 199 validation images. No test-split score has been reported.
The stenosis score is low; outputs are a functional research demonstration,
not reliable lesion detection. The predicted masks must be reviewed alongside
the source image and ground truth where available. The current
`arcade-pixel-mlp-v2` weights use seeded paired small-angle rotation on the
training split only; older v1 analyses retain their original model version.

## Optional U-Net path

For a stronger convolutional baseline, install
`python3 -m pip install -r backend/requirements-ai.txt` and run
`python3 scripts/train_baseline.py`. U-Net weights take precedence if both
models are present. This path requires a working PyTorch installation.

## Segmentation and vessel-analysis milestone

The comparison runner trains two convolutional architectures for both ARCADE
targets: the existing Tiny U-Net and a new Attention U-Net. `syntax` masks are
converted to binary artery foreground for this experiment; stenosis annotations
remain a separate task. Official train and validation splits are used, with
stenosis validation image 155 excluded because it duplicates training image
218. The trainer does not open the test split.

Install the optional model runtime and run from the repository root. The
trainer supports synchronized flips, BCE plus Dice loss for sparse masks,
ReduceLROnPlateau scheduling on validation Dice, early stopping, and
best-checkpoint retention:

```bash
python3 -m pip install -r backend/requirements-ai.txt
python3 scripts/train_segmentation_models.py --task both --epochs 20 --batch-size 8
```

### Train with Colab GPU

The prepared train/validation images and matching trainer/model code are bundled
for the Colab notebook at
[`colab/CoroVision_Colab_Training.ipynb`](../colab/CoroVision_Colab_Training.ipynb).
Upload `colab/corovision_colab_training_bundle.zip` to
`MyDrive/CoroVisionAI/`, open the notebook in Colab, select a GPU runtime, and
run its cells from top to bottom. It trains both architectures and tasks, then
saves an app-compatible model artifact ZIP and a run manifest with checkpoint
hashes to the same Drive folder. Extract the downloaded artifact at the project
root after backing up `models/segmentation/`; it contains the unique run
version and validation reports. The bundle contains only the public prepared
ARCADE train/validation splits; the held-out test split and user uploads are
excluded. The notebook trains at 512×512 by default, runs a tiny-subset
overfit sanity check, uses synchronized geometric augmentation and a capped
positive-class weight, and selects checkpoints with a validation composite
averaging pixel accuracy, precision, recall, F1, AUC-ROC, Dice, IoU, sensitivity,
and specificity. It also saves fixed validation overlays for visual review.

Best validation checkpoints and reports are written under
`models/segmentation/`. A combined report compares Dice, IoU, precision,
sensitivity/recall, F1, specificity, pixel accuracy, and binned ROC-AUC. Pixel
accuracy is background-sensitive; AUC is estimated from 256 probability bins.
The selected architecture maximizes the average of those nine validation
metrics across artery and stenosis tasks (a binary-mask proxy, not the official
ARCADE instance/category F1); the API uses it for inference when both
checkpoints exist. Accuracy can be background-dominated, and recall/sensitivity
and F1/Dice are duplicate pairs, so the individual scores and overlays should
also be inspected. This selection is validation-driven and is not clinical
validation.

After selecting the architecture and thresholds, generate the final held-out
test report once:

```bash
python3 scripts/evaluate_selected_segmentation.py
```

This refreshes validation metric details for each saved comparison checkpoint,
then evaluates only the promoted checkpoint on the held-out test split with
thresholds fixed from validation. It writes `models/segmentation/test_report.json`.
Do not use the test report to retune or reselect the model.

### Recorded experiment

The following is a historical local eight-epoch binary-mask baseline selected
by mean Dice before the composite ranking described above. It is not the result
of the new Colab training run. The local run used 1,000 training frames per task. On validation,
Attention U-Net scored artery Dice 0.7132 / IoU 0.5542 (200 frames) and stenosis
Dice 0.2772 / IoU 0.1609 (199 frames). Tiny U-Net scored artery Dice 0.6984 /
IoU 0.5365 and stenosis Dice 0.2539 / IoU 0.1454. The selected Attention
U-Net therefore had the higher mean task validation Dice (0.4952 versus
0.4762).

The one-time held-out test report measured Attention U-Net artery Dice 0.6690 /
IoU 0.5026 and stenosis Dice 0.2844 / IoU 0.1658, each on 300 frames, using
threshold 0.25 fixed from validation. See the JSON report for precision,
sensitivity, specificity, F1, pixel accuracy, binned AUC-ROC, and pixel-level
confusion counts. The stenosis results remain
weak for reliable lesion identification; outputs are research masks only.

Inference applies small-component cleanup and single-pixel hole filling, then
extracts a 2D skeleton and estimates local mask width. Measurements are in
pixels unless uploaded DICOM metadata includes valid physical spacing, in which
case the app reports mm. These are approximate mask-geometry descriptors, not
clinical measurements or stenosis grading. ARCADE source PNG/COCO files have
no physical spacing metadata.

### Explainability views and architecture limits

The Analysis Workbench provides artery and stenosis pixel-probability heatmaps,
a segmentation overlay, a Grad-CAM saliency map targeting the
stenosis segmentation logits, and Attention U-Net gate weights when that
architecture is selected. It also compares mask and centerline geometry at the
selected artery threshold and offsets of up to 0.10. These are exploratory
visualizations; they are not
calibrated confidence or proof of model reasoning. The viewer also reports mean
foreground pixel probabilities, explicitly marked as uncalibrated. Grad-CAM++
is not currently implemented.

Only Tiny U-Net and Attention U-Net checkpoints are trained in this project.
ResNet/EfficientNet/DenseNet backbones, U-Net++, DeepLabV3+, nnU-Net, 3D U-Net,
Vision/Swin Transformers, transfer learning, ensembles, multi-scale fusion,
hyperparameter search, and 3D volume analysis remain future work. The interface
identifies these limitations instead of listing untrained architectures as
available models.

The per-analysis vessel summary also reports boundary length, connected mask
components as candidate regions, skeleton endpoints, grouped branch points,
branch-segment count, continuity ratio, a longest-path tortuosity estimate,
diameter range/coefficient of variation, and projected mask area. Connected
components are not validated anatomical branch identities. A 2D angiography
mask cannot provide true 3D lumen cross-sectional area, volume, or voxel-level
segmentation; the UI leaves cross-sectional area unavailable without a suitable
3D scan and annotation.

The centerline graph traces ordered pixel paths between endpoint and junction
candidates, retains cycles and isolated skeleton pixels, and serves a separate
overlay with a faint artery mask, centerline paths, yellow junction labels, and
green endpoint markers. Quality flags report empty predictions, disconnected
regions, frame-edge clipping, short paths, isolated skeleton pixels, and
near-threshold uncertainty when model probabilities are available. They do not
automatically bridge gaps or delete branches. The graph and dimensions are in
the 128×128 model coordinate system; visualization scales paths to the source
frame. ARCADE has no expert centerline references, so path accuracy has not
been evaluated against curated centerline ground truth. Tests cover empty masks,
a Y junction, disconnected regions, a cycle, and graph overlay generation.

## Research limits

- Dice and IoU in the training report describe validation images, not clinical
  performance. The default subset is intentionally small and may perform poorly.
- ARCADE does not provide verified patient identifiers for patient-level split
  assurance. An exact train/validation duplicate was found and excluded from
  this baseline's stenosis validation subset.
- Artery and stenosis masks are independent predictions. A colored region alone
  is not evidence of measured luminal narrowing.
- Do not use real patient images or clinical decisions with this prototype.
