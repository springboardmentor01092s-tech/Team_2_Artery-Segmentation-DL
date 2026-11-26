import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy import ndimage

from .classifier import stenosis_probability
from .gradcam import explain

THRESHOLD = 0.5        # candidates below this classifier probability are dropped
REF_RING_PX = 45       # how far outside the box we look for the normal vessel width

# Severity from % diameter narrowing (common angiography grading)
SEVERITY_BINS = [(25, "minimal"), (50, "mild"), (70, "moderate"), (101, "severe")]


@dataclass
class StenosisCandidate:
    bbox: List[int]              # x, y, w, h
    score: float                 # classifier probability of stenosis
    severity: Optional[str] = None
    narrowing_pct: Optional[float] = None
    segment: Optional[int] = None                 # vessel segment number
    centerline_point: Optional[List[int]] = None  # nearest centerline point (x, y)
    local_diameter_px: Optional[float] = None     # vessel width at that point
    location: Optional[str] = None                # position in the image
    narrowest_width_px: Optional[float] = None    # vessel width at the narrowing
    reference_width_px: Optional[float] = None    # normal vessel width nearby
    gradcam_url: Optional[str] = None             # Grad-CAM / Grad-CAM++ image


@dataclass
class PipelineResult:
    case_id: int
    vessel_mask_url: str = ""
    stenosis_mask_url: str = ""
    centerline_url: str = ""
    visualization_url: str = ""
    vessel_stats: dict = field(default_factory=dict)
    candidates: List[StenosisCandidate] = field(default_factory=list)
    stages_done: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def url_to_path(url: str) -> str:
    """Convert '/uploads/results/x.png' into a real file path."""
    rel = url.lstrip("/")
    for base in (Path.cwd(), Path(__file__).resolve().parent.parent):
        p = base / rel
        if p.exists():
            return str(p)
    raise FileNotFoundError(f"Mask file not found for {url}")


def load_mask(path: str):
    return np.array(Image.open(path).convert("L")) > 127


def _results_dir(image_path):
    d = Path(image_path).parent / "results"
    os.makedirs(d, exist_ok=True)
    return d


def extract_candidates(stenosis_mask, vessel_mask=None,
                       min_area=40, pad=8, max_candidates=10):
    lab, _ = ndimage.label(stenosis_mask, structure=np.ones((3, 3)))
    H, W = stenosis_mask.shape
    found = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        comp = lab[sl] == i
        area = int(comp.sum())
        if area < min_area:
            continue
        overlap = 1.0
        if vessel_mask is not None:
            overlap = float((comp & vessel_mask[sl]).sum()) / area
            if overlap < 0.3:        # blob not on a vessel, skip
                continue
        x0 = max(0, sl[1].start - pad)
        y0 = max(0, sl[0].start - pad)
        x1 = min(W, sl[1].stop + pad)
        y1 = min(H, sl[0].stop + pad)
        found.append((area, StenosisCandidate(
            bbox=[x0, y0, x1 - x0, y1 - y0],
            score=round(overlap, 3))))
    found.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in found[:max_candidates]]


def classify_candidates(image_path, shape, candidates, threshold=THRESHOLD):
    """Score each candidate box with the trained classifier; drop unlikely ones."""
    H, W = shape
    scan = Image.open(image_path).convert("L").resize((W, H))
    kept = []
    for c in candidates:
        c.score = stenosis_probability(scan, c.bbox)
        if c.score >= threshold:
            kept.append(c)
    kept.sort(key=lambda c: c.score, reverse=True)
    return kept


def _where(cx, cy, W, H):
    v = "upper" if cy < H / 3 else "lower" if cy > 2 * H / 3 else "middle"
    h = "left" if cx < W / 3 else "right" if cx > 2 * W / 3 else "center"
    return f"{v}-{h}"


def severity_from_pct(pct):
    for limit, name in SEVERITY_BINS:
        if pct < limit:
            return name
    return "severe"


