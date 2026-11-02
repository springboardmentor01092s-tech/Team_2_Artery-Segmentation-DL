"""
Training Pipeline for Baseline U-Net and Attention Residual U-Net.
"""

import os
import sys
import tempfile
os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_cache")
import json
import time
import argparse
import yaml
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.unet import BaselineUNet
from models.attention_resunet import AttentionResUNet
from src.preprocess import get_dataloaders


class DiceBCELoss(nn.Module):
    """Combined Binary Cross-Entropy and Soft Dice Loss."""

    def __init__(self, bce_weight: float = 0.5, dice_weight: float = 0.5, smooth: float = 1e-6):
        super().__init__()
        self.bce_weight, self.dice_weight, self.smooth = bce_weight, dice_weight, smooth
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = self.bce(logits, targets)
        p, t = torch.sigmoid(logits).reshape(-1), targets.reshape(-1)
        intersection = (p * t).sum()
        dice = (2.0 * intersection + self.smooth) / (p.sum() + t.sum() + self.smooth)
        return self.bce_weight * bce + self.dice_weight * (1.0 - dice)


def compute_metrics(logits: torch.Tensor, targets: torch.Tensor, smooth: float = 1e-6):
    """Computes batch Dice score and IoU on binarized predictions."""
    p = (torch.sigmoid(logits) > 0.5).float().reshape(-1)
    t = targets.reshape(-1)
    intersection = (p * t).sum()
    dice = (2.0 * intersection + smooth) / (p.sum() + t.sum() + smooth)
    iou = (intersection + smooth) / (p.sum() + t.sum() - intersection + smooth)
    return dice.item(), iou.item()


def build_model(model_name: str, config: dict, device: torch.device):
    """Factory to instantiate Baseline U-Net or Attention ResU-Net."""
    in_ch = config["dataset"].get("in_channels", 1)
    num_cls = config["dataset"].get("num_classes", 1)
    name_lower = model_name.lower()

    if "att" in name_lower or "res" in name_lower:
        feats = config["models"]["attention_resunet"].get("features", [32, 64, 128, 256, 512])
        model, display_name = AttentionResUNet(in_ch, num_cls, feats), "Attention_ResUNet"
    else:
        feats = config["models"]["baseline_unet"].get("features", [32, 64, 128, 256, 512])
        model, display_name = BaselineUNet(in_ch, num_cls, feats), "Baseline_UNet"

    return model.to(device), display_name


def _run_epoch(model, loader, criterion, optimizer, device, is_train=True):
    """Executes a single train or validation pass across all batches."""
    model.train() if is_train else model.eval()
    loss_acc, dice_acc, iou_acc = 0.0, 0.0, 0.0

    with torch.set_grad_enabled(is_train):
        for imgs, masks, _ in loader:
            imgs, masks = imgs.to(device), masks.to(device)
            if is_train:
                optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, masks)
            if is_train:
                loss.backward()
                optimizer.step()

            d, j = compute_metrics(logits, masks)
            loss_acc += loss.item()
            dice_acc += d
            iou_acc += j

    n = len(loader)
    return loss_acc / n, dice_acc / n, iou_acc / n


