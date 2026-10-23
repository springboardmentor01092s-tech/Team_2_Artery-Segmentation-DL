"""Train a lightweight two-hidden-layer neural pixel-mask baseline on ARCADE."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from app.analysis_model import prepare_mask  # noqa: E402
from app.pixel_mlp import pixel_features  # noqa: E402
from ml.preprocessing.model_input import augment_training_pair  # noqa: E402


def pairs(task: str, split: str, limit: int):
    root = ROOT / "data" / "processed" / "arcade" / task / split
    images = sorted((root / "images").glob("*.png"))
    if task == "stenosis" and split == "val":
        images = [image for image in images if image.stem != "155"]
    output = [(image, root / "masks" / image.name) for image in images[:limit]]
    if not output or any(not mask.exists() for _, mask in output):
        raise RuntimeError(f"Missing prepared {task}/{split} pairs")
    return output


def dice(predicted, truth):
    intersection = np.logical_and(predicted, truth).sum()
    return 2 * intersection, predicted.sum() + truth.sum()


def train(task: str, args, rng):
    training = pairs(task, "train", args.train_images)
    validation = pairs(task, "val", args.validation_images)
    x_parts, y_parts = [], []
    for index, (image, mask_path) in enumerate(training):
        samples = [(image, mask_path)]
        if args.augment:
            with Image.open(image) as source, Image.open(mask_path) as label:
                rotated = augment_training_pair(source.convert("L"), label.convert("L"),
                                                seed=args.seed + index + (10000 if task == "stenosis" else 0))
                samples.append(rotated)
        for sample_image, sample_mask in samples:
            features = pixel_features(sample_image)
            mask = prepare_mask(sample_mask).ravel().astype(np.uint8)
            positive = np.flatnonzero(mask)
            negative = np.flatnonzero(1 - mask)
            indices = [rng.choice(negative, args.samples_per_class, replace=len(negative) < args.samples_per_class)]
            if len(positive):
                indices.append(rng.choice(positive, args.samples_per_class, replace=len(positive) < args.samples_per_class))
            chosen = np.concatenate(indices)
            x_parts.append(features[chosen])
            y_parts.append(mask[chosen])
    x = np.concatenate(x_parts)
    y = np.concatenate(y_parts)
    if len(np.unique(y)) != 2:
        raise RuntimeError(f"{task} training sample has only one class")
    scaler = StandardScaler().fit(x)
    model = MLPClassifier(hidden_layer_sizes=(32, 16), activation="relu", solver="adam",
                          batch_size=256, max_iter=args.iterations, random_state=args.seed,
                          early_stopping=True, n_iter_no_change=4)
    model.fit(scaler.transform(x), y)
    scores = {threshold: [0, 0] for threshold in (0.5, 0.65, 0.8, 0.9, 0.95)}
    for image, mask_path in validation:
        probabilities = model.predict_proba(scaler.transform(pixel_features(image)))[:, 1]
        truth = prepare_mask(mask_path).ravel().astype(bool)
        for threshold in scores:
            numerator, denominator = dice(probabilities >= threshold, truth)
            scores[threshold][0] += numerator
            scores[threshold][1] += denominator
    validation_dice = {threshold: numerator / max(denominator, 1) for threshold, (numerator, denominator) in scores.items()}
    threshold = max(validation_dice, key=validation_dice.get)
    output = ROOT / "models" / "baseline"
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / f"{task}.npz", mean=scaler.mean_.astype(np.float32),
                        scale=scaler.scale_.astype(np.float32), threshold=np.float32(threshold),
                        **{f"coef{i}": value.astype(np.float32) for i, value in enumerate(model.coefs_)},
                        **{f"intercept{i}": value.astype(np.float32) for i, value in enumerate(model.intercepts_)})
    report = {"task": task, "model_version": "arcade-pixel-mlp-v2", "architecture": "pixel_mlp_32_16", "train_images": len(training),
              "validation_images": len(validation), "training_pixels": len(y), "iterations": model.n_iter_,
              "threshold": threshold, "best_validation_dice": round(validation_dice[threshold], 4),
              "validation_dice_by_threshold": validation_dice, "seed": args.seed,
              "training_rotation_augmentation": args.augment,
              "clinical_validation": False}
    print(json.dumps(report), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-images", type=int, default=100)
    parser.add_argument("--validation-images", type=int, default=30)
    parser.add_argument("--samples-per-class", type=int, default=160)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-augment", action="store_false", dest="augment")
    parser.set_defaults(augment=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    reports = [train(task, args, rng) for task in ("syntax", "stenosis")]
    output = ROOT / "models" / "baseline"
    (output / "training_report_mlp.json").write_text(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
