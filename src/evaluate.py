"""Full-volume sliding-window evaluation on a manifest split."""
import argparse
import csv
from pathlib import Path
import pandas as pd
import numpy as np
try:
    import SimpleITK as sitk
except ImportError:
    sitk = None
import torch

from .dataset import load_case_from_record
from .inference import load_model, predict_volume
from .metrics import binary_metrics
from .postprocessing import postprocess_prediction


def extract_category(case_id):
    """Infer AortaSeg category from case prefix (e.g. Anev_01 -> Anev)."""
    for prefix in ["Anev", "Nat", "Old", "Dissec", "Ven", "Young"]:
        if str(case_id).lower().startswith(prefix.lower()):
            return prefix
    return "Other"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--checkpoint", default="checkpoints/best_corovision_3d_unet.pth")
    parser.add_argument("--split", choices=["train", "val", "test", "all"], default="test")
    parser.add_argument("--output-dir", default="results/full_volume")
    parser.add_argument("--raw-ct", action="store_true")
    parser.add_argument("--threshold", type=float, default=0.5, help="Probability threshold (default: 0.5)")
    parser.add_argument("--lcc", action="store_true", help="Apply connected component filtering")
    parser.add_argument("--postprocess-mode", choices=["major", "lcc", "filter_small", "none"], default="major",
                        help="Component filtering mode: 'major' preserves largest + major branches, 'lcc' is single largest")
    parser.add_argument("--no-save-masks", action="store_true", help="Skip writing 3D NIfTI prediction masks to save disk")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    df = pd.read_csv(manifest_path)
    required = {"case_id", "image_path", "mask_path", "split"}
    if required - set(df.columns):
        raise ValueError(f"Manifest must contain columns: {sorted(required)}")

    if args.split != "all":
        df = df[df["split"].astype(str).str.lower() == args.split.lower()]
    if df.empty:
        raise ValueError(f"No rows found for split={args.split}")

    # Resolve relative paths exactly as the patch dataset does.
    records = []
    for _, row in df.iterrows():
        rec = row.to_dict()
        if "category" not in rec or pd.isna(rec["category"]):
            rec["category"] = extract_category(rec["case_id"])
        for key in ("image_path", "mask_path"):
            p = Path(str(rec[key]))
            if not p.is_absolute():
                p = manifest_path.parent / p
            rec[key] = str(p.resolve())
        records.append(rec)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, checkpoint = load_model(args.checkpoint, device)
    out_dir = Path(args.output_dir)
    pred_dir = out_dir / "predictions"
    if not args.no_save_masks:
        pred_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for record in records:
        case_id = str(record["case_id"])
        cat = str(record.get("category", extract_category(case_id)))
        print(f"Evaluating {case_id} ({cat})...", flush=True)
        ct, gt, ct_image = load_case_from_record(record)
        probabilities = predict_volume(
            model, ct, device, already_normalized=not args.raw_ct
        )
        pp_mode = args.postprocess_mode if args.lcc else "none"
        pred = postprocess_prediction(
            probabilities, threshold=args.threshold, apply_lcc=args.lcc, mode=pp_mode
        )
        metrics = binary_metrics(pred, gt)

        if not args.no_save_masks:
            pred_image = sitk.GetImageFromArray(pred.astype(np.uint8))
            pred_image.CopyInformation(ct_image)
            pred_path = pred_dir / f"{case_id}_prediction.nii.gz"
            sitk.WriteImage(pred_image, str(pred_path))

        row = {
            "case_id": case_id,
            "category": cat,
            "split": record["split"],
            "threshold": args.threshold,
            "lcc_applied": args.lcc,
            "pred_to_ref_ratio": round(metrics["predicted_voxels"] / max(metrics["reference_voxels"], 1), 3),
            **metrics,
        }
        rows.append(row)
        print(
            f"{case_id}: Dice={metrics['dice']:.4f}, "
            f"precision={metrics['precision']:.4f}, "
            f"recall={metrics['recall']:.4f}, "
            f"pred/ref={row['pred_to_ref_ratio']}x"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Calculate Macro and Micro metrics
    results_df = pd.DataFrame(rows)
    per_case_mean_dice = float(results_df["dice"].mean())
    per_case_median_dice = float(results_df["dice"].median())

    # Category Macro Mean
    cat_means = results_df.groupby("category")["dice"].mean().to_dict()
    macro_dice = float(np.mean(list(cat_means.values())))

    # Micro Aggregated
    tot_tp = int(results_df["tp_voxels"].sum())
    tot_fp = int(results_df["fp_voxels"].sum())
    tot_fn = int(results_df["fn_voxels"].sum())
    micro_dice = float((2 * tot_tp) / max(2 * tot_tp + tot_fp + tot_fn, 1))
    micro_prec = float(tot_tp / max(tot_tp + tot_fp, 1))
    micro_rec = float(tot_tp / max(tot_tp + tot_fn, 1))

    print("\n================ EVALUATION SUMMARY ================")
    print("Checkpoint:", args.checkpoint)
    print("Checkpoint epoch:", checkpoint.get("epoch", "unknown"))
    print(f"Total evaluated cases: {len(rows)}")
    print(f"Per-case Mean Dice:    {per_case_mean_dice:.4f}")
    print(f"Per-case Median Dice:  {per_case_median_dice:.4f}")
    print(f"Macro-Average Dice:    {macro_dice:.4f} (across {len(cat_means)} categories)")
    print(f"Micro-Aggregated Dice: {micro_dice:.4f} (Prec: {micro_prec:.4f}, Recall: {micro_rec:.4f})")
    print("\nCategory breakdown (Mean Dice):")
    for cat_name, c_dice in sorted(cat_means.items()):
        c_rows = results_df[results_df["category"] == cat_name]
        c_p = c_rows["precision"].mean()
        c_r = c_rows["recall"].mean()
        print(f"  {cat_name:8s}: Dice={c_dice:.4f} | Prec={c_p:.4f} | Recall={c_r:.4f} ({len(c_rows)} cases)")
    print("====================================================")
    print("Full metrics CSV saved to:", csv_path)


if __name__ == "__main__":
    main()
