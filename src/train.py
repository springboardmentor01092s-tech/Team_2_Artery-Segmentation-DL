"""Train or fine-tune the notebook's Small3DUNet using manifest-defined cases."""
import argparse
import csv
import random
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader

from .dataset import CoroVisionPatchDataset
from .losses import (
    BCEDiceLoss,
    TverskyLoss,
    FocalTverskyLoss,
    dice_score_from_logits,
)
from .model import Small3DUNet


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_checkpoint(model, optimizer, path, device, resume_optimizer=False):
    path = Path(path)
    if path.is_dir():
        import io
        import os
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
            for root, _, files in os.walk(path):
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, path)
                    zf.write(full, f"{path.name}/" + rel.replace(os.sep, "/"))
        buf.seek(0)
        checkpoint = torch.load(buf, map_location=device, weights_only=True)
    else:
        checkpoint = torch.load(path, map_location=device, weights_only=True)
    state = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state, strict=True)
    if resume_optimizer and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--checkpoint", default="checkpoints/best_corovision_3d_unet.pth")
    parser.add_argument("--output", default="checkpoints/corovision_finetuned_best.pth")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--patches-per-case", type=int, default=4)
    parser.add_argument("--val-patches-per-case", type=int, default=1)
    parser.add_argument("--loss", choices=["bce_dice", "tversky", "focal_tversky"], default="bce_dice", help="Loss function (default: bce_dice)")
    parser.add_argument("--resume-optimizer", action="store_true")
    parser.add_argument("--raw-ct", action="store_true", help="Normalize raw HU CT volumes on the fly")
    parser.add_argument("--no-cache", action="store_true", help="Disable in-memory volume caching")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset-best-score", action="store_true",
                        help="Reset best validation score baseline (essential when fine-tuning on a new category/domain)")
    parser.add_argument("--no-amp", action="store_true")
    args = parser.parse_args()

    if args.epochs < 1 or args.batch_size < 1:
        parser.error("--epochs and --batch-size must be positive")
    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda" and not args.no_amp
    print(f"Device: {device} | AMP: {use_amp}")

    train_ds = CoroVisionPatchDataset(
        args.manifest, "train", args.patches_per_case,
        patch_size=(64, 128, 128), foreground_probability=0.7,
        raw_ct=args.raw_ct, cache_in_memory=not args.no_cache,
    )
    # Fixed-seed validation sampling makes patch validation reproducible.
    val_ds = CoroVisionPatchDataset(
        args.manifest, "val", args.val_patches_per_case,
        patch_size=(64, 128, 128), foreground_probability=0.7,
        fixed_seed=args.seed,
        raw_ct=args.raw_ct, cache_in_memory=not args.no_cache,
    )
    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        num_workers=0, pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds, batch_size=1, shuffle=False, num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    model = Small3DUNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    if args.loss == "tversky":
        criterion = TverskyLoss(alpha=0.7, beta=0.3)
    elif args.loss == "focal_tversky":
        criterion = FocalTverskyLoss(alpha=0.7, beta=0.3)
    else:
        criterion = BCEDiceLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    checkpoint_path = Path(args.checkpoint)
    if not (checkpoint_path.is_file() or checkpoint_path.is_dir()):
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_path}. "
            "Check the path; do not train from scratch accidentally."
        )
    previous = load_checkpoint(
        model, optimizer, checkpoint_path, device, args.resume_optimizer
    )
    print("Loaded checkpoint:", checkpoint_path)
    source_epoch = int(previous.get("epoch", 0)) if isinstance(previous, dict) else 0
    saved_val_dice = (
        previous.get("mean_validation_patch_dice",
                     previous.get("validation_patch_dice", -1.0))
        if isinstance(previous, dict) else -1.0
    )
    try:
        saved_val_dice = float(saved_val_dice)
    except (ValueError, TypeError):
        saved_val_dice = -1.0

    print("Source checkpoint epoch:", source_epoch)
    print("Saved validation patch Dice:",
          f"{saved_val_dice:.6f}" if saved_val_dice >= 0 else "not recorded")

    if args.reset_best_score:
        best_dice = -1.0
        print("Resetting best validation score baseline to -1.0 for new domain fine-tuning.")
    else:
        best_dice = saved_val_dice if saved_val_dice >= 0 else -1.0
    start_epoch = source_epoch + 1
    end_epoch = source_epoch + args.epochs
    print(f"Fine-tuning plan: epochs {start_epoch} to {end_epoch} (total {args.epochs} epochs)")
    print(f"Initial best patch Dice baseline: {best_dice:.6f}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    history_path = Path("results/training_history.csv")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history = []

    for epoch in range(start_epoch, end_epoch + 1):
        model.train()
        train_losses = []
        for images, masks, _case_ids in train_loader:
            images, masks = images.to(device), masks.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
                logits = model(images)
                loss = criterion(logits, masks)
            if not torch.isfinite(loss):
                raise RuntimeError("Non-finite loss encountered; stopping safely.")
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            train_losses.append(float(loss.detach().cpu()))

        model.eval()
        val_scores, val_losses = [], []
        with torch.inference_mode():
            for images, masks, _case_ids in val_loader:
                images, masks = images.to(device), masks.to(device)
                with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
                    logits = model(images)
                    val_loss = criterion(logits, masks)
                val_losses.append(float(val_loss.cpu()))
                val_scores.append(dice_score_from_logits(logits.float(), masks))

        train_loss = float(np.mean(train_losses))
        val_loss = float(np.mean(val_losses))
        val_dice = float(np.mean(val_scores))
        row = {
            "epoch": epoch, "train_loss": train_loss,
            "validation_patch_loss": val_loss,
            "mean_validation_patch_dice": val_dice,
            "learning_rate": optimizer.param_groups[0]["lr"],
        }
        history.append(row)
        print(
            f"Epoch {epoch}/{end_epoch} | train_loss={train_loss:.4f} | "
            f"val_loss={val_loss:.4f} | val_patch_dice={val_dice:.4f}"
        )

        if val_dice > best_dice:
            best_dice = val_dice
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "mean_validation_patch_dice": val_dice,
                "validation_patch_loss": val_loss,
                "source_checkpoint": str(checkpoint_path),
                "training_config": vars(args),
            }, out_path)
            print(f"Saved new best checkpoint (improved patch Dice to {best_dice:.6f}):", out_path)

    with history_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)
    print("Training history:", history_path)
    print("Best validation patch Dice:", best_dice)
    print("Reminder: patch Dice is not whole-volume Dice.")


if __name__ == "__main__":
    main()
