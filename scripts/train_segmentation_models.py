"""Train and compare Tiny U-Net and Attention U-Net on official ARCADE splits.

Only official train/val images are used for fitting and model selection. The
official test split is never read by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.analysis_model import MODEL_SIZE, build_attention_unet, build_model, prepare_input, prepare_mask  # noqa: E402


class ArcadePairs(Dataset):
    def __init__(self, task: str, split: str, training: bool = False, input_size: int = MODEL_SIZE):
        self.training = training
        self.input_size = input_size
        root = ROOT / "data" / "processed" / "arcade" / task / split
        images = sorted((root / "images").glob("*.png"))
        self.excluded_train_duplicates: list[str] = []
        if split == "train":
            raw_root = ROOT / "arcade" / task
            images, self.excluded_train_duplicates = exclude_training_validation_duplicates(
                images,
                raw_root / "train" / "images",
                raw_root / "val" / "images",
            )
        self.pairs = [(path, root / "masks" / path.name) for path in images
                      if (root / "masks" / path.name).is_file()]
        if not self.pairs:
            raise RuntimeError(f"No prepared {task}/{split} image-mask pairs found")

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, index):
        image_path, mask_path = self.pairs[index]
        image = torch.from_numpy(prepare_input(image_path, self.input_size))
        mask = torch.from_numpy(prepare_mask(mask_path, self.input_size))
        if self.training:
            # Small affine changes are applied identically to images and masks.
            import math
            angle = math.radians(random.uniform(-10, 10))
            scale = random.uniform(0.92, 1.08)
            tx, ty = random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04)
            theta = torch.tensor([[[scale * math.cos(angle), -scale * math.sin(angle), tx],
                                   [scale * math.sin(angle), scale * math.cos(angle), ty]]], dtype=image.dtype)
            grid = torch.nn.functional.affine_grid(theta, (1, 1, self.input_size, self.input_size), align_corners=False)
            image = torch.nn.functional.grid_sample(image[None], grid, mode="bilinear", padding_mode="zeros", align_corners=False)[0]
            mask = torch.nn.functional.grid_sample(mask[None], grid, mode="nearest", padding_mode="zeros", align_corners=False)[0]
            if random.random() < 0.5:
                image = (image * random.uniform(0.9, 1.1) + random.uniform(-0.04, 0.04)).clamp(0, 1)
        return image, mask


def _pixel_digest(path: Path) -> str:
    """Hash decoded RGB pixels so alternate PNG encodings still match."""
    with Image.open(path) as opened:
        image = opened.convert("RGB")
        digest = hashlib.sha256()
        digest.update(f"{image.width}x{image.height}:RGB:".encode())
        digest.update(image.tobytes())
        return digest.hexdigest()


def exclude_training_validation_duplicates(processed_training_images: list[Path],
                                           raw_training_images: Path,
                                           raw_validation_images: Path) -> tuple[list[Path], list[str]]:
    """Drop exact pixel duplicates from train while retaining every official val item."""
    image_suffixes = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    validation_digests = {
        _pixel_digest(path) for path in raw_validation_images.glob("*")
        if path.is_file() and path.suffix.lower() in image_suffixes
    }
    kept, excluded = [], []
    for processed_path in processed_training_images:
        raw_path = raw_training_images / processed_path.name
        if raw_path.is_file() and _pixel_digest(raw_path) in validation_digests:
            excluded.append(processed_path.name)
        else:
            kept.append(processed_path)
    return kept, sorted(excluded)

def dataset(task: str, split: str, training: bool, input_size: int = MODEL_SIZE):
    return ArcadePairs(task, split, training, input_size)


def score(model, loader, device, positive_weight,
          thresholds=(0.10, 0.15, 0.20, 0.25, 0.35, 0.50, 0.65, 0.75)):
    model.eval()
    counts = {threshold: [0, 0, 0, 0] for threshold in thresholds}
    image_f1 = {threshold: [] for threshold in thresholds}
    positive_hist = np.zeros(256, dtype=np.int64)
    negative_hist = np.zeros(256, dtype=np.int64)
    validation_loss = 0.0
    validation_examples = 0
    with torch.inference_mode():
        for images, masks in loader:
            logits = model(images.to(device))
            targets = masks.to(device)
            batch_loss = nn.functional.binary_cross_entropy_with_logits(logits, targets,
                        pos_weight=torch.tensor(positive_weight, device=device)) + dice_loss(logits, targets)
            validation_loss += float(batch_loss.item()) * len(images)
            validation_examples += len(images)
            probability_batch = logits.sigmoid().cpu().numpy()[:, 0]
            target_batch = (masks >= 0.5).cpu().numpy()[:, 0]
            probabilities = probability_batch.reshape(-1)
            target = target_batch.reshape(-1)
            positive_hist += np.histogram(probabilities[target], bins=256, range=(0, 1))[0]
            negative_hist += np.histogram(probabilities[~target], bins=256, range=(0, 1))[0]
            for threshold, values in counts.items():
                pred_batch = probability_batch >= threshold
                for prediction, truth in zip(pred_batch, target_batch):
                    tp_i = int(np.count_nonzero(prediction & truth))
                    fp_i = int(np.count_nonzero(prediction & ~truth))
                    fn_i = int(np.count_nonzero(~prediction & truth))
                    image_f1[threshold].append(2 * tp_i / max(2 * tp_i + fp_i + fn_i, 1))
                predictions = pred_batch.reshape(-1)
                values[0] += int(np.count_nonzero(predictions & target))
                values[1] += int(np.count_nonzero(predictions & ~target))
                values[2] += int(np.count_nonzero(~predictions & target))
                values[3] += int(np.count_nonzero(~predictions & ~target))
    tpr = np.r_[0.0, np.cumsum(positive_hist[::-1]) / max(positive_hist.sum(), 1)]
    fpr = np.r_[0.0, np.cumsum(negative_hist[::-1]) / max(negative_hist.sum(), 1)]
    auc_roc = float(np.sum(np.diff(fpr) * (tpr[1:] + tpr[:-1]) / 2))
    results = {}
    for threshold, (tp, fp, fn, tn) in counts.items():
        denominator = max(tp + fp + fn, 1)
        results[threshold] = {
            "threshold": threshold,
            "dice": round(2 * tp / max(2 * tp + fp + fn, 1), 4),
            "iou": round(tp / denominator, 4),
            "precision": round(tp / max(tp + fp, 1), 4),
            "recall": round(tp / max(tp + fn, 1), 4),
            "sensitivity": round(tp / max(tp + fn, 1), 4),
            "f1": round(2 * tp / max(2 * tp + fp + fn, 1), 4),
            "specificity": round(tn / max(tn + fp, 1), 4),
            "pixel_accuracy": round((tp + tn) / max(tp + fp + fn + tn, 1), 4),
            "auc_roc": round(auc_roc, 4),
            "mean_image_pixel_f1": round(float(np.mean(image_f1[threshold])), 4),
            "std_image_pixel_f1": round(float(np.std(image_f1[threshold])), 4),
            "validation_loss": round(validation_loss / max(validation_examples, 1), 4),
            "pixels": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        }
        row = results[threshold]
        row["selection_score"] = round(float(np.mean([
            row["pixel_accuracy"], row["precision"], row["recall"], row["f1"],
            row["auc_roc"], row["dice"], row["iou"], row["sensitivity"], row["specificity"],
        ])), 4)
    return max(results.values(), key=lambda row: row["selection_score"])


def dice_loss(logits, targets):
    probabilities = logits.sigmoid()
    intersection = (probabilities * targets).sum(dim=(1, 2, 3))
    denominator = probabilities.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
    return (1 - (2 * intersection + 1) / (denominator + 1)).mean()


def train_one(task: str, architecture: str, args, device):
    training = dataset(task, "train", True, args.input_size)
    validation = dataset(task, "val", False, args.input_size)
    train_loader = DataLoader(training, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(validation, batch_size=args.batch_size, num_workers=0)
    # Estimate a capped positive-class weight from train masks only. The cap
    # avoids letting a few tiny masks dominate optimization.
    positive_pixels = negative_pixels = 0
    for _, mask_path in training.pairs:
        mask = prepare_mask(mask_path, args.input_size)
        positive_pixels += int((mask >= 0.5).sum())
        negative_pixels += int((mask < 0.5).sum())
    positive_weight = min(20.0, max(1.0, (negative_pixels / max(positive_pixels, 1)) ** 0.5))
    model = (build_attention_unet() if architecture == "attention_unet" else build_model()).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2,
                                                           threshold=0.001, min_lr=args.learning_rate / 16)
    output = args.output_root / task
    output.mkdir(parents=True, exist_ok=True)
    best_selection_score, best_metrics, history = -1.0, {}, []
    stale_epochs = 0
    stopped_early = False
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    for epoch in range(args.epochs):
        epoch_started = time.perf_counter()
        model.train()
        total_loss = 0.0
        for images, masks in train_loader:
            images, masks = images.to(device), masks.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = nn.functional.binary_cross_entropy_with_logits(
                logits, masks, pos_weight=torch.tensor(positive_weight, device=device)) + dice_loss(logits, masks)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
        metrics = score(model, val_loader, device, positive_weight)
        row = {"epoch": epoch + 1, "train_loss": round(total_loss / max(len(train_loader), 1), 4),
               "learning_rate": optimizer.param_groups[0]["lr"],
               "epoch_seconds": round(time.perf_counter() - epoch_started, 2), **metrics}
        history.append(row)
        print(task, architecture, row, flush=True)
        scheduler.step(metrics["selection_score"])
        if metrics["selection_score"] > best_selection_score:
            best_selection_score, best_metrics = metrics["selection_score"], metrics
            stale_epochs = 0
            torch.save(model.state_dict(), output / f"{architecture}.pt")
        else:
            stale_epochs += 1
            if stale_epochs >= args.early_stopping_patience:
                stopped_early = True
                break
    report = {
        "task": task, "architecture": architecture, "input_size": args.input_size,
        "model_version": f"arcade-{architecture}-{args.run_id}",
        "training_run_id": args.run_id,
        "train_images": len(training), "validation_images": len(validation),
        "training_duplicates_excluded_against_validation": training.excluded_train_duplicates,
        "epochs_requested": args.epochs, "epochs_completed": len(history), "stopped_early": stopped_early,
        "early_stopping_patience": args.early_stopping_patience,
        "scheduler": "ReduceLROnPlateau on validation composite metric score", "seed": args.seed,
        "learning_rate": args.learning_rate, "batch_size": args.batch_size,
        "class_imbalance_strategy": "train-mask-derived capped square-root positive BCE weight plus Dice loss",
        "positive_class_weight": round(positive_weight, 4),
        "peak_cuda_memory_mib": round(torch.cuda.max_memory_allocated() / (1024 ** 2), 1) if device == "cuda" else None,
        "mask_semantics": "binary union of annotated vessel regions; not ARCADE instance/category labels",
        "checkpoint_selection_metric": "unweighted mean of validation accuracy, precision, recall, F1, AUC-ROC, Dice, IoU, sensitivity, and specificity (binary pixel proxy; not official ARCADE instance F1)",
        "threshold": best_metrics["threshold"],
        "best_validation": best_metrics, "history": history,
        "dataset": "ARCADE official train/validation splits",
        "test_split_used": False, "clinical_validation": False,
    }
    (output / f"{architecture}_report.json").write_text(json.dumps(report, indent=2))
    return report


def run_overfit_check(task: str, input_size: int, device: str, steps: int = 200) -> tuple[float, float]:
    """Debug labels, finite gradients, optimizer updates, and learnability on two fixed examples."""
    fixed = dataset(task, "train", False, input_size)
    images, masks = zip(*(fixed[index] for index in range(min(2, len(fixed)))))
    images, masks = torch.stack(images).to(device), torch.stack(masks).to(device)
    positives = int((masks >= 0.5).sum())
    negatives = int((masks < 0.5).sum())
    positive_weight = min(20.0, max(1.0, (negatives / max(positives, 1)) ** 0.5))
    model = build_model().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    def current_loss():
        logits = model(images)
        return nn.functional.binary_cross_entropy_with_logits(
            logits, masks, pos_weight=torch.tensor(positive_weight, device=device)) + dice_loss(logits, masks)

    model.eval()
    with torch.no_grad():
        initial = float(current_loss().item())
    model.train()
    gradient_norm = None
    parameter_changed = False
    for step in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = current_loss()
        if not torch.isfinite(loss):
            raise RuntimeError(f"Tiny-subset loss became non-finite for {task}")
        loss.backward()
        if step == 0:
            grads = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
            if not grads or not all(torch.isfinite(grad).all() for grad in grads):
                raise RuntimeError(f"Tiny-subset gradients are missing or non-finite for {task}")
            gradient_norm = float(torch.sqrt(sum(torch.sum(grad.detach() ** 2) for grad in grads)).item())
            before = [parameter.detach().clone() for parameter in model.parameters()]
        optimizer.step()
        if step == 0:
            parameter_changed = any(not torch.equal(previous, current.detach())
                                    for previous, current in zip(before, model.parameters()))
            if not parameter_changed:
                raise RuntimeError(f"Optimizer did not update model parameters for {task}")
    model.eval()
    with torch.no_grad():
        final = float(current_loss().item())
    print(f"overfit-check {task}: fixed 2-image loss {initial:.4f} -> {final:.4f} "
          f"in {steps} steps; gradient_norm={gradient_norm:.4f}; parameter_changed={parameter_changed}", flush=True)
    if not final <= initial * 0.8:
        raise RuntimeError(f"Tiny-subset overfit check failed for {task}; inspect masks, model, and loss")
    return initial, final


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=("syntax", "stenosis", "both"), default="both")
    parser.add_argument("--architectures", nargs="+", choices=("tiny_unet", "attention_unet"),
                        default=("tiny_unet", "attention_unet"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--input-size", type=int, default=512,
                        help="Square training size (multiple of 32; 128–512)")
    parser.add_argument("--learning-rate", type=float, default=0.0002)
    parser.add_argument("--early-stopping-patience", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                        help="Unique UTC identifier recorded with every checkpoint and report")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Experiment output directory (default: models/segmentation/experiments/<run-id>)")
    parser.add_argument("--overfit-check", action="store_true",
                        help="Run a fixed two-image train-only gradient/optimizer/learnability check and exit")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.early_stopping_patience < 1:
        parser.error("epochs, batch-size, and early-stopping-patience must be positive")
    if args.input_size < 128 or args.input_size > 512 or args.input_size % 32:
        parser.error("input-size must be a multiple of 32 between 128 and 512")
    args.output_root = args.output_dir or (ROOT / "models" / "segmentation" / "experiments" / args.run_id)
    if not args.output_root.is_absolute():
        args.output_root = ROOT / args.output_root
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    print("device", device, flush=True)
    tasks = ("syntax", "stenosis") if args.task == "both" else (args.task,)
    if args.overfit_check:
        for task in tasks:
            run_overfit_check(task, args.input_size, device)
        return
    results = [train_one(task, architecture, args, device)
               for task in tasks for architecture in args.architectures]
    output = args.output_root / "comparison_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    by_architecture = {}
    dice_by_architecture = {}
    for architecture in args.architectures:
        rows = [row for row in results if row["architecture"] == architecture]
        if len(rows) == len(tasks):
            by_architecture[architecture] = round(sum(row["best_validation"]["selection_score"] for row in rows) / len(rows), 4)
            dice_by_architecture[architecture] = round(sum(row["best_validation"]["dice"] for row in rows) / len(rows), 4)
    promoted = max(by_architecture, key=by_architecture.get) if by_architecture else None
    report = {"experiments": results,
              "selection_metric": "mean task validation composite across pixel accuracy, precision, recall, F1, AUC-ROC, Dice, IoU, sensitivity, and specificity (binary mask proxy; not official ARCADE instance F1)",
              "selection_metric_components": ["pixel_accuracy", "precision", "recall", "f1", "auc_roc", "dice", "iou", "sensitivity", "specificity"],
              "architecture_mean_validation_composite_score": by_architecture,
              "architecture_mean_validation_image_f1": {architecture: round(sum(row["best_validation"]["mean_image_pixel_f1"] for row in results if row["architecture"] == architecture) / max(sum(row["architecture"] == architecture for row in results), 1), 4) for architecture in args.architectures},
              "architecture_mean_validation_dice": dice_by_architecture,
              "selected_architecture": promoted, "input_size": args.input_size,
              "mask_semantics": "binary union of annotated vessel regions; not ARCADE instance/category labels",
              "test_split_used": False, "clinical_validation": False}
    output.write_text(json.dumps(report, indent=2))
    if promoted and set(tasks) == {"syntax", "stenosis"}:
        (output.parent / "promoted_model.json").write_text(json.dumps({
            "architecture": promoted,
            "version": next(row["model_version"] for row in results if row["architecture"] == promoted),
            "training_run_id": args.run_id,
            "selection_metric": report["selection_metric"],
            "selection_metric_components": report["selection_metric_components"],
            "input_size": args.input_size,
            "validation_composite_score_by_architecture": by_architecture,
            "validation_image_f1_by_architecture": report["architecture_mean_validation_image_f1"],
            "validation_dice_by_architecture": dice_by_architecture,
            "thresholds": {row["task"]: row["threshold"] for row in results if row["architecture"] == promoted},
            "test_split_used": False, "clinical_validation": False,
        }, indent=2))


if __name__ == "__main__":
    main()
