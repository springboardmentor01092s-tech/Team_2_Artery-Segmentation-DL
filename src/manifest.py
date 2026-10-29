"""Automated manifest generation and dataset validation across all six AortaSeg-60 categories."""
import argparse
import csv
from pathlib import Path


# Known duplicate groups and split allocations for AortaSeg-60 to eliminate data leakage
CANONICAL_CASES = {
    "Anev": {
        "Anev_01": {"split": "train", "group": "anev_g1", "notes": "Z-reversed candidate"},
        "Anev_02": {"split": "train", "group": "anev_g2", "notes": "Z-reversed candidate"},
        "Anev_03": {"split": "train", "group": "anev_g3", "notes": "Duplicate patient scan"},
        "Anev_04": {"split": "train", "group": "anev_g4", "notes": "Duplicate patient scan"},
        "Anev_05": {"split": "train", "group": "anev_g3", "notes": "Duplicate patient scan"},
        "Anev_06": {"split": "val",   "group": "anev_g5", "notes": "Validation baseline scan"},
        "Anev_07": {"split": "train", "group": "anev_g4", "notes": "Duplicate patient scan"},
        "Anev_08": {"split": "train", "group": "anev_g3", "notes": "Duplicate patient scan"},
        "Anev_09": {"split": "test",  "group": "anev_g6", "notes": "Held-out test scan"},
        "Anev_10": {"split": "train", "group": "anev_g3", "notes": "Duplicate patient scan"},
    },
    "Nat": {
        "Nat_01": {"split": "train", "group": "nat_01", "notes": "Slices 138-777; first-half distribution"},
        "Nat_02": {"split": "train", "group": "nat_02", "notes": "Slices 127-752; first-half distribution"},
        "Nat_03": {"split": "train", "group": "nat_03", "notes": "Slices 95-689; first-half distribution"},
        "Nat_04": {"split": "train", "group": "nat_04", "notes": "Slices 115-637; first-half distribution"},
        "Nat_05": {"split": "train", "group": "nat_05", "notes": "Slices 357-906; second-half distribution (inverted orientation)"},
        "Nat_06": {"split": "train", "group": "nat_06", "notes": "Slices 106-721; first-half distribution"},
        "Nat_07": {"split": "train", "group": "nat_07", "notes": "Slices 324-877; second-half distribution (inverted orientation)"},
        "Nat_08": {"split": "val",   "group": "nat_08", "notes": "Slices 122-713; first-half distribution"},
        "Nat_09": {"split": "test",  "group": "nat_09", "notes": "Slices 379-911; second-half distribution (inverted orientation)"},
        "Nat_10": {"split": "test",  "group": "nat_10", "notes": "Slices 115-637; first-half distribution"},
    },
    "Old": {
        "Old_01": {"split": "train", "group": "old_01", "notes": "Z-reversed candidate"},
        "Old_02": {"split": "train", "group": "old_02", "notes": "Z-reversed candidate"},
        "Old_03": {"split": "train", "group": "old_03", "notes": "Z-reversed candidate"},
        "Old_04": {"split": "train", "group": "old_04", "notes": "Metadata matches originally; unchanged array"},
        "Old_05": {"split": "train", "group": "old_05", "notes": "Z-reversed candidate"},
        "Old_06": {"split": "train", "group": "old_06", "notes": "Z-reversed candidate"},
        "Old_07": {"split": "train", "group": "old_07", "notes": "Z-reversed candidate"},
        "Old_08": {"split": "val",   "group": "old_08", "notes": "Z-reversed candidate"},
        "Old_09": {"split": "test",  "group": "old_09", "notes": "Metadata matches originally; unchanged array"},
        "Old_10": {"split": "test",  "group": "old_10", "notes": "Z-reversed candidate"},
    },
    "Dissec": {
        "Dissec_01": {"split": "train", "group": "dissec_01", "notes": "Z-reversed candidate"},
        "Dissec_02": {"split": "train", "group": "dissec_02", "notes": "Z-reversed candidate"},
        "Dissec_03": {"split": "train", "group": "dissec_03", "notes": "Z-reversed candidate"},
        "Dissec_04": {"split": "train", "group": "dissec_04", "notes": "Z-reversed candidate"},
        "Dissec_05": {"split": "train", "group": "dissec_05", "notes": "Z-reversed candidate"},
        "Dissec_06": {"split": "train", "group": "dissec_06", "notes": "Z-reversed candidate"},
        "Dissec_07": {"split": "train", "group": "dissec_07", "notes": "Z-reversed candidate"},
        "Dissec_08": {"split": "val",   "group": "dissec_08", "notes": "Z-reversed candidate"},
        "Dissec_09": {"split": "test",  "group": "dissec_09", "notes": "Held-out test scan"},
        "Dissec_10": {"split": "test",  "group": "dissec_10", "notes": "Held-out test scan"},
    },
    "Ven": {
        "Ven_01": {"split": "train", "group": "ven_01", "notes": "Z-reversed candidate"},
        "Ven_02": {"split": "train", "group": "ven_02", "notes": "Z-reversed candidate"},
        "Ven_03": {"split": "train", "group": "ven_03", "notes": "Z-reversed candidate"},
        "Ven_04": {"split": "train", "group": "ven_04", "notes": "Z-reversed candidate"},
        "Ven_05": {"split": "exclude", "group": "ven_05", "notes": "EXCLUDED: 7-slice shape mismatch (1069 vs 1076)"},
        "Ven_06": {"split": "val",   "group": "ven_06", "notes": "Metadata matches originally; unchanged array"},
        "Ven_07": {"split": "train", "group": "ven_07", "notes": "Z-reversed candidate"},
        "Ven_08": {"split": "train", "group": "ven_08", "notes": "Z-reversed candidate"},
        "Ven_09": {"split": "test",  "group": "ven_09", "notes": "Z-reversed candidate"},
        "Ven_10": {"split": "exclude", "group": "ven_10", "notes": "EXCLUDED: Unresolved 3mm origin mismatch"},
    },
    "Young": {
        "Young_01": {"split": "train", "group": "young_01", "notes": "Z-reversed candidate"},
        "Young_02": {"split": "train", "group": "young_02", "notes": "Z-reversed candidate"},
        "Young_03": {"split": "train", "group": "young_03", "notes": "Z-reversed candidate"},
        "Young_04": {"split": "train", "group": "young_04", "notes": "Z-reversed candidate"},
        "Young_05": {"split": "val",   "group": "young_05", "notes": "Metadata matches originally"},
        "Young_06": {"split": "val",   "group": "young_06", "notes": "Metadata matches originally"},
        "Young_07": {"split": "train", "group": "young_07", "notes": "Z-reversed candidate"},
        "Young_08": {"split": "train", "group": "young_08", "notes": "Metadata matches originally"},
        "Young_09": {"split": "test",  "group": "young_09", "notes": "Z-reversed candidate"},
        "Young_10": {"split": "test",  "group": "young_10", "notes": "Z-reversed candidate"},
    },
}


