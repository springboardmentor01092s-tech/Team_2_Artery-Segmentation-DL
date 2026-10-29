"""Post-processing and threshold optimization for 3D binary segmentation."""
import numpy as np
from scipy import ndimage


def keep_largest_connected_component(mask):
    """
    Retain only the single largest 3D connected foreground component.
    Aorta is an anatomically contiguous lumen; isolated blobs in veins or organs
    are false positives and are pruned by this function.
    """
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return np.zeros_like(mask, dtype=np.uint8)

    labeled, num_features = ndimage.label(mask)
    if num_features <= 1:
        return mask.astype(np.uint8)

    counts = ndimage.sum(mask, labeled, range(1, num_features + 1))
    largest_label = int(np.argmax(counts)) + 1
    return (labeled == largest_label).astype(np.uint8)


def keep_major_components(mask, min_voxels=1000, ratio_to_largest=0.15):
    """
    Retain major 3D connected components (largest component + any component >= ratio_to_largest).
    Prevents discarding valid aortic sections (e.g. thoracic vs abdominal aorta) if an intimal
    flap or narrow gap creates a temporary discontinuity in the segmentation.
    """
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return np.zeros_like(mask, dtype=np.uint8)

    labeled, num_features = ndimage.label(mask)
    if num_features <= 1:
        return mask.astype(np.uint8)

    counts = np.array(ndimage.sum(mask, labeled, range(1, num_features + 1)))
    max_count = np.max(counts)
    if max_count == 0:
        return np.zeros_like(mask, dtype=np.uint8)

    # Valid if at least min_voxels AND (either largest OR >= ratio_to_largest * max_count)
    threshold_count = max(min_voxels, max_count * ratio_to_largest)
    valid_labels = [i + 1 for i, count in enumerate(counts) if (count == max_count or count >= threshold_count)]

    return np.isin(labeled, valid_labels).astype(np.uint8)


def filter_small_components(mask, min_voxels=1000):
    """Remove disconnected components smaller than min_voxels."""
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return np.zeros_like(mask, dtype=np.uint8)

    labeled, num_features = ndimage.label(mask)
    if num_features <= 1:
        return mask.astype(np.uint8)

    counts = ndimage.sum(mask, labeled, range(1, num_features + 1))
    valid_labels = [i + 1 for i, count in enumerate(counts) if count >= min_voxels]
    if not valid_labels:
        largest_label = int(np.argmax(counts)) + 1
        return (labeled == largest_label).astype(np.uint8)

    return np.isin(labeled, valid_labels).astype(np.uint8)


def postprocess_prediction(probabilities, threshold=0.5, apply_lcc=True,
                           mode="major", min_voxels=1000, ratio_to_largest=0.15):
    """
    Convert raw sigmoid probabilities into a cleaned binary segmentation mask.
    
    Args:
        probabilities: 3D float numpy array in [0, 1].
        threshold: Classification threshold for foreground.
        apply_lcc: Boolean flag for backward compatibility (if False, mode is set to 'none').
        mode: Post-processing mode: 'major' (keeps largest + major branches), 'lcc' (strict single largest),
              'filter_small' (removes < min_voxels), or 'none'.
        min_voxels: Minimum voxel volume for retained components.
        ratio_to_largest: Relative volume ratio to largest component for retention.
    """
    pred = (probabilities >= threshold)
    if not pred.any():
        return np.zeros_like(pred, dtype=np.uint8)

    if not apply_lcc or mode == "none":
        return pred.astype(np.uint8)

    if mode == "major":
        return keep_major_components(pred, min_voxels=min_voxels, ratio_to_largest=ratio_to_largest)
    elif mode == "lcc":
        return keep_largest_connected_component(pred)
    elif mode == "filter_small":
        return filter_small_components(pred, min_voxels=min_voxels)

    return pred.astype(np.uint8)


def find_optimal_threshold(probabilities, ground_truth, thresholds=None):
    """
    Find threshold maximizing whole-volume Dice on a validation volume.
    Never run on held-out test data.
    """
    if thresholds is None:
        thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    gt = np.asarray(ground_truth, dtype=bool)
    gt_sum = gt.sum()
    if gt_sum == 0:
        return 0.5, 0.0, {t: 0.0 for t in thresholds}

    best_thresh = 0.5
    best_dice = -1.0
    results = {}

    for t in thresholds:
        pred = (probabilities >= t)
        tp = np.logical_and(pred, gt).sum()
        denominator = pred.sum() + gt_sum
        dice = float((2 * tp) / max(denominator, 1))
        results[t] = dice
        if dice > best_dice:
            best_dice = dice
            best_thresh = t

    return best_thresh, best_dice, results
