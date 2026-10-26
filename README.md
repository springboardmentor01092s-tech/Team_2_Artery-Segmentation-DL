# Artery Segmentation and Stenosis Detection Using Deep Learning

## Overview

This project focuses on **coronary artery segmentation and stenosis analysis** from angiography images using deep learning. The work includes dataset preparation, annotation handling, U-Net based segmentation, model evaluation, post-processing, and vessel structure extraction.

This branch contains the **ML and image-processing implementation** developed for the artery segmentation pipeline.

## Dataset

The project uses the **ARCADE (Artery Recognition and Classification in Coronary Angiography)** dataset.

Two datasets are used:

- **Syntax**
- **Stenosis**

Each dataset contains separate training, validation, and testing data along with the corresponding annotations.

## Technologies Used

- **Python**
- **PyTorch** — model development and training
- **OpenCV** — image and mask processing
- **NumPy** — numerical operations
- **Matplotlib** — visualization
- **U-Net** — baseline segmentation model

## Setup and Usage

### Requirements

- Python 3.9+
- PyTorch
- OpenCV
- NumPy
- Matplotlib

Install the required Python packages using:

```bash
pip install torch torchvision opencv-python numpy matplotlib
```

### Dataset Setup

Place the ARCADE dataset inside the project directory with the following structure:

```text
dataset/
└── arcade/
    ├── syntax/
    │   ├── train/
    │   ├── val/
    │   └── test/
    │
    └── stenosis/
        ├── train/
        ├── val/
        └── test/
```

Each split should contain the required images and annotations.

### Running the Pipeline

First, prepare the annotations and required masks:

```bash
python prepare_annotations.py
```

Run the preprocessing when required:

```bash
python preprocess.py
```

Train the Syntax segmentation model:

```bash
python train.py
```

Train the Stenosis segmentation model:

```bash
python train_stenosis.py
```

Generate predictions:

```bash
python generate_syntax_predictions.py
```

```bash
python generate_stenosis_predictions.py
```

Apply post-processing:

```bash
python postprocess_syntax.py
```

```bash
python postprocess_stenosis.py
```

Extract vessel structures from the processed masks:

```bash
python extract_vessel_structures.py
```

Evaluate the segmentation results:

```bash
python evaluate_syntax.py
```

```bash
python evaluate_stenosis.py
```

Visualization scripts can be used to inspect the original images, masks, predictions, post-processed results, and extracted vessel structures.

## Segmentation Approach

A **U-Net architecture** is used as the baseline segmentation model.

The model consists of:

- **Encoder** — extracts important image features.
- **Bottleneck** — captures deeper feature representations.
- **Decoder** — reconstructs the segmentation map.
- **Skip connections** — transfer spatial information from the encoder to the decoder.
- **Final convolution layer** — produces the predicted artery mask.

Separate model implementations are used for the **Syntax** and **Stenosis** datasets.

## ML Pipeline

```text
ARCADE Dataset
      ↓
Annotation Preparation
      ↓
Image / Mask Preparation
      ↓
U-Net Training
      ↓
Model Prediction
      ↓
Predicted Masks
      ↓
Post-Processing
      ↓
Vessel Structure Extraction
      ↓
Evaluation & Visualization
```

## Model Evaluation

The segmentation models are evaluated by comparing the predicted masks with the ground-truth masks.

The following metrics are calculated:

- **Dice Score**
- **IoU (Intersection over Union)**
- **Precision**
- **Recall**

These metrics help measure how accurately the model identifies the artery regions.

## Post-Processing

Post-processing is applied to the predicted segmentation masks to refine the detected vessel regions and reduce unwanted regions or noise.

The processed masks are then used for further vessel analysis.

## Vessel Structure Extraction

The final stage of the current ML pipeline extracts **vessel structures from the processed artery masks**.

This provides a structural representation of the detected vessels that can be used for subsequent analysis.

## Visualization

Visualization scripts are included to inspect:

- Original angiography images
- Ground-truth masks
- Predicted masks
- Post-processed masks
- Extracted vessel structures

This helps visually compare the segmentation output with the available annotations.

## Current Progress

- ARCADE dataset setup
- Syntax and stenosis dataset handling
- Annotation preparation
- Baseline U-Net implementation
- Syntax segmentation
- Stenosis segmentation
- Model prediction
- Segmentation evaluation
- Syntax optimization experiments
- Post-processing of segmentation masks
- Vessel structure extraction
- Visualization of segmentation results

## Team

**Team 2 — Artery Segmentation and Stenosis Detection**

This branch contains the ML implementation and experimental work for the project's artery segmentation pipeline.