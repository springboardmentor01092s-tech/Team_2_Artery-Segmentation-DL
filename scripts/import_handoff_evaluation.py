"""Import verified artery training/evaluation records; no training or weight writes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def build_bundle(drive):
    manifest = {}
    with (drive / "CoroVision_Full_20261024/manifest.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            manifest[row["source_path"].replace("\\", "/")] = row

    def read(relative, lines=False):
        row = manifest[relative]
        path = (drive / row["disk_path"]).resolve()
        if not path.is_relative_to(drive.resolve()):
            raise ValueError("Unsafe manifest reference")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("Handoff metadata integrity mismatch")
        return [json.loads(line) for line in raw.decode().splitlines() if line.strip()] if lines else json.loads(raw)

    prefix = "trained_models/syntax_binary_resnet34_v1/"
    config = read(prefix + "config.json")
    selection = read(prefix + "validation_selection.json")
    history = read(prefix + "history.jsonl", lines=True)
    expected = json.loads((ROOT / "ml/releases/corovision_20261023.json").read_text())["models"][0]
    if selection["sha256"] != expected["sha256"] or selection["selected"]["threshold"] != .5:
        raise ValueError("Evaluation is not bound to the installed baseline")
    definitions = {"dice": "2 × intersection / (prediction size + reference size)",
                   "iou": "Intersection / union of prediction and reference masks",
                   "precision": "Foreground TP / (TP + FP)", "recall": "Foreground TP / (TP + FN)",
                   "specificity": "Background TN / (TN + FP)", "accuracy": "(TP + TN) / all pixels"}

    def metrics(values, aggregation):
        return [{"name": name, "value": values[key], "unit": "ratio",
                 "definition": definitions[key], "aggregation": aggregation}
                for key, name in (("dice", "Dice"), ("iou", "IoU"), ("precision", "Precision"),
                                  ("recall", "Recall"), ("specificity", "Specificity"), ("accuracy", "Accuracy"))
                if key in values]

    chosen = selection["selected"]
    return {
        "name": "Preserved ARCADE binary artery · verified drive history",
        "architecture": "resnet34_unet", "version": "corovision-preserved-2d-20261023",
        "checkpoint_sha256": expected["sha256"], "task": "binary_artery_segmentation", "dimension": "2D",
        "dataset": {"name": "ARCADE syntax", "version": "preserved-handoff-20261024",
                    "split": "validation", "protocol": "Mean per-image binary union excluding stenosis; fixed threshold 0.5; development-exposed",
                    "counts": {"validation_images": 200}, "patient_independence_verified": None,
                    "audit_notes": "Shared ARCADE task images; patient mapping unverified. No independent final-test claim."},
        "metrics": metrics(chosen["summary"]["mean_per_image"], "mean per image"),
        "epochs": [{"epoch": row["epoch"], "values": {
            "train_loss": row["loss"], "learning_rate": row["lr"],
            **{"validation_" + key: value for key, value in row["validation"].items()
               if key in definitions and isinstance(value, (int, float))}}} for row in history],
        "samples": [{"id": "ARCADE-syntax-" + str(row["id"]),
                     "metrics": metrics(row, "per image"), "reference_available": False,
                     "reviewed": False, "notes": "Saved numeric evaluation only; reference/prediction images not imported."}
                    for row in chosen["per_case"]],
        "configuration": {key: value for key, value in config.items() if isinstance(value, (str, int, float, bool))},
        "runtime_seconds": None, "hardware": None, "code_revision": None,
        "seed": config.get("seed"), "best_epoch": None,
        "deidentified_research_data": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive", type=Path, required=True)
    parser.add_argument("--owner-email", required=True)
    args = parser.parse_args()
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend/.env", override=False)
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import User, EvaluationExperiment
    from app.evaluation_workspace import Experiment, import_run
    data = Experiment.model_validate(build_bundle(args.drive))
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.owner_email))
        if not user or user.status != "active" or user.role not in {"admin", "ml_engineer"}:
            raise ValueError("An existing authorized ML engineer or administrator must own the import")
        for row in db.scalars(select(EvaluationExperiment)):
            saved = json.loads(row.payload_json)
            if saved["name"] == data.name and saved["checkpoint_sha256"] == data.checkpoint_sha256:
                print("Verified baseline history already imported; no duplicate written")
                return
        result = import_run(data, user, db)
        print(json.dumps({"id": result["id"], "epochs": len(result["epochs"]), "samples": len(result["samples"]),
                          "status": result["status"], "weights_changed": False}))


if __name__ == "__main__":
    main()
