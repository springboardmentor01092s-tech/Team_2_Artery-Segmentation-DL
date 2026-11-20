"""Compute the specification's segmentation metrics from saved prediction/reference mask pairs.

Each input .npz must contain boolean 'prediction' and 'reference' arrays of the same shape.
No model is run; this re-scores frozen outputs. Distances are in pixels unless --spacing is given.
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.segmentation_metrics import segmentation_metrics, summarize  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--label", default="saved mask pairs")
    ap.add_argument("--spacing", type=float, nargs="*")
    args = ap.parse_args()
    files = sorted(args.folder.glob("*.npz"), key=lambda p: (len(p.stem), p.stem))
    rows, tp, fp, fn, tn = [], 0, 0, 0, 0
    digest = hashlib.sha256()
    for f in files:
        z = np.load(f)
        r = segmentation_metrics(z["prediction"], z["reference"], args.spacing)
        r["id"] = f.stem
        rows.append(r)
        tp += r["tp"]; fp += r["fp"]; fn += r["fn"]; tn += r["tn"]
        digest.update(f.name.encode()); digest.update(f.read_bytes())
    summary = summarize(rows)
    summary.update(label=args.label, source_folder=str(args.folder.name), input_sha256=digest.hexdigest(),
                   pooled={"dice": 2*tp/(2*tp+fp+fn), "iou": tp/(tp+fp+fn), "precision": tp/(tp+fp), "recall": tp/(tp+fn),
                           "specificity": tn/(tn+fp), "pixel_accuracy": (tp+tn)/(tp+fp+fn+tn), "tp": tp, "fp": fp, "fn": fn, "tn": tn},
                   distance_unit="mm" if args.spacing else "pixel (512x512 grid; no physical calibration)")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"summary": summary, "cases": rows}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
