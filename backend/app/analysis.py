import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def thin(mask):
    """Zhang-Suen thinning (numpy only) -> one-pixel centerline."""
    img = mask.astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            p = np.pad(img, 1)
            n = [p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:], p[2:, 2:],
                 p[2:, 1:-1], p[2:, :-2], p[1:-1, :-2], p[:-2, :-2]]
            B = sum(x.astype(np.int16) for x in n)
            seq = n + [n[0]]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.int16) for i in range(8))
            if step == 0:
                c = ((n[0] * n[2] * n[4]) == 0) & ((n[2] * n[4] * n[6]) == 0)
            else:
                c = ((n[0] * n[2] * n[6]) == 0) & ((n[0] * n[4] * n[6]) == 0)
            rm = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if rm.any():
                img[rm] = 0
                changed = True
    return img.astype(bool)


def analyze_vessels(image_path, mask_path, out_dir, prefix, min_size=64):
    os.makedirs(out_dir, exist_ok=True)
    original = Image.open(image_path).convert("L")
    mask = np.asarray(Image.open(mask_path).convert("L")) > 127

    # 1) ignore a thin margin (frames / black borders)
    h, w = mask.shape
    m = max(1, int(0.03 * min(h, w)))
    mask[:m, :] = False
    mask[-m:, :] = False
    mask[:, :m] = False
    mask[:, -m:] = False

    clean = ndi.binary_closing(mask, structure=np.ones((3, 3)), iterations=2)
    clean = ndi.binary_fill_holes(clean)

    # 2) drop tiny blobs
    labels, n = ndi.label(clean)
    if n:
        sizes = ndi.sum(clean, labels, range(1, n + 1))
        clean = np.isin(labels, np.where(sizes >= min_size)[0] + 1)

    # 3) drop long straight bar-like components (not vessels)
    labels, n = ndi.label(clean)
    for i in range(1, n + 1):
        ys, xs = np.nonzero(labels == i)
        if ys.size < 200:
            continue
        ev = np.linalg.eigvalsh(np.cov(np.vstack([xs, ys])))
        elong = np.sqrt(ev[1] / max(ev[0], 1e-6))
        length = 3.5 * np.sqrt(ev[1])
        if elong > 10 and length > 0.3 * max(h, w):
            clean[labels == i] = False
            print("removed bar component", i, round(float(elong), 1))

    _, segments = ndi.label(clean)

    skel = thin(clean)
    dist = ndi.distance_transform_edt(clean)
    d = dist[skel] * 2
    has = d.size > 0

    rgb = np.stack([np.asarray(original)] * 3, axis=-1).astype(np.float32)
    rgb[clean] = rgb[clean] * 0.6 + np.array([255, 40, 40]) * 0.4
    rgb[ndi.binary_dilation(skel)] = [255, 255, 0]

    clean_name, line_name = f"{prefix}_clean.png", f"{prefix}_centerline.png"
    Image.fromarray(clean.astype(np.uint8) * 255).save(os.path.join(out_dir, clean_name))
    Image.fromarray(rgb.astype(np.uint8)).save(os.path.join(out_dir, line_name))

    return {
        "clean": clean_name,
        "centerline": line_name,
        "vessel_segments": int(segments),
        "centerline_length_px": int(skel.sum()),
        "mean_diameter_px": round(float(d.mean()), 2) if has else 0,
        "max_diameter_px": round(float(d.max()), 2) if has else 0,
        "min_diameter_px": round(float(np.percentile(d, 5)), 2) if has else 0,
    }