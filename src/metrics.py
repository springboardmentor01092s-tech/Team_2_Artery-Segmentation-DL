"""Binary segmentation metrics."""
import numpy as np


def binary_metrics(prediction, target, eps=1e-8):
    pred = np.asarray(prediction, dtype=bool)
    gt = np.asarray(target, dtype=bool)
    if pred.shape != gt.shape:
        raise ValueError(f"Prediction/target shape mismatch: {pred.shape} vs {gt.shape}")

    tp = int(np.logical_and(pred, gt).sum())
    fp = int(np.logical_and(pred, ~gt).sum())
    fn = int(np.logical_and(~pred, gt).sum())
    tn = int(np.logical_and(~pred, ~gt).sum())

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0

    return {
        "dice": float((2 * tp + eps) / (2 * tp + fp + fn + eps)),
        "iou": float((tp + eps) / (tp + fp + fn + eps)),
        "precision": precision,
        "recall": recall,
        "tp_voxels": tp,
        "fp_voxels": fp,
        "fn_voxels": fn,
        "tn_voxels": tn,
        "predicted_voxels": int(pred.sum()),
        "reference_voxels": int(gt.sum()),
    }
