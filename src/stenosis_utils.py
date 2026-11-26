"""
Helper utilities for coronary artery stenosis detection, caliber profiling,
patch extraction, dataset construction, and lesion record formatting.
"""

import os
import cv2
import numpy as np
import torch
from torch.utils.data import TensorDataset
from scipy.ndimage import distance_transform_edt
from src.vessel_analysis import postprocess_mask, extract_vessel_centerline


def extract_centerline_diameters(mask: np.ndarray):
    """Extracts cleaned vessel mask, centerline coordinates, and lumen diameters."""
    clean_m = postprocess_mask(mask)
    skel = extract_vessel_centerline(clean_m) > 0
    if not np.any(skel):
        return clean_m, None, None
    coords = np.column_stack(np.where(skel))
    diameters = distance_transform_edt(clean_m > 0)[skel] * 2.0
    return clean_m, coords, diameters


def get_rvd(coords: np.ndarray, diameters: np.ndarray, y: int, x: int, rvd_radius: int = 18) -> float:
    """Calculates reference vessel diameter (85th percentile of neighboring diameters)."""
    nbrs = np.where((np.hypot(coords[:, 0] - y, coords[:, 1] - x) <= rvd_radius) &
                    (np.hypot(coords[:, 0] - y, coords[:, 1] - x) > 3))[0]
    return float(np.percentile(diameters[nbrs], 85)) if len(nbrs) >= 5 else 0.0


def extract_patch(image: np.ndarray, mask: np.ndarray, cy: int, cx: int, patch_size: int = 48):
    """Crops a normalized 2-channel [image, mask] patch centered at (cy, cx)."""
    half = patch_size // 2
    y1, y2 = max(0, cy - half), min(image.shape[0], cy + half)
    x1, x2 = max(0, cx - half), min(image.shape[1], cx + half)
    img_p = image[y1:y2, x1:x2].astype(np.float32) / 255.0
    msk_p = (mask[y1:y2, x1:x2] > 127).astype(np.float32)

    ph, pw = patch_size - img_p.shape[0], patch_size - img_p.shape[1]
    if ph > 0 or pw > 0:
        img_p = np.pad(img_p, ((0, ph), (0, pw)), mode="reflect")
        msk_p = np.pad(msk_p, ((0, ph), (0, pw)), mode="constant", constant_values=0)
    return (int(x1), int(y1), int(x2), int(y2)), np.stack([img_p, msk_p], axis=0)


def build_stenosis_dataset(case_ids: list, images_dir: str, masks_dir: str, cfg: dict):
    """Constructs balanced training/val dataset of candidate stenosis vs normal patches."""
    p_size, s_thresh = cfg.get("patch_size", 48), cfg.get("stenosis_threshold", 0.45)
    rvd_rad, min_rvd = cfg.get("reference_radius", 18), cfg.get("min_ref_caliber", 3.5)
    patches, labels = [], []

    for cid in case_ids:
        img = cv2.imread(os.path.join(images_dir, f"{cid}.png"), cv2.IMREAD_GRAYSCALE)
        msk = cv2.imread(os.path.join(masks_dir, f"{cid}.png"), cv2.IMREAD_GRAYSCALE)
        if img is None or msk is None:
            continue
        clean_m, coords, diameters = extract_centerline_diameters(msk)
        if coords is None:
            continue

        pos_pts, neg_pts = [], []
        for i, (y, x) in enumerate(coords):
            d_cur = diameters[i]
            rvd = get_rvd(coords, diameters, y, x, rvd_rad)
            if rvd >= min_rvd:
                drop = (rvd - d_cur) / rvd
                if drop >= s_thresh:
                    pos_pts.append((int(y), int(x)))
                elif drop < 0.15 and d_cur >= min_rvd * 0.85:
                    neg_pts.append((int(y), int(x)))

        for pts, label in [(pos_pts, 1), (neg_pts, 0)]:
            for idx in np.linspace(0, len(pts) - 1, min(len(pts), 3), dtype=int) if pts else []:
                _, p = extract_patch(img, clean_m, pts[idx][0], pts[idx][1], p_size)
                patches.append(p)
                labels.append(label)

    return TensorDataset(torch.tensor(np.array(patches), dtype=torch.float32),
                         torch.tensor(np.array(labels), dtype=torch.long))


def calc_array_stats(arr: np.ndarray) -> dict:
    """Computes basic statistics (mean, median, std, min, max) for numeric arrays."""
    return {
        "mean": round(float(np.mean(arr)), 2),
        "median": round(float(np.median(arr)), 2),
        "std": round(float(np.std(arr)), 2),
        "min": round(float(np.min(arr)), 2),
        "max": round(float(np.max(arr)), 2),
    }


def format_lesion_record(cid: str, lid: str, has_stenosis: bool, l: dict = None) -> dict:
    """Formats a single lesion record for tabular CSV reporting."""
    if not has_stenosis or l is None:
        return {
            "case_id": cid, "lesion_id": f"{cid}_none", "has_stenosis": False,
            "box_x1": 0, "box_y1": 0, "box_x2": 0, "box_y2": 0, "center_x": 0, "center_y": 0,
            "reference_diameter_px": 0.0, "min_lumen_diameter_px": 0.0, "percentage_narrowing": 0.0,
            "severity_class": "Normal", "severity_range": "0–24%", "severity_grade": 1, "confidence": 0.0,
            "calibration_status": "No stenosis detected", "mld_px": 0.0, "rvd_px": 0.0, "stenosis_pct": 0.0,
            "severity": "Normal",
        }
    return {
        "case_id": cid, "lesion_id": lid, "has_stenosis": True,
        "box_x1": l["box"][0], "box_y1": l["box"][1], "box_x2": l["box"][2], "box_y2": l["box"][3],
        "center_x": l["center"][0], "center_y": l["center"][1],
        "reference_diameter_px": l["rvd_px"], "min_lumen_diameter_px": l["mld_px"],
        "percentage_narrowing": l["narrowing_pct"], "severity_class": l["severity"],
        "severity_range": l["severity_range"], "severity_grade": l["severity_grade"],
        "confidence": l["confidence"], "calibration_status": l["calibration_status"],
        "mld_px": l["mld_px"], "rvd_px": l["rvd_px"], "stenosis_pct": l["narrowing_pct"],
        "severity": l["severity"],
    }