def localize_candidates(vessel_mask, candidates):
    """Place each box on the vessel, then estimate % narrowing and severity."""
    H, W = vessel_mask.shape
    dist = ndimage.distance_transform_edt(vessel_mask)
    try:                                           # exact skeleton if available
        from skimage.morphology import skeletonize
        skel = skeletonize(vessel_mask)
    except ImportError:                            # fallback: ridge of the distance map
        ridge = dist >= ndimage.maximum_filter(dist, size=5)
        skel = vessel_mask & ridge & (dist >= 2)
    seg_lab, _ = ndimage.label(vessel_mask, structure=np.ones((3, 3)))
    ys, xs = np.nonzero(skel)
    wid = dist[ys, xs] * 2
    comp = seg_lab[ys, xs]

    for c in candidates:
        x, y, w, h = c.bbox
        cx, cy = x + w / 2, y + h / 2
        c.location = _where(cx, cy, W, H)
        if len(xs) == 0:
            continue
        inside = (xs >= x) & (xs < x + w) & (ys >= y) & (ys < y + h)
        pool = np.where(inside)[0] if inside.any() else np.arange(len(xs))
        k = pool[np.argmin((xs[pool] - cx) ** 2 + (ys[pool] - cy) ** 2)]
        c.centerline_point = [int(xs[k]), int(ys[k])]
        c.local_diameter_px = round(float(wid[k]), 1)
        c.segment = int(comp[k])

        same = comp == comp[k]
        in_box = inside & same
        dx = np.maximum(np.maximum(x - xs, xs - (x + w)), 0)
        dy = np.maximum(np.maximum(y - ys, ys - (y + h)), 0)
        d_out = np.hypot(dx, dy)
        ring = same & (d_out > 3) & (d_out <= REF_RING_PX)
        if in_box.sum() >= 3 and ring.sum() >= 5:
            narrow_w = float(np.percentile(wid[in_box], 10))
            ref_w = float(np.percentile(wid[ring], 75))
            pct = max(0.0, min(100.0, (1 - narrow_w / ref_w) * 100))
            c.narrowest_width_px = round(narrow_w, 1)
            c.reference_width_px = round(ref_w, 1)
            c.narrowing_pct = round(pct, 1)
            c.severity = severity_from_pct(pct)
    return candidates


def explain_candidates(image_path, shape, candidates, case_id):
    """Task 7: save a Grad-CAM / Grad-CAM++ image for every confirmed candidate."""
    H, W = shape
    scan = Image.open(image_path).convert("L").resize((W, H))
    out_dir = _results_dir(image_path)
    for old in out_dir.glob(f"case_{case_id}_gradcam_*.png"):   # remove stale heatmaps
        old.unlink()
    for i, c in enumerate(candidates, start=1):
        img = explain(scan, c.bbox)
        if img is None:
            continue
        name = f"case_{case_id}_gradcam_{i}.png"
        img.save(out_dir / name)
        c.gradcam_url = f"/uploads/results/{name}"
    return candidates


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                               # older Pillow
        return ImageFont.load_default()


def _tag(img, text, font):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 20], fill=(0, 0, 0))
    d.text((6, 3), text, fill=(255, 255, 255), font=font)
    return img


