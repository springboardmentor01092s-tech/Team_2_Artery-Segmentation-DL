"""Auditable preprocessing for the ARCADE COCO polygon release."""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import platform
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

LOG = logging.getLogger("corovision.preprocessing")
TASKS = ("syntax", "stenosis")
SPLITS = ("train", "val", "test")


@dataclass
class Issue:
    task: str
    split: str
    path: str
    issue_type: str
    severity: str
    explanation: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_coco(path: Path) -> dict[str, Any]:
    """Load and minimally validate an ARCADE COCO annotation file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("images", "annotations", "categories"):
        if key not in data or not isinstance(data[key], list):
            raise ValueError(f"{path}: missing list field {key!r}")
    return data


def polygon_points(flat: list[float]) -> list[tuple[float, float]]:
    if len(flat) < 6 or len(flat) % 2:
        raise ValueError("polygon must contain at least three x/y pairs")
    return list(zip(flat[0::2], flat[1::2]))


def fit_transform(image: Image.Image, size: tuple[int, int], resample: int, fill: int = 0) -> Image.Image:
    """Letterbox an image without changing its aspect ratio."""
    contained = ImageOps.contain(image, size, method=resample)
    canvas = Image.new(image.mode, size, fill)
    canvas.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return canvas


def rasterize(image_row: dict[str, Any], annotations: list[dict[str, Any]], task: str) -> Image.Image:
    """Rasterize source COCO polygons without inventing label semantics."""
    size = (int(image_row["width"]), int(image_row["height"]))
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for ann in annotations:
        value = int(ann["category_id"]) if task == "syntax" else 1
        for flat in ann.get("segmentation", []):
            draw.polygon(polygon_points(flat), fill=value)
    return mask


def _annotation_errors(task: str, split: str, data: dict[str, Any], image_files: dict[str, Path]) -> list[Issue]:
    issues: list[Issue] = []
    image_ids: dict[Any, dict[str, Any]] = {}
    names: set[str] = set()
    for row in data["images"]:
        if row.get("id") in image_ids:
            issues.append(Issue(task, split, "", "duplicate_image_id", "error", str(row.get("id"))))
        image_ids[row.get("id")] = row
        name = str(row.get("file_name", ""))
        if name in names:
            issues.append(Issue(task, split, name, "duplicate_filename", "error", name))
        names.add(name)
        if name not in image_files:
            issues.append(Issue(task, split, name, "missing_image", "error", "annotation image is absent"))
    for name in sorted(set(image_files) - names):
        issues.append(Issue(task, split, name, "unlisted_image", "error", "image is absent from COCO images"))
    category_ids = {row.get("id") for row in data["categories"]}
    for ann in data["annotations"]:
        image = image_ids.get(ann.get("image_id"))
        if image is None:
            issues.append(Issue(task, split, "", "bad_image_reference", "error", str(ann.get("image_id"))))
            continue
        if ann.get("category_id") not in category_ids:
            issues.append(Issue(task, split, image["file_name"], "unknown_category", "error", str(ann.get("category_id"))))
        for flat in ann.get("segmentation", []):
            try:
                points = polygon_points(flat)
            except ValueError as exc:
                issues.append(Issue(task, split, image["file_name"], "invalid_polygon", "error", str(exc)))
                continue
            width, height = float(image["width"]), float(image["height"])
            if any(x < 0 or y < 0 or x > width or y > height for x, y in points):
                issues.append(Issue(task, split, image["file_name"], "coordinate_out_of_bounds", "error", f"image={width}x{height}"))
    return issues


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _overlay(image: Image.Image, mask: Image.Image) -> Image.Image:
    base = image.convert("RGBA")
    tint = Image.new("RGBA", image.size, (255, 67, 54, 0))
    tint.putalpha(mask.point(lambda value: 115 if value else 0))
    return Image.alpha_composite(base, tint).convert("RGB")


def run_pipeline(data_root: Path, output_root: Path, tasks: Iterable[str] = TASKS,
                 splits: Iterable[str] = SPLITS, config_path: Path | None = None,
                 dry_run: bool = False, force: bool = False) -> dict[str, Any]:
    """Validate and preprocess selected ARCADE tasks and official splits."""
    config_path = config_path or Path(__file__).parent / "configs" / "arcade_preprocessing.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    size = tuple(int(v) for v in config["target_size"])
    selected_tasks, selected_splits = tuple(tasks), tuple(splits)
    unknown = (set(selected_tasks) - set(TASKS)) | (set(selected_splits) - set(SPLITS))
    if unknown:
        raise ValueError(f"unknown tasks/splits: {sorted(unknown)}")
    if output_root.resolve() == data_root.resolve() or data_root.resolve() in output_root.resolve().parents:
        raise ValueError("output root must not be the raw data root or a child of it")

    issues: list[Issue] = []
    manifests: dict[str, list[dict[str, Any]]] = defaultdict(list)
    inventory: list[dict[str, Any]] = []
    hashes: dict[tuple[str, str], dict[str, list[str]]] = {}
    previews: list[tuple[str, str, str, Image.Image]] = []
    preview_counts: Counter[tuple[str, str]] = Counter()

    for task in selected_tasks:
        for split in selected_splits:
            base = data_root / task / split
            annotation_path = base / "annotations" / f"{split}.json"
            images_dir = base / "images"
            if not annotation_path.is_file() or not images_dir.is_dir():
                raise FileNotFoundError(f"required ARCADE split is missing: {base}")
            data = load_coco(annotation_path)
            image_files = {path.name: path for path in images_dir.iterdir() if path.is_file()}
            issues.extend(_annotation_errors(task, split, data, image_files))
            by_image: dict[Any, list[dict[str, Any]]] = defaultdict(list)
            for ann in data["annotations"]:
                by_image[ann.get("image_id")].append(ann)
            categories = {int(row["id"]): str(row["name"]) for row in data["categories"]}
            hash_to_samples: dict[str, list[str]] = defaultdict(list)
            modes, dimensions = Counter(), Counter()

            for image_row in data["images"]:
                source = images_dir / image_row["file_name"]
                sample_id = f"{task}_{split}_{image_row['id']}"
                row_issues: list[str] = []
                if not source.is_file():
                    continue
                try:
                    with Image.open(source) as opened:
                        opened.verify()
                    with Image.open(source) as opened:
                        source_image = opened.convert(config["image_mode"])
                        actual_size, source_mode = opened.size, opened.mode
                    modes[source_mode] += 1
                    dimensions[f"{actual_size[0]}x{actual_size[1]}"] += 1
                    if actual_size != (int(image_row["width"]), int(image_row["height"])):
                        row_issues.append("metadata_dimension_mismatch")
                        issues.append(Issue(task, split, str(source), row_issues[-1], "error", f"COCO={image_row['width']}x{image_row['height']}, actual={actual_size}"))
                except (UnidentifiedImageError, OSError) as exc:
                    issues.append(Issue(task, split, str(source), "unreadable_image", "error", str(exc)))
                    continue
                digest = sha256(source)
                hash_to_samples[digest].append(sample_id)
                processed_image = output_root / task / split / "images" / f"{Path(image_row['file_name']).stem}.png"
                processed_label = output_root / task / split / ("masks" if task == "syntax" else "labels") / (f"{Path(image_row['file_name']).stem}.png" if task == "syntax" else f"{Path(image_row['file_name']).stem}.json")
                if not dry_run:
                    processed_image.parent.mkdir(parents=True, exist_ok=True)
                    processed_label.parent.mkdir(parents=True, exist_ok=True)
                    transformed = fit_transform(source_image, size, Image.Resampling.BILINEAR, int(config["padding_value"]))
                    mask = rasterize(image_row, by_image[image_row["id"]], task)
                    mask = fit_transform(mask, size, Image.Resampling.NEAREST, 0)
                    if force or not processed_image.exists():
                        transformed.save(processed_image, format="PNG")
                    if task == "syntax":
                        if force or not processed_label.exists():
                            mask.save(processed_label, format="PNG")
                    else:
                        mask_path = output_root / task / split / "masks" / f"{Path(image_row['file_name']).stem}.png"
                        mask_path.parent.mkdir(parents=True, exist_ok=True)
                        label = {"sample_id": sample_id, "source_image_id": image_row["id"], "categories": categories,
                                 "annotations": by_image[image_row["id"]]}
                        if force or not processed_label.exists():
                            processed_label.write_text(json.dumps(label, separators=(",", ":")), encoding="utf-8")
                        if force or not mask_path.exists():
                            mask.save(mask_path, format="PNG")
                    if preview_counts[(task, split)] < 2:
                        previews.append((task, split, sample_id, _overlay(transformed, mask)))
                        preview_counts[(task, split)] += 1
                manifests[task].append({
                    "sample_id": sample_id, "task": task, "split": split,
                    "source_image_path": str(source.relative_to(data_root.parent)),
                    "source_annotation_path": str(annotation_path.relative_to(data_root.parent)),
                    "processed_image_path": str(processed_image.relative_to(output_root.parent)),
                    "processed_label_path": str(processed_label.relative_to(output_root.parent)),
                    "width": actual_size[0], "height": actual_size[1], "channels": 1 if config["image_mode"] == "L" else 3,
                    "pixel_spacing_x_mm": "", "pixel_spacing_y_mm": "", "spacing_status": "unavailable_in_source_png_coco",
                    "annotation_type": "coco_polygon", "annotation_status": "present" if by_image[image_row["id"]] else "empty",
                    "preprocessing_config_version": config["config_version"],
                    "validation_status": "fail" if row_issues else "pass", "exclusion_reason": "|".join(row_issues),
                    "source_sha256": digest,
                })
            hashes[(task, split)] = hash_to_samples
            inventory.append({"task": task, "split": split, "images": len(data["images"]), "files": len(image_files),
                              "annotations": len(data["annotations"]), "categories": categories,
                              "dimensions": dict(dimensions), "modes": dict(modes)})

    for task in selected_tasks:
        for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
            if (task, left) not in hashes or (task, right) not in hashes:
                continue
            for digest in sorted(set(hashes[(task, left)]) & set(hashes[(task, right)])):
                samples = hashes[(task, left)][digest] + hashes[(task, right)][digest]
                issues.append(Issue(task, f"{left}/{right}", "", "cross_split_exact_duplicate", "warning", ",".join(samples)))

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "dry_run": dry_run,
        "data_root": str(data_root.resolve()), "output_root": str(output_root.resolve()),
        "config": config, "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pillow": Image.__version__},
        "inventory": inventory, "issue_counts": dict(Counter(item.issue_type for item in issues)),
        "status": "fail" if any(item.severity == "error" for item in issues) else ("warning" if issues else "pass"),
    }
    if not dry_run:
        reports = output_root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "inventory.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (reports / "issues.json").write_text(json.dumps([asdict(item) for item in issues], indent=2), encoding="utf-8")
        fields = ["sample_id", "task", "split", "source_image_path", "source_annotation_path", "processed_image_path",
                  "processed_label_path", "width", "height", "channels", "annotation_type", "annotation_status",
                  "pixel_spacing_x_mm", "pixel_spacing_y_mm", "spacing_status", "preprocessing_config_version",
                  "validation_status", "exclusion_reason", "source_sha256"]
        for task, rows in manifests.items():
            _write_csv(output_root / "manifests" / f"{task}.csv", rows, fields)
        if previews:
            cell = (size[0], size[1] + 24)
            columns = 3
            sheet = Image.new("RGB", (cell[0] * columns, cell[1] * ((len(previews) + columns - 1) // columns)), "white")
            draw = ImageDraw.Draw(sheet)
            for idx, (task, split, sample, preview) in enumerate(previews):
                x, y = (idx % columns) * cell[0], (idx // columns) * cell[1]
                sheet.paste(preview, (x, y + 24)); draw.text((x + 4, y + 4), f"{task}/{split} {sample}", fill="black")
            qa = output_root / "qa"; qa.mkdir(parents=True, exist_ok=True); sheet.save(qa / "contact_sheet.jpg", quality=90)
        stages = {
            "raw_medical_image": "complete: source PNG retained unchanged and SHA-256 recorded",
            "validation": "complete: decode, dimensions, schema, mapping, coordinates, categories, and duplicates checked",
            "normalization": "complete at model input: float32 intensity scaling to [0,1]",
            "noise_reduction": "implemented at model input: configurable 3x3 median filter",
            "contrast_enhancement": "implemented at model input: configurable clipped autocontrast",
            "roi_extraction": "implemented for explicit ROIs with aligned mask crop; not automatically inferred from ground truth",
            "model_input": "complete: single-channel [1,H,W] float32 tensor preparation",
            "slice_selection": "not applicable: ARCADE provides independent 2D angiography PNGs with no ordered slice metadata",
            "2d_preparation": "complete",
            "3d_volume_preparation": "supported only for explicitly ordered slices with supplied voxel spacing; not run on ARCADE",
            "data_augmentation": "implemented training-only: seeded small-angle rotation with nearest-neighbor masks",
            "image_registration": "not required/not run: no paired temporal or multimodal registration target is defined",
            "pixel_voxel_spacing": "audited and preserved as unavailable; source PNG/COCO records contain no physical spacing",
        }
        (reports / "pipeline_stages.json").write_text(json.dumps(stages, indent=2), encoding="utf-8")
    LOG.info("status=%s samples=%d issues=%d", summary["status"], sum(map(len, manifests.values())), len(issues))
    return summary
