# DCA/ICA Coronary Artery Segmentation

An end-to-end PyTorch deep learning and computer vision pipeline for automated coronary artery segmentation, centerline extraction, and vascular caliber estimation on X-ray coronary angiograms using the DCA/ICA dataset.

---

## 1. Project Overview

Accurate identification and structural profiling of coronary arteries from digital X-ray angiograms (DCA/ICA) are essential for diagnosing coronary artery disease (CAD), locating stenosis, and guiding percutaneous coronary interventions (PCI).

This project implements, evaluates, and compares two deep neural architectures:
1. **Baseline U-Net**: Classic encoder-decoder network with skip connections for binary vessel segmentation.
2. **Advanced Attention Residual U-Net**: Enhances U-Net with residual convolutional blocks and additive attention gates to focus on fine, tapering coronary vessels while suppressing soft tissue and bone shadow artifacts.

In addition to segmentation, the pipeline extracts clinical morphometry:
- **Vessel Centerlines**: Single-pixel wide medial axis extraction via topological skeletonization.
- **Vessel Caliber (Diameters)**: Quantitative diameter estimation in pixels via the Euclidean Distance Transform (EDT).
- **Branch Complexity**: Connected component analysis of the coronary vascular tree.

---

## 2. Dataset

* **Source**: DCA1 (Database of Coronary Angiograms) / DCA-ICA dataset.
* **Volume**: 134 coronary angiograms with expert ground truth binary masks.
* **Resolution**: Standardized to $320 \times 320$ pixels via CLAHE (Contrast-Limited Adaptive Histogram Equalization) and symmetric reflection padding, guaranteeing clean downsampling through multi-scale pooling layers.
* **Split Policy**: 70% Training (93 cases), 15% Validation (20 cases), 15% Testing (21 cases).
* **Data Leakage Prevention**: Independent splits stored in `dataset/splits.json` with fixed seed (`42`).

---

## 3. Project Directory Structure

```
DCA-ICA-Segmentation/
│
├── dataset/
│   ├── images/               # 134 preprocessed coronary angiograms (PNG, 320x320)
│   ├── masks/                # 134 binary ground truth masks (PNG, 320x320)
│   └── splits.json           # Train / Validation / Test split allocations
│
├── models/
│   ├── unet.py               # Baseline U-Net architecture
│   └── attention_resunet.py  # Advanced Attention Residual U-Net architecture
│
├── outputs/
│   ├── checkpoints/          # Best PyTorch model weights (.pth)
│   ├── masks/                # Predicted & post-processed binary masks
│   ├── visualizations/       # 4-panel diagnostic and vessel caliber overlays
│   └── reports/              # metrics.json, results.csv, loss & dice curves
│
├── src/
│   ├── preprocess.py         # CLAHE, padding, Dataset, and DataLoaders
│   ├── train.py              # CUDA training, Dice+BCE loss, early stopping
│   ├── evaluate.py           # Test evaluation, metrics computation, comparisons
│   └── vessel_analysis.py    # Noise removal, skeletonization, diameter estimation
│
├── config.yaml               # Centralized hyperparameters & paths
├── requirements.txt          # Minimal Python dependencies
├── main.py                   # Unified CLI runner
└── README.md                 # Project documentation
```

---

## 4. Model Architectures

### Model 1: Baseline U-Net
* **Encoder**: 4 stages of double convolution (`Conv2d -> BatchNorm2d -> ReLU`) followed by $2 \times 2$ Max-Pooling.
* **Bottleneck**: Deepest 512-channel convolutional block.
* **Decoder**: 4 stages of transposed convolutions (`ConvTranspose2d`) concatenating encoder skip features.
* **Output**: $1 \times 1$ convolution projecting to a single logit channel.

### Model 2: Advanced Attention Residual U-Net
* **Residual Conv Blocks**: Identity / $1 \times 1$ conv shortcut connections ($F(x) + x$) preventing vanishing gradients and preserving fine vessel edges.
* **Additive Attention Gates**: Employs gating signals from deeper decoder stages to modulate encoder skip connections ($x \cdot \alpha$), filtering out irrelevant background cardiac structures.
* **Decoder**: Attention-gated feature fusion followed by residual refinement.

---

## 5. Installation & Setup

