"""Offline, CPU-only volume preparation; never starts model training."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np
import SimpleITK as sitk
from app.volume_preprocessing import read_volume, prepare_volume, augment_training_volume


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="NIfTI or one de-identified DICOM series directory")
    parser.add_argument("output", type=Path, help="New output directory; never overwrites")
    parser.add_argument("--mask", type=Path)
    parser.add_argument("--reference", type=Path, help="Opt-in fixed reference for rigid registration")
    parser.add_argument("--spacing", type=float, nargs=3, metavar=("X", "Y", "Z"))
    parser.add_argument("--roi", type=int, nargs=6)
    parser.add_argument("--slice-axis", type=int, choices=[0, 1, 2], default=2)
    parser.add_argument("--slice-index", type=int)
    parser.add_argument("--denoise", action="store_true")
    parser.add_argument("--enhance", action="store_true")
    parser.add_argument("--augment-training-seed", type=int)
    parser.add_argument("--split", choices=["train", "validation", "test"], default="test")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output directory already exists; choose a new path")
    if args.augment_training_seed is not None and (args.split != "train" or args.mask is None):
        parser.error("Augmentation requires --split train and an aligned --mask")
    image, mask, tensor, selected, record, transform = prepare_volume(
        read_volume(args.source), mask=read_volume(args.mask) if args.mask else None,
        reference=read_volume(args.reference) if args.reference else None,
        spacing=args.spacing, roi=args.roi, denoise=args.denoise, enhance=args.enhance,
        slice_axis=args.slice_axis, slice_index=args.slice_index)
    args.output.mkdir(parents=True)
    sitk.WriteImage(image, str(args.output / "prepared.nii.gz"))
    if mask is not None:
        sitk.WriteImage(mask, str(args.output / "prepared_mask.nii.gz"))
    if transform is not None:
        sitk.WriteTransform(transform, str(args.output / "registration.tfm"))
    np.save(args.output / "model_input_czyx.npy", tensor, allow_pickle=False)
    np.save(args.output / "selected_slice_chw.npy", selected, allow_pickle=False)
    if args.augment_training_seed is not None:
        augmented, augmented_mask = augment_training_volume(image, mask, seed=args.augment_training_seed, split=args.split)
        sitk.WriteImage(augmented, str(args.output / "augmented_train.nii.gz"))
        sitk.WriteImage(augmented_mask, str(args.output / "augmented_train_mask.nii.gz"))
        record["augmentation"] = {"seed": args.augment_training_seed, "split": args.split,
                                  "image_interpolation": "linear", "mask_interpolation": "nearest"}
    source_files = sorted(args.source.iterdir()) if args.source.is_dir() else [args.source]
    record["source_sha256"] = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files if p.is_file()}
    record["source_files_unchanged"] = True
    (args.output / "processing_record.json").write_text(json.dumps(record, indent=2))
    print(args.output / "processing_record.json")


if __name__ == "__main__":
    main()
