"""Evaluate the validation-selected segmentation checkpoint once on ARCADE test."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from app.analysis_model import build_attention_unet, build_model  # noqa: E402
from scripts.train_segmentation_models import ArcadePairs, score  # noqa: E402


def main():
    artifact_root = ROOT / "models" / "segmentation"
    selected = json.loads((artifact_root / "promoted_model.json").read_text())
    architecture = selected["architecture"]
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    comparison_path = artifact_root / "comparison_report.json"
    comparison = json.loads(comparison_path.read_text())
    for experiment in comparison.get("experiments", []):
        task, model_arch = experiment["task"], experiment["architecture"]
        model = (build_attention_unet() if model_arch == "attention_unet" else build_model()).to(device)
        checkpoint = artifact_root / task / f"{model_arch}.pt"
        model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
        input_size = int(experiment.get("input_size", selected.get("input_size", 128)))
        validation = ArcadePairs(task, "val", training=False, input_size=input_size)
        loader = DataLoader(validation, batch_size=8, num_workers=0)
        threshold = float(experiment["best_validation"].get("threshold", 0.5))
        positive_weight = float(experiment.get("positive_class_weight", 1.0))
        experiment["best_validation"] = score(model, loader, device, positive_weight, thresholds=(threshold,))
        experiment["validation_images"] = len(validation)
    comparison["auc_roc_method"] = "256-bin probability histogram, trapezoidal integration"
    comparison_path.write_text(json.dumps(comparison, indent=2))
    results = []
    for task in ("syntax", "stenosis"):
        test_data = ArcadePairs(task, "test", training=False, input_size=int(selected.get("input_size", 128)))
        loader = DataLoader(test_data, batch_size=8, num_workers=0)
        model = (build_attention_unet() if architecture == "attention_unet" else build_model()).to(device)
        checkpoint = artifact_root / task / f"{architecture}.pt"
        model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
        threshold = float(selected.get("thresholds", {}).get(task, 0.5))
        report_path = artifact_root / task / f"{architecture}_report.json"
        training_report = json.loads(report_path.read_text())
        positive_weight = float(training_report.get("positive_class_weight", 1.0))
        metrics = score(model, loader, device, positive_weight, thresholds=(threshold,))
        results.append({"task": task, "architecture": architecture, "test_images": len(test_data),
                        "threshold_from_validation": threshold, "metrics": metrics})
    report = {"architecture": architecture, "model_version": selected["version"],
              "selection_metric": selected.get("selection_metric"),
              "selection_source": "official validation split", "test_split_used": True,
              "auc_roc_method": "256-bin probability histogram, trapezoidal integration",
              "clinical_validation": False, "results": results}
    (artifact_root / "test_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