def train_single_model(model_name: str, config_path: str = "config.yaml"):
    """Executes complete training loop for the specified architecture."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    seed = cfg["training"].get("seed", 42)
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    dev_str = cfg["training"].get("device", "cuda")
    device = torch.device(dev_str if (torch.cuda.is_available() and dev_str == "cuda") else "cpu")
    print(f"\nTraining {model_name} on {device}...")

    train_loader, val_loader, _, _ = get_dataloaders(config_path)
    model, display_name = build_model(model_name, cfg, device)

    criterion = DiceBCELoss(bce_weight=0.5, dice_weight=0.5)
    lr = float(cfg["training"].get("learning_rate", 0.001))
    weight_decay = float(cfg["training"].get("weight_decay", 0.0001))
    optimizer = Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=4)

    epochs = cfg["training"].get("epochs", 35)
    patience = cfg["training"].get("early_stopping_patience", 10)
    ckpt_dir, rpt_dir = cfg["paths"]["checkpoints_dir"], cfg["paths"]["reports_dir"]
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(rpt_dir, exist_ok=True)
    ckpt_path = os.path.join(ckpt_dir, f"best_{display_name}.pth")

    history = {k: [] for k in ["epoch", "train_loss", "train_dice", "train_iou", "val_loss", "val_dice", "val_iou", "lr"]}
    best_val_dice, no_improve = -1.0, 0
    t0 = time.time()

    for epoch in range(1, epochs + 1):
        tr_loss, tr_dice, tr_iou = _run_epoch(model, train_loader, criterion, optimizer, device, is_train=True)
        val_loss, val_dice, val_iou = _run_epoch(model, val_loader, criterion, optimizer, device, is_train=False)

        cur_lr = optimizer.param_groups[0]["lr"]
        scheduler.step(val_dice)

        for k, v in [("epoch", epoch), ("train_loss", round(tr_loss, 4)), ("train_dice", round(tr_dice, 4)),
                     ("train_iou", round(tr_iou, 4)), ("val_loss", round(val_loss, 4)),
                     ("val_dice", round(val_dice, 4)), ("val_iou", round(val_iou, 4)), ("lr", cur_lr)]:
            history[k].append(v)

        marker = ""
        if val_dice > best_val_dice:
            best_val_dice, no_improve = val_dice, 0
            torch.save({
                "epoch": epoch, "model_name": display_name,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_dice": val_dice, "val_iou": val_iou, "config": cfg
            }, ckpt_path)
            marker = " [* Best Saved]"
        else:
            no_improve += 1

        print(f"Epoch [{epoch:02d}/{epochs:02d}] Train Loss: {tr_loss:.4f} | Train Dice: {tr_dice:.4f} | "
              f"Val Loss: {val_loss:.4f} | Val Dice: {val_dice:.4f} | Val IoU: {val_iou:.4f} (lr: {cur_lr:.1e}){marker}")

        if no_improve >= patience:
            print(f"[Early Stopping] Triggered at epoch {epoch}.")
            break

    print(f"Completed {display_name} in {time.time() - t0:.1f}s. Best Val Dice: {best_val_dice:.4f}")
    with open(os.path.join(rpt_dir, f"history_{display_name}.json"), "w") as fp:
        json.dump(history, fp, indent=2)

    plot_training_curves(history, display_name, rpt_dir)
    return ckpt_path, history


def plot_training_curves(history: dict, model_name: str, reports_dir: str):
    """Saves loss and dice learning curves."""
    epochs = history["epoch"]
    for title, metric_keys, colors, ylabel, fname in [
        (f"{model_name} - Loss vs Epochs", [("train_loss", "Train Loss", "-"), ("val_loss", "Val Loss", "--")],
         ["#1f77b4", "#d62728"], "Loss (Dice + BCE)", f"{model_name}_loss_curve.png"),
        (f"{model_name} - Dice & IoU vs Epochs", [("train_dice", "Train Dice", "-"), ("val_dice", "Val Dice", "--"), ("val_iou", "Val IoU", ":")],
         ["#2ca02c", "#1f77b4", "#ff7f0e"], "Metric Score", f"{model_name}_dice_curve.png"),
    ]:
        plt.figure(figsize=(7, 5))
        for (k, label, ls), c in zip(metric_keys, colors):
            plt.plot(epochs, history[k], label=label, color=c, linestyle=ls, linewidth=2)
        plt.title(title, fontsize=13, fontweight="bold")
        plt.xlabel("Epoch")
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.savefig(os.path.join(reports_dir, fname), dpi=200, bbox_inches="tight")
        plt.close()


def train_both_models(config_path: str = "config.yaml"):
    """Trains Baseline U-Net followed by Attention ResU-Net."""
    train_single_model("Baseline_UNet", config_path)
    train_single_model("Attention_ResUNet", config_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="both", choices=["unet", "attention_resunet", "both"])
    parser.add_argument("--config", type=str, default="config.yaml")
    args = parser.parse_args()
    if args.model == "both":
        train_both_models(args.config)
    else:
        train_single_model(args.model, args.config)
