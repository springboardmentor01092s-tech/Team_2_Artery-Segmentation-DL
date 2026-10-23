"""Train independent binary artery and stenosis U-Net research baselines."""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.analysis_model import MODEL_SIZE, build_model, prepare_input, prepare_mask  # noqa: E402


class ArcadePairs(Dataset):
    def __init__(self, task: str, split: str, limit: int | None):
        root = ROOT / "data" / "processed" / "arcade" / task / split
        pairs = [(p, root / "masks" / p.name) for p in sorted((root / "images").glob("*.png"))]
        pairs = [(image, mask) for image, mask in pairs if mask.exists()]
        if task == "stenosis" and split == "val":
            # Exact duplicate of train image 218; exclude it from validation.
            pairs = [(image, mask) for image, mask in pairs if image.stem != "155"]
        if limit is not None:
            pairs = pairs[:limit]
        if not pairs:
            raise RuntimeError(f"No prepared {task}/{split} image-mask pairs found")
        self.pairs = pairs

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, index):
        image, mask = self.pairs[index]
        return torch.from_numpy(prepare_input(image)), torch.from_numpy(prepare_mask(mask))


def dice_loss(logits, targets):
    probabilities = logits.sigmoid()
    intersection = (probabilities * targets).sum(dim=(1, 2, 3))
    denominator = probabilities.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
    return (1 - (2 * intersection + 1) / (denominator + 1)).mean()


def metrics(model, loader, device):
    model.eval()
    intersection = prediction_sum = target_sum = 0
    with torch.no_grad():
        for images, masks in loader:
            prediction = (model(images.to(device)).sigmoid() >= 0.5).cpu()
            intersection += (prediction * masks).sum().item()
            prediction_sum += prediction.sum().item()
            target_sum += masks.sum().item()
    return {"dice": round((2 * intersection + 1) / (prediction_sum + target_sum + 1), 4),
            "iou": round((intersection + 1) / (prediction_sum + target_sum - intersection + 1), 4)}


def train(task: str, args, device):
    training = ArcadePairs(task, "train", args.max_train)
    validation = ArcadePairs(task, "val", args.max_val)
    train_loader = DataLoader(training, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(validation, batch_size=args.batch_size, num_workers=0)
    model = build_model().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    best = -1.0
    output_dir = ROOT / "models" / "baseline"
    output_dir.mkdir(parents=True, exist_ok=True)
    history = []
    for epoch in range(args.epochs):
        model.train()
        loss_sum = 0.0
        for images, masks in train_loader:
            images, masks = images.to(device), masks.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = nn.functional.binary_cross_entropy_with_logits(logits, masks) + dice_loss(logits, masks)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item()
        score = metrics(model, val_loader, device)
        row = {"epoch": epoch + 1, "loss": round(loss_sum / len(train_loader), 4), **score}
        history.append(row)
        print(task, row, flush=True)
        if score["dice"] > best:
            best = score["dice"]
            torch.save(model.cpu().state_dict(), output_dir / f"{task}.pt")
            model.to(device)
    return {"task": task, "architecture": "tiny_unet", "input_size": MODEL_SIZE,
            "train_images": len(training), "validation_images": len(validation), "best_validation_dice": best,
            "epochs": args.epochs, "seed": args.seed, "history": history,
            "threshold": 0.5, "source": "ARCADE official train/validation splits",
            "clinical_validation": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--max-train", type=int, default=400)
    parser.add_argument("--max-val", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print("device", device, flush=True)
    reports = [train(task, args, device) for task in ("syntax", "stenosis")]
    (ROOT / "models" / "baseline" / "training_report.json").write_text(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
