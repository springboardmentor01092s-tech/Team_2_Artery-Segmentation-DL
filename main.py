"""
Main Entrypoint for DCA/ICA Coronary Artery Segmentation Project.
Supports running complete end-to-end pipeline or individual stages:
- Preprocessing & Dataset Verification
- Model Training (Baseline U-Net & Attention ResU-Net)
- Test Evaluation & Comparison
- Vessel Centerline and Caliber Analysis
"""

import argparse
import os
import sys

from src.preprocess import get_dataloaders, prepare_raw_dataset
from src.train import train_single_model, train_both_models
from src.evaluate import evaluate_both_models


def run_pipeline(mode: str = "all", model_name: str = "both", config_path: str = "config.yaml"):
    """Orchestrates pipeline execution according to the selected mode."""
    print("=" * 65)
    print(" DCA/ICA Coronary Artery Segmentation Pipeline")
    print(f" Execution Mode: {mode.upper()} | Model Selection: {model_name.upper()}")
    print("=" * 65)

    if mode in ["preprocess", "all"]:
        print("\n--- STAGE 1: Dataset Verification & Preparation ---")
        # Check if preprocessed dataset exists
        if not os.path.exists("dataset/images") or len(os.listdir("dataset/images")) == 0:
            raw_path = "dataset/raw"
            if os.path.exists(raw_path):
                print("Processing raw images from dataset/raw...")
                prepare_raw_dataset(raw_path, output_base="dataset")
            else:
                raise FileNotFoundError("dataset/images not found and dataset/raw not available.")
        else:
            print("Verified: dataset/images and dataset/masks are ready.")

        train_ld, val_ld, test_ld, splits = get_dataloaders(config_path)
        print(f"Data Splits: Train={len(splits['train'])} | Val={len(splits['val'])} | Test={len(splits['test'])}")

    if mode in ["train", "all"]:
        print("\n--- STAGE 2: Model Training ---")
        if model_name.lower() == "both":
            train_both_models(config_path)
        else:
            train_single_model(model_name, config_path)

    if mode in ["evaluate", "all", "analyze"]:
        print("\n--- STAGE 3: Test Evaluation, Comparison & Vessel Analysis ---")
        evaluate_both_models(config_path)

    print("\n" + "=" * 65)
    print(" Pipeline execution finished successfully!")
    print(" Deliverables generated:")
    print("  - Trained Weights: outputs/checkpoints/")
    print("  - Prediction Masks: outputs/masks/")
    print("  - Visualizations:   outputs/visualizations/")
    print("  - Reports & Charts: outputs/reports/")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coronary Artery Segmentation Pipeline")
    parser.add_argument("--mode", type=str, default="all",
                        choices=["all", "preprocess", "train", "evaluate", "analyze"],
                        help="Pipeline stage to execute: 'all', 'preprocess', 'train', 'evaluate', 'analyze'")
    parser.add_argument("--model", type=str, default="both",
                        choices=["unet", "attention_resunet", "both"],
                        help="Model to train ('unet', 'attention_resunet', 'both')")
    parser.add_argument("--config", type=str, default="config.yaml",
                        help="Path to configuration YAML file")
    args = parser.parse_args()

    run_pipeline(mode=args.mode, model_name=args.model, config_path=args.config)

