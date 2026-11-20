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


def matched_instance_index(output, reference_mask, *, label=1, minimum_iou=.1, minimum_score=None):
    """Return the output index of the best spatially matched eligible detection."""
    import torch

    reference = torch.as_tensor(reference_mask, dtype=torch.bool)
    labels = output['labels'].detach().cpu()
    scores = output['scores'].detach().cpu()
    masks = output['masks'].detach().cpu()[:, 0] >= .5
    if masks.shape[-2:] != reference.shape:
        raise ValueError('Reference mask and detector output use different coordinates')
    allowed = labels == int(label)
    if minimum_score is not None:
        allowed &= scores >= minimum_score
    eligible = torch.where(allowed)[0]
    if eligible.numel() == 0 or not bool(reference.any()):
        return None
    candidate_masks = masks[eligible]
    intersection = (candidate_masks & reference).flatten(1).sum(1).float()
    union = (candidate_masks | reference).flatten(1).sum(1).float().clamp_min(1)
    iou = intersection / union
    best = int(torch.argmax(iou))
    if float(iou[best]) < float(minimum_iou):
        return None
    return int(eligible[best])


def matched_instance_score(output, reference_mask, *, label=1, minimum_iou=.1):
    """Return the score of the same spatial detection target or zero if lost."""
    index = matched_instance_index(output, reference_mask, label=label, minimum_iou=minimum_iou)
    return 0.0 if index is None else float(output['scores'][index].detach().cpu())


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
    baseline = np.asarray(baseline_value, dtype=np.float32)
    try:
        baseline = np.broadcast_to(baseline, image.shape).copy()
    except ValueError as error:
        raise ValueError('Baseline must be scalar or broadcast to the exact input frame') from error
    if not np.isfinite(baseline).all():
        raise ValueError('Finite perturbation baseline required')
    importance = np.array([float(np.mean(attribution[cell])) for cell in cells])
    ranked = np.argsort(importance)[::-1]
    random = np.random.default_rng(seed).permutation(len(cells))

    def curves(order):
        deleted = image.copy()
        inserted = baseline.copy()
        deletion = [float(score_fn(deleted))]
        insertion = [float(score_fn(inserted))]
        for index in order:
            cell = cells[int(index)]
            deleted[..., cell[0], cell[1]] = baseline[..., cell[0], cell[1]]
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
