"""Forward-only attribution diagnostics with predeclared controls.

This module never changes a supplied model. Parameter randomization must use a
separate disposable model and score function supplied by the caller.
"""
import hashlib

import numpy as np
from scipy.stats import spearmanr

PROTOCOL = {
    "id": "corovision-forward-occlusion-v1",
    "deletion_auc_advantage_min": 0.01,
    "insertion_auc_advantage_min": 0.01,
    "randomized_attribution_abs_spearman_max": 0.2,
}


def _cells(shape, grid):
    height, width = shape[-2:]
    ys = np.linspace(0, height, grid + 1, dtype=int)
    xs = np.linspace(0, width, grid + 1, dtype=int)
    return [(slice(ys[y], ys[y + 1]), slice(xs[x], xs[x + 1]))
            for y in range(grid) for x in range(grid)]


def _auc(values):
    values = np.asarray(values, dtype=float)
    return float(np.trapezoid(values, dx=1 / max(1, len(values) - 1)))


def evaluate_forward_occlusion(image, attribution, score_fn, *, randomized_score_fn=None,
                               randomized_attribution=None, grid=8, seed=20261114,
                               baseline_value=0.0):
    """Compare attribution-ranked deletion/insertion with equal-area random controls."""
    image = np.asarray(image, dtype=np.float32)
    attribution = np.asarray(attribution, dtype=np.float32)
    if image.ndim not in (2, 3) or attribution.shape != image.shape[-2:]:
        raise ValueError("Attribution must match the exact input spatial frame")
    if grid < 2 or min(attribution.shape) < grid or not np.isfinite(image).all() or not np.isfinite(attribution).all():
        raise ValueError("Finite input and attribution on a valid grid are required")
    cells = _cells(image.shape, grid)
    importance = np.array([float(np.mean(attribution[cell])) for cell in cells])
    ranked = np.argsort(importance)[::-1]
    random = np.random.default_rng(seed).permutation(len(cells))

    def curves(order):
        deleted = image.copy()
        inserted = np.full_like(image, baseline_value)
        deletion = [float(score_fn(deleted))]
        insertion = [float(score_fn(inserted))]
        for index in order:
            cell = cells[int(index)]
            deleted[..., cell[0], cell[1]] = baseline_value
            inserted[..., cell[0], cell[1]] = image[..., cell[0], cell[1]]
            deletion.append(float(score_fn(deleted)))
            insertion.append(float(score_fn(inserted)))
        return deletion, insertion

    ranked_deletion, ranked_insertion = curves(ranked)
    random_deletion, random_insertion = curves(random)
    metrics = {
        "ranked_deletion_auc": _auc(ranked_deletion),
        "random_deletion_auc": _auc(random_deletion),
        "ranked_insertion_auc": _auc(ranked_insertion),
        "random_insertion_auc": _auc(random_insertion),
    }
    metrics["deletion_auc_advantage"] = metrics["random_deletion_auc"] - metrics["ranked_deletion_auc"]
    metrics["insertion_auc_advantage"] = metrics["ranked_insertion_auc"] - metrics["random_insertion_auc"]
    if (randomized_score_fn is None) != (randomized_attribution is None):
        raise ValueError("Randomization control requires a disposable score function and attribution together")
    randomization = None
    if randomized_score_fn is not None:
        randomized_attribution = np.asarray(randomized_attribution, dtype=np.float32)
        if randomized_attribution.shape != attribution.shape:
            raise ValueError("Randomized attribution geometry differs")
        correlation = float(spearmanr(attribution.ravel(), randomized_attribution.ravel()).statistic)
        randomization = {"absolute_spearman": abs(correlation),
                         "disposable_model_score": float(randomized_score_fn(image))}
    gates = {
        "deletion": metrics["deletion_auc_advantage"] >= PROTOCOL["deletion_auc_advantage_min"],
        "insertion": metrics["insertion_auc_advantage"] >= PROTOCOL["insertion_auc_advantage_min"],
        "randomization": (randomization is not None and randomization["absolute_spearman"]
                          <= PROTOCOL["randomized_attribution_abs_spearman_max"]),
    }
    return {
        "protocol": PROTOCOL,
        "input_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
        "grid": grid,
        "seed": seed,
        "target_binding": "caller_supplied_frozen_checkpoint_score_function",
        "metrics": metrics,
        "randomization": randomization,
        "gates": gates,
        "status": "faithfulness_controls_passed" if all(gates.values()) else "faithfulness_not_established",
        "clinical_validated": False,
    }