### Requirements
* Python 3.10+
* PyTorch 2.0+ with CUDA support
* OpenCV, Scikit-Image, SciPy, Matplotlib, Pandas, PyYAML

```bash
# Clone or open the project folder
cd DCA-ICA-Segmentation

# Install dependencies
pip install -r requirements.txt
```

---

## 6. How to Run

### Run Complete Pipeline End-to-End
Execute dataset verification, training of both models, test evaluation, comparison chart generation, and vessel morphometry analysis with one command:
```bash
python main.py --mode all
```

### Run Individual Stages
* **Preprocess & Verify Dataset**:
  ```bash
  python main.py --mode preprocess
  ```

* **Train Models**:
  ```bash
  # Train both models
  python main.py --mode train --model both

  # Or train individually:
  python main.py --mode train --model unet
  python main.py --mode train --model attention_resunet
  ```

* **Evaluate on Held-out Test Set & Generate Reports**:
  ```bash
  python main.py --mode evaluate
  ```

* **Run Vessel Centerline & Diameter Analysis**:
  ```bash
  python main.py --mode analyze
  ```

---

## 7. Quantitative Test Evaluation & Results

Evaluated on 21 held-out test coronary angiograms from the DCA/ICA dataset:

| Metric | Baseline U-Net | Attention ResU-Net | Absolute Delta | Relative Gain |
| :--- | :---: | :---: | :---: | :---: |
| **Dice Score (F1)** | 0.7539 +/- 0.0532 | **0.7699 +/- 0.0481** | +0.0160 | **+2.12%** |
| **IoU (Jaccard Index)** | 0.6078 +/- 0.0670 | **0.6282 +/- 0.0636** | +0.0204 | **+3.36%** |
| **Precision** | **0.7653 +/- 0.0632** | 0.7651 +/- 0.0694 | -0.0002 | -0.03% |
| **Recall (Sensitivity)** | 0.7562 +/- 0.1050 | **0.7888 +/- 0.0999** | +0.0326 | **+4.31%** |
| **Specificity** | **0.9884 +/- 0.0059** | 0.9878 +/- 0.0069 | -0.0006 | -0.06% |
| **Mean Centerline Length** | 799.4 px | **841.8 px** | +42.4 px | **+5.30%** |
| **Mean Vessel Caliber** | 5.63 px | 5.59 px | -0.04 px | - |

---

## 8. Deliverables Generated

1. **Model Weights**:
   - `outputs/checkpoints/best_Baseline_UNet.pth`
   - `outputs/checkpoints/best_Attention_ResUNet.pth`

2. **Evaluation Metrics & Reports**:
   - `outputs/reports/metrics.json`: Overall summary metrics (Mean ± Std).
   - `outputs/reports/results.csv`: Case-by-case test metrics for all 21 test patients.
   - `outputs/reports/model_comparison.png`: Side-by-side grouped bar chart comparing Dice, IoU, Precision, Recall, and Specificity.
   - `outputs/reports/model_comparison_report.md`: Markdown summary table.

3. **Vessel Morphometry Outputs**:
   - `outputs/reports/vessel_analysis.csv`: Centerline length, caliber (mean/median/max diameter), and branch counts per test case.
   - `outputs/reports/vessel_analysis.json`: Serialized vessel morphometry data.

4. **Visualizations**:
   - `outputs/visualizations/<Model>/<case>_comparison.png`: 4-panel visualizer (Angiogram, Ground Truth, Prediction, Color Overlay).
   - `outputs/visualizations/<Model>_vessel_analysis/<case>_vessel_caliber.png`: 4-panel centerline & caliber heatmap.
   - `outputs/reports/<Model>_loss_curve.png`: Loss progression.
   - `outputs/reports/<Model>_dice_curve.png`: Dice & IoU progression.

---

## 9. Clinical Significance & Discussion

- **Noise Suppression**: Coronary angiograms suffer from non-uniform X-ray illumination, catheter shadows, and overlapping anatomical structures. The Attention Gates in Attention ResU-Net suppress false positives in background soft tissue.
- **Centerline Continuity**: Morphological closing and connected component filtering retain fine distal vessel branches while eliminating isolated specks.
- **Diameter Profiling**: Utilizing Euclidean Distance Transform along medial axis centerlines enables automated stenosis detection and vessel caliber tracking without manual caliper measurement.

