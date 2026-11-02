"""
Coronary Artery Post-processing and Morphological Vessel Analysis.
"""

import os
import tempfile
os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_cache")
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize
from scipy.ndimage import distance_transform_edt


def postprocess_mask(raw_mask: np.ndarray, min_component_size: int = 40, kernel_size: int = 3) -> np.ndarray:
    """Applies morphological closing and removes small isolated noise components."""
    binary = ((raw_mask > 127) if raw_mask.max() > 1 else (raw_mask > 0.5)).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    clean_mask = np.zeros_like(closed)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_component_size:
            clean_mask[labels == i] = 255
    return clean_mask


def extract_vessel_centerline(binary_mask: np.ndarray) -> np.ndarray:
    """Extracts a 1-pixel wide topological centerline via skeletonization."""
    return (skeletonize(binary_mask > 0).astype(np.uint8)) * 255


def estimate_vessel_diameters(binary_mask: np.ndarray, skeleton_mask: np.ndarray) -> dict:
    """Estimates vessel caliber along the centerline using Euclidean Distance Transform."""
    bool_mask, skel_bool = binary_mask > 0, skeleton_mask > 0
    total_pixels = binary_mask.shape[0] * binary_mask.shape[1]
    vessel_area = int(np.sum(bool_mask))

    num_labels, _, _, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    num_segments = max(0, num_labels - 1)

    if not np.any(skel_bool):
        d_vals = np.array([0.0])
        dist_map = np.zeros_like(binary_mask, dtype=np.float32)
    else:
        dist_map = distance_transform_edt(bool_mask)
        d_vals = dist_map[skel_bool] * 2.0

    return {
        "centerline_length_px": int(np.sum(skel_bool)),
        "vessel_area_px": vessel_area,
        "vessel_area_pct": round(float((vessel_area / total_pixels) * 100.0), 3),
        "num_vessel_segments": num_segments,
        "mean_diameter_px": round(float(np.mean(d_vals)), 2),
        "median_diameter_px": round(float(np.median(d_vals)), 2),
        "max_diameter_px": round(float(np.max(d_vals)), 2),
        "min_diameter_px": round(float(np.min(d_vals)), 2),
        "std_diameter_px": round(float(np.std(d_vals)), 2),
        "distance_map": dist_map,
    }


def create_vessel_analysis_figure(image: np.ndarray, clean_mask: np.ndarray,
                                  skeleton: np.ndarray, dist_map: np.ndarray,
                                  metrics: dict, save_path: str = None) -> plt.Figure:
    """Generates a 4-panel diagnostic plot: Angiogram, Mask, Centerline, Caliber Heatmap."""
    fig, axes = plt.subplots(1, 4, figsize=(18, 5))

    # Panel 1: Original
    axes[0].imshow(image, cmap="gray")
    # Panel 2: Mask
    axes[1].imshow(clean_mask, cmap="gray")

    # Panel 3: Centerline overlay in green
    overlay = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2RGB)
    overlay[skeleton > 0] = [0, 255, 0]
    axes[2].imshow(overlay)

    # Panel 4: Diameter Heatmap on centerline
    d_map = np.zeros_like(dist_map)
    d_map[skeleton > 0] = dist_map[skeleton > 0] * 2.0
    axes[3].imshow(image, cmap="gray")
    im = axes[3].imshow(np.ma.masked_where(d_map == 0, d_map), cmap="jet", alpha=0.9)
    plt.colorbar(im, ax=axes[3], fraction=0.046, pad=0.04, label="Diameter (px)")

    titles = [
        "1. Coronary Angiogram",
        f"2. Artery Mask ({metrics['vessel_area_pct']}%)",
        f"3. Centerline ({metrics['centerline_length_px']} px)",
        f"4. Caliber (Mean: {metrics['mean_diameter_px']} px)",
    ]
    for ax, title in zip(axes, titles):
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.axis("off")

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return None
    return fig


if __name__ == "__main__":
    mask = cv2.imread("dataset/masks/1.png", cv2.IMREAD_GRAYSCALE)
    if mask is not None:
        clean = postprocess_mask(mask)
        skel = extract_vessel_centerline(clean)
        res = estimate_vessel_diameters(clean, skel)
        print("Vessel Analysis Test:", {k: v for k, v in res.items() if k != "distance_map"})
