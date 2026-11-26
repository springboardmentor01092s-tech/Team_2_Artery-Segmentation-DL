"""
Main Entrypoint for CoroVision-AI Project:
Coronary Artery Segmentation, Vessel Morphometry,
Stenosis Severity Classification, Explainable AI (Grad-CAM),
Model Comparison, Automated Reporting, and API Service.
"""

import argparse
import os
import unittest

from src.preprocess import get_dataloaders, prepare_raw_dataset
from src.train import train_single_model, train_both_models
from src.evaluate import evaluate_both_models
from src.stenosis_detection import run_stenosis_pipeline
from src.gradcam import run_explainable_ai_pipeline
from src.model_comparison import compare_models
from src.report_generator import generate_automated_reports
from src.api import run_api_server


def run_pipeline(mode: str = "all", model_name: str = "both", config_path: str = "config.yaml",
                 port: int = 8000, patient_id: str = None):
    """Orchestrates pipeline execution according to the selected mode."""
    print("=" * 70)
    print(" CoroVision-AI: Coronary Artery Segmentation & Diagnostic Pipeline")
    print(f" Execution Mode: {mode.upper()} | Model Selection: {model_name.upper()}")
    print("=" * 70)

    if mode in ["preprocess", "all"]:
        print("\n--- STAGE 1: Dataset Verification & Preparation ---")
        if not os.path.exists("dataset/images") or len(os.listdir("dataset/images")) == 0:
            if os.path.exists("dataset/raw"):
                prepare_raw_dataset("dataset/raw", output_base="dataset")
            else:
                raise FileNotFoundError("dataset/images not found and dataset/raw not available.")
        train_ld, val_ld, test_ld, splits = get_dataloaders(config_path)
        print(f"Data Splits: Train={len(splits['train'])} | Val={len(splits['val'])} | Test={len(splits['test'])}")

    if mode in ["train", "all"]:
        print("\n--- STAGE 2: Model Training ---")
        train_both_models(config_path) if model_name.lower() == "both" else train_single_model(model_name, config_path)

    if mode in ["evaluate", "all", "analyze"]:
        print("\n--- STAGE 3: Test Evaluation, Comparison & Vessel Morphometry ---")
        evaluate_both_models(config_path)

    if mode in ["stenosis", "all"]:
        print("\n--- STAGE 4: Stenosis Severity Classification, QCA & Localization ---")
        run_stenosis_pipeline(config_path)

    if mode in ["xai", "all"]:
        print("\n--- STAGE 5: Explainable AI (Grad-CAM) Feature Attribution ---")
        run_explainable_ai_pipeline(config_path)

    if mode in ["compare", "all"]:
        print("\n--- STAGE 6: Deep Learning Architecture Benchmarking ---")
        compare_models(config_path)

    if mode in ["report", "all"]:
        print("\n--- STAGE 7: Automated Clinical Reporting (PDF, CSV, JSON) ---")
        generate_automated_reports(config_path, export_formats=("pdf", "csv", "json"), patient_case_id=patient_id)

    if mode == "api":
        print("\n--- STAGE: CoroVision-AI REST API Service ---")
        run_api_server(host="127.0.0.1", port=port, config_path=config_path, blocking=True)

    if mode == "test":
        print("\n--- STAGE: Automated End-to-End & API Test Suites ---")
        loader = unittest.TestLoader()
        suite = loader.discover("tests", pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        res = runner.run(suite)
        if not res.wasSuccessful():
            raise SystemExit(1)

    print("\n" + "=" * 70)
    print(" Pipeline execution finished successfully!")
    print(" Deliverables: checkpoints/, masks/, visualizations/, reports/")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoroVision-AI Pipeline")
    parser.add_argument("--mode", type=str, default="all",
                        choices=["all", "preprocess", "train", "evaluate", "analyze", "stenosis", "xai", "compare", "report", "api", "test"],
                        help="Pipeline stage: 'all', 'preprocess', 'train', 'evaluate', 'analyze', 'stenosis', 'xai', 'compare', 'report', 'api', 'test'")
    parser.add_argument("--model", type=str, default="both",
                        choices=["unet", "attention_resunet", "both"],
                        help="Model to train ('unet', 'attention_resunet', 'both')")
    parser.add_argument("--config", type=str, default="config.yaml",
                        help="Path to configuration YAML file")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port for REST API server (default: 8000)")
    parser.add_argument("--patient", type=str, default=None,
                        help="Case ID for individual patient PDF report generation")
    args = parser.parse_args()

    run_pipeline(mode=args.mode, model_name=args.model, config_path=args.config,
                 port=args.port, patient_id=args.patient)
