"""Generate reproducible exploratory analysis for the extracted ARCADE dataset."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TASKS = ("syntax", "stenosis")
SPLITS = ("train", "val", "test")


def _summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "q1": None, "median": None, "mean": None, "q3": None, "max": None}
    array = np.asarray(values, dtype=np.float64)
    return {"count": len(values), "min": float(array.min()), "q1": float(np.quantile(array, .25)),
            "median": float(np.median(array)), "mean": float(array.mean()),
            "q3": float(np.quantile(array, .75)), "max": float(array.max())}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bar_chart(title: str, labels: list[str], values: list[float], path: Path,
               width: int = 1200, height: int = 650) -> None:
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas); font = ImageFont.load_default()
    draw.text((40, 20), title, fill="#172033", font=font)
    left, top, right, bottom = 75, 60, width - 25, height - 90
    draw.line((left, top, left, bottom, right, bottom), fill="#6b7280", width=2)
    maximum = max(values, default=1) or 1
    slot = (right - left) / max(len(values), 1)
    for index, (label, value) in enumerate(zip(labels, values)):
        x0 = left + index * slot + slot * .12; x1 = left + (index + 1) * slot - slot * .12
        y0 = bottom - (value / maximum) * (bottom - top - 25)
        draw.rectangle((x0, y0, x1, bottom), fill="#1597a5")
        draw.text((x0, max(top, y0 - 14)), f"{value:g}", fill="#172033", font=font)
        draw.text((x0, bottom + 8), label[:14], fill="#172033", font=font)
    path.parent.mkdir(parents=True, exist_ok=True); canvas.save(path)


def analyze(data_root: Path, output_root: Path) -> dict[str, Any]:
    """Analyze every ARCADE image and annotation, then write reports and charts."""
    records: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []
    hashes: dict[tuple[str, str], dict[str, list[str]]] = {}
    global_hashes: dict[str, list[str]] = defaultdict(list)
    intensity_histogram = np.zeros(256, dtype=np.int64)

    for task in TASKS:
        for split in SPLITS:
            base = data_root / task / split
            coco = json.loads((base / "annotations" / f"{split}.json").read_text(encoding="utf-8"))
            categories = {int(row["id"]): str(row["name"]) for row in coco["categories"]}
            annotations: dict[Any, list[dict[str, Any]]] = defaultdict(list)
            class_counts = Counter()
            for annotation in coco["annotations"]:
                annotations[annotation["image_id"]].append(annotation)
                class_counts[int(annotation["category_id"])] += 1
            for category_id in sorted(categories):
                count = class_counts[category_id]
                if count:
                    class_rows.append({"task": task, "split": split, "category_id": category_id,
                                       "category_name": categories[category_id], "annotation_count": count})

            ann_counts: list[float] = []; areas: list[float] = []; bbox_widths: list[float] = []
            bbox_heights: list[float] = []; polygon_vertices: list[float] = []
            image_means: list[float] = []; image_stds: list[float] = []
            modes = Counter(); dimensions = Counter(); empty_images = 0
            split_hashes: dict[str, list[str]] = defaultdict(list)
            for image_row in coco["images"]:
                sample = f"{task}_{split}_{image_row['id']}"
                path = base / "images" / image_row["file_name"]
                with Image.open(path) as opened:
                    modes[opened.mode] += 1; dimensions[f"{opened.width}x{opened.height}"] += 1
                    pixels = np.asarray(opened.convert("L"), dtype=np.uint8)
                image_means.append(float(pixels.mean())); image_stds.append(float(pixels.std()))
                intensity_histogram += np.bincount(pixels.ravel(), minlength=256)
                digest = _sha256(path); split_hashes[digest].append(sample); global_hashes[digest].append(sample)
                sample_annotations = annotations[image_row["id"]]
                ann_counts.append(float(len(sample_annotations)))
                if not sample_annotations: empty_images += 1
                for annotation in sample_annotations:
                    if "area" in annotation: areas.append(float(annotation["area"]))
                    if len(annotation.get("bbox", [])) == 4:
                        bbox_widths.append(float(annotation["bbox"][2])); bbox_heights.append(float(annotation["bbox"][3]))
                    for polygon in annotation.get("segmentation", []): polygon_vertices.append(len(polygon) / 2)
            hashes[(task, split)] = split_hashes
            records.append({"task": task, "split": split, "images": len(coco["images"]),
                            "annotations": len(coco["annotations"]), "annotated_images": len(coco["images"]) - empty_images,
                            "empty_images": empty_images, "category_count_used": len(class_counts),
                            "dimensions": dict(dimensions), "modes": dict(modes),
                            "annotations_per_image": _summary(ann_counts), "annotation_area_px2": _summary(areas),
                            "bbox_width_px": _summary(bbox_widths), "bbox_height_px": _summary(bbox_heights),
                            "polygon_vertices": _summary(polygon_vertices), "image_mean_intensity": _summary(image_means),
                            "image_std_intensity": _summary(image_stds)})

    duplicate_rows: list[dict[str, str]] = []
    for task in TASKS:
        for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
            shared = set(hashes[(task, left)]) & set(hashes[(task, right)])
            for digest in sorted(shared):
                duplicate_rows.append({"scope": "within_task_cross_split", "sha256": digest,
                                       "samples": "|".join(hashes[(task, left)][digest] + hashes[(task, right)][digest])})
    for digest, samples in global_hashes.items():
        tasks = {sample.split("_", 1)[0] for sample in samples}
        if len(tasks) > 1:
            duplicate_rows.append({"scope": "cross_task", "sha256": digest, "samples": "|".join(samples)})

    output_root.mkdir(parents=True, exist_ok=True)
    report = {"dataset": "ARCADE", "source_root": str(data_root.resolve()), "splits": records,
              "totals": {"images": sum(row["images"] for row in records),
                         "annotations": sum(row["annotations"] for row in records)},
              "exact_duplicate_groups": {"within_task_cross_split": sum(row["scope"] == "within_task_cross_split" for row in duplicate_rows),
                                         "cross_task": sum(row["scope"] == "cross_task" for row in duplicate_rows)},
              "limitations": ["No verified patient/study grouping is present in inspected COCO metadata.",
                              "Exact hashes do not detect near-duplicate frames.",
                              "Physical pixel spacing is absent from PNG/COCO metadata."]}
    (output_root / "eda_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for name, rows, fields in (("class_distribution.csv", class_rows, ["task", "split", "category_id", "category_name", "annotation_count"]),
                               ("exact_duplicates.csv", duplicate_rows, ["scope", "sha256", "samples"])):
        with (output_root / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    _bar_chart("Images by task and official split", [f"{r['task']}-{r['split']}" for r in records],
               [r["images"] for r in records], output_root / "split_distribution.png")
    syntax_train = [row for row in class_rows if row["task"] == "syntax" and row["split"] == "train"]
    _bar_chart("Syntax train annotations by source category", [str(r["category_name"]) for r in syntax_train],
               [r["annotation_count"] for r in syntax_train], output_root / "syntax_train_class_distribution.png")
    histogram_values = intensity_histogram.astype(float)
    _bar_chart("All-image grayscale intensity histogram (16-bin)", [str(i) for i in range(0, 256, 16)],
               [float(histogram_values[i:i+16].sum()) for i in range(0, 256, 16)], output_root / "intensity_histogram.png")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("arcade"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/eda"))
    args = parser.parse_args()
    report = analyze(args.data_root, args.output_root)
    print(json.dumps({"totals": report["totals"], "exact_duplicate_groups": report["exact_duplicate_groups"]}, indent=2))


if __name__ == "__main__":
    main()