def make_visualization(image_path, vessel_mask, shape, candidates, case_id, out_dir):
    """Task 8: original + artery segmentation + stenosis regions + model explanation."""
    H, W = shape
    S, ROW = 256, 148
    font, small = _font(15), _font(13)
    scan = ImageOps.autocontrast(Image.open(image_path).convert("L").resize((W, H)), cutoff=1)
    base = scan.resize((S, S)).convert("RGB")
    kx, ky = S / W, S / H

    p1 = _tag(base.copy(), "Original image", small)

    vm = np.asarray(Image.fromarray((vessel_mask * 255).astype(np.uint8)).resize((S, S)),
                    dtype=np.float32) / 255.0
    b = np.asarray(base, dtype=np.float32)
    green = np.array([0, 230, 100], dtype=np.float32)
    seg = b * (1 - 0.6 * vm[..., None]) + green * (0.6 * vm[..., None])
    p2 = _tag(Image.fromarray(seg.clip(0, 255).astype(np.uint8)), "Artery segmentation", small)

    p3 = base.copy()
    d = ImageDraw.Draw(p3)
    for i, c in enumerate(candidates, start=1):
        x, y, w, h = c.bbox
        x, y, w, h = x * kx, y * ky, w * kx, h * ky
        d.rectangle([x, y, x + w, y + h], outline=(255, 40, 40), width=2)
        d.text((x + 2, max(22, y - 14)), str(i), fill=(255, 220, 0), font=small)
        if c.centerline_point:
            cx, cy = c.centerline_point[0] * kx, c.centerline_point[1] * ky
            d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 220, 0))
    p3 = _tag(p3, "Stenosis regions", small)

    shown = candidates[:3]
    rows = max(1, len(shown))
    canvas = Image.new("RGB", (S * 3, 30 + S + rows * ROW), (255, 255, 255))
    dr = ImageDraw.Draw(canvas)
    dr.rectangle([0, 0, canvas.width, 30], fill=(15, 23, 42))
    dr.text((8, 6), f"Stenosis analysis - case {case_id} - {len(candidates)} region(s)",
            fill=(255, 255, 255), font=font)
    for i, p in enumerate((p1, p2, p3)):
        canvas.paste(p, (i * S, 30))

    y0 = 30 + S
    if not shown:
        dr.text((8, y0 + 10), "No stenosis region was confirmed by the classifier.",
                fill=(60, 60, 60), font=font)
    for i, c in enumerate(shown, start=1):
        y = y0 + (i - 1) * ROW
        gc = Path(out_dir) / f"case_{case_id}_gradcam_{i}.png"
        if gc.exists():
            canvas.paste(Image.open(gc).convert("RGB").resize((432, 144)), (4, y + 2))
        lines = [f"Region {i}", f"Confidence: {c.score * 100:.1f}%"]
        if c.narrowing_pct is not None:
            lines.append(f"Narrowing: {c.narrowing_pct}% ({c.severity})")
        else:
            lines.append("Narrowing: not measurable")
        lines.append(f"Location: {c.location or '-'}, segment {c.segment or '-'}")
        for j, t in enumerate(lines):
            dr.text((444, y + 8 + j * 24), t, fill=(30, 30, 30), font=font if j == 0 else small)

    out = Path(out_dir) / f"case_{case_id}_visualization.png"
    canvas.save(out)
    return f"/uploads/results/{out.name}"


def run_stenosis_pipeline(case_id: int, image_path: str,
                          segment_fn, analyze_fn=None) -> PipelineResult:
    res = PipelineResult(case_id=case_id)

    # Stage 1: artery segmentation (syntax U-Net)
    vessel = segment_fn(image_path, task="syntax")
    res.vessel_mask_url = vessel["mask_url"]
    res.stages_done.append("artery_segmentation")

    # Stage 2: stenosis segmentation (stenosis U-Net)
    sten = segment_fn(image_path, task="stenosis")
    res.stenosis_mask_url = sten["mask_url"]
    res.stages_done.append("stenosis_segmentation")

    # Stage 3: vessel analysis (centerline, diameter)
    stats = analyze_fn(vessel) if analyze_fn else vessel.get("vessel", {})
    res.vessel_stats = stats
    res.centerline_url = stats.get("centerline_url", "")
    res.stages_done.append("vessel_analysis")

    # Stage 4: candidate regions
    sten_mask = load_mask(url_to_path(sten["mask_url"]))
    vess_mask = load_mask(url_to_path(vessel["mask_url"]))
    cands = extract_candidates(sten_mask, vess_mask)
    res.stages_done.append("candidate_extraction")

    # Stage 5: classifier check
    res.candidates = classify_candidates(image_path, sten_mask.shape, cands)
    res.stages_done.append("stenosis_classification")

    # Stages 6-8: localization, % narrowing, severity
    clean_url = stats.get("clean_url") or vessel["mask_url"]
    clean_mask = load_mask(url_to_path(clean_url))
    res.candidates = localize_candidates(clean_mask, res.candidates)
    res.stages_done.append("stenosis_localization")
    res.stages_done.append("narrowing_estimation")
    res.stages_done.append("severity_classification")

    # Stage 9: explainable AI (Task 7)
    res.candidates = explain_candidates(image_path, sten_mask.shape, res.candidates, case_id)
    res.stages_done.append("explainable_ai")

    # Stage 10: combined visualization (Task 8)
    res.visualization_url = make_visualization(
        image_path, vess_mask, sten_mask.shape, res.candidates, case_id, _results_dir(image_path))
    res.stages_done.append("visualization")

    return res