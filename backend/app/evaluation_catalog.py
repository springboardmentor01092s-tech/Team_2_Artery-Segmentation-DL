"""Read-only imported validation reports; never executes evaluation or training."""
from .trained_release import RELEASE


def evaluation_runs():
    records = []
    for model in RELEASE["models"]:
        artery = model["task"] == "syntax"
        aggregation = "mean image" if artery else "pooled union"
        records.append({
            "id": f'{RELEASE["version"]}:{model["task"]}',
            "record_type": "imported_release_validation_report",
            "model": {"architecture": model["architecture"], "version": RELEASE["version"],
                      "checkpoint_sha256": model["sha256"], "checkpoint_reference": model["filename"]},
            "task": "binary_artery_segmentation" if artery else "stenosis_masks",
            "dataset": {"name": "ARCADE", "version": None, "split": "validation",
                        "patient_independence_verified": None},
            "dimension": "2D",
            "sample_counts": {"images": model["validation_images"], "patients": None,
                              "studies": None, "excluded": None},
            "metrics": [
                {"name": "Dice", "value": model["validation_dice"], "unit": "ratio",
                 "aggregation": aggregation, "definition": "2 × intersection / (prediction size + reference size)"},
                {"name": "IoU", "value": model["validation_iou"], "unit": "ratio",
                 "aggregation": aggregation, "definition": "Intersection / union of prediction and reference masks"},
            ],
            "protocol": {"id": None, "description": model["validation_status"],
                         "independent_final_test": False},
            "evaluated_at": None, "runtime_seconds": None, "hardware": None,
            "approval_status": None, "reviewer_status": None,
            "source": "ml/releases/corovision_20261023.json",
            "training_history": [], "prediction_artifacts": [], "sample_evaluations": [],
            "limitations": RELEASE["limitations"],
        })
    return records


def catalog():
    runs = evaluation_runs()
    return {"runs": runs, "summary": {
        "evaluated_models": len(runs), "imported_evaluation_records": len(runs),
        "approved_models": None, "experimental_models": None, "running_experiments": None,
        "pending_review": None, "failed_experiments": None, "latest_successful_evaluation": None,
    }, "capabilities": {
        "epoch_history": False, "evaluation_predictions": False, "dataset_audits": False,
        "approval_workflow": False, "live_training": False,
    }, "research_only": True}