def build_manifest(data_root, output_csv="data/manifest.csv"):
    """
    Scan data_root for actual NIfTI files and compile a verified manifest.csv.
    """
    root = Path(data_root).resolve()
    rows = []
    missing = []

    for cat, cases in CANONICAL_CASES.items():
        for case_id, meta in cases.items():
            if meta["split"] == "exclude":
                continue

            # Check potential CT locations
            ct_candidates = [
                root / f"{case_id}_image_normalized.nii",
                root / f"{case_id}_image_normalized.nii.gz",
                root / f"{case_id}_image.nii",
                root / f"{case_id}_image.nii.gz",
                root / cat / f"{case_id}_image.nii.gz",
                root / cat / case_id / "nifti" / f"{case_id}_image.nii.gz",
                root / cat / case_id / "nifti" / f"{case_id}_image.nii",
            ]
            found_ct = None
            for p in ct_candidates:
                if p.is_file():
                    found_ct = p
                    break

            # Check potential Mask locations
            mask_candidates = [
                root / f"{case_id}_mask_reversed.nii.gz",
                root / f"{case_id}_candidate_mask.nii.gz",
                root / f"{case_id}_mask.nii.gz",
                root / cat / f"{case_id}_candidate_mask.nii.gz",
                root / cat / case_id / "segmentation" / f"{case_id}_segmentation.nii.gz",
                root / cat / case_id / "segmentation" / f"{case_id}_segmentation.nii",
            ]
            found_mask = None
            for p in mask_candidates:
                if p.is_file():
                    found_mask = p
                    break

            if found_ct and found_mask:
                rows.append({
                    "case_id": case_id,
                    "category": cat,
                    "image_path": str(found_ct),
                    "mask_path": str(found_mask),
                    "split": meta["split"],
                    "leakage_group": meta["group"],
                    "alignment_notes": meta["notes"],
                })
            else:
                missing.append({
                    "case_id": case_id,
                    "category": cat,
                    "ct_found": bool(found_ct),
                    "mask_found": bool(found_mask),
                })

    out_p = Path(output_csv).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with open(out_p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Manifest written with {len(rows)} verified cases -> {out_p}")
    else:
        print(f"No matching file pairs found on disk under {data_root}.")

    print(f"Total eligible cases: 58 (2 excluded)")
    print(f"Cases found: {len(rows)} | Missing: {len(missing)}")
    return rows, missing


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="data")
    parser.add_argument("--output", default="data/manifest.csv")
    args = parser.parse_args()
    build_manifest(args.data_root, args.output)
