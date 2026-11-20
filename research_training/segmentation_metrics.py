"""Overlap and boundary metrics for binary segmentation masks (2D images or 3D volumes).

Implements the segmentation metrics named in the project specification: Dice, IoU,
pixel accuracy, precision, recall/sensitivity, specificity, Hausdorff distance (HD),
95th-percentile Hausdorff distance (HD95) and average symmetric surface distance (ASSD).
Distances use the supplied voxel spacing, so results are in millimetres when spacing is
known and in pixels/voxels otherwise. Undefined values are returned as None, never 0 or 1.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

SCHEMA = "corovision.segmentation-metrics.v1"


def _surface(mask: np.ndarray) -> np.ndarray:
    from scipy.ndimage import binary_erosion, generate_binary_structure
    if not mask.any():
        return np.zeros_like(mask, dtype=bool)
    structure = generate_binary_structure(mask.ndim, 1)
    return mask & ~binary_erosion(mask, structure=structure, border_value=0)


def surface_distances(prediction, reference, spacing: Sequence[float] | None = None):
    """Distances from each prediction-surface voxel to the reference surface and vice versa."""
    from scipy.ndimage import distance_transform_edt
    pred = np.asarray(prediction).astype(bool)
    ref = np.asarray(reference).astype(bool)
    if pred.shape != ref.shape:
        raise ValueError(f"Mask shapes differ: {pred.shape} vs {ref.shape}")
    spacing = tuple(float(s) for s in (spacing or (1.0,) * pred.ndim))
    if len(spacing) != pred.ndim or any(s <= 0 for s in spacing):
        raise ValueError("Spacing must give one positive value per mask dimension")
    if not pred.any() or not ref.any():
        return None, None
    pred_surface, ref_surface = _surface(pred), _surface(ref)
    to_ref = distance_transform_edt(~ref_surface, sampling=spacing)
    to_pred = distance_transform_edt(~pred_surface, sampling=spacing)
    return to_ref[pred_surface], to_pred[ref_surface]


def boundary_metrics(prediction, reference, spacing: Sequence[float] | None = None) -> dict:
    a, b = surface_distances(prediction, reference, spacing)
    if a is None:
        return {"hausdorff": None, "hd95": None, "assd": None,
                "boundary_note": "Undefined when either mask is empty."}
    both = np.concatenate([a, b])
    return {"hausdorff": float(max(a.max(), b.max())),
            "hd95": float(max(np.percentile(a, 95), np.percentile(b, 95))),
            "assd": float(both.mean())}


def segmentation_metrics(prediction, reference, spacing: Sequence[float] | None = None) -> dict:
    pred = np.asarray(prediction).astype(bool)
    ref = np.asarray(reference).astype(bool)
    if pred.shape != ref.shape:
        raise ValueError(f"Mask shapes differ: {pred.shape} vs {ref.shape}")
    tp = int((pred & ref).sum()); fp = int((pred & ~ref).sum())
    fn = int((~pred & ref).sum()); tn = int((~pred & ~ref).sum())
    ratio = lambda n, d: (n / d) if d else None
    result = {"schema_version": SCHEMA, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
              "dice": ratio(2 * tp, 2 * tp + fp + fn), "iou": ratio(tp, tp + fp + fn),
              "pixel_accuracy": ratio(tp + tn, tp + fp + fn + tn),
              "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
              "sensitivity": ratio(tp, tp + fn), "specificity": ratio(tn, tn + fp),
              "distance_unit": "mm" if spacing else "pixel"}
    result.update(boundary_metrics(pred, ref, spacing))
    return result


def summarize(rows: list[dict]) -> dict:
    """Mean of per-case metrics, ignoring undefined (None) values and reporting their support."""
    keys = ("dice", "iou", "pixel_accuracy", "precision", "recall", "sensitivity", "specificity", "hausdorff", "hd95", "assd")
    out = {"schema_version": SCHEMA, "cases": len(rows), "aggregation": "mean_of_per_case_values"}
    for key in keys:
        values = [r[key] for r in rows if r.get(key) is not None]
        out[key] = float(np.mean(values)) if values else None
        out[f"{key}_support"] = len(values)
    return out
