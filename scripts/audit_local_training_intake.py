"""Read-only source audit; write a reproducible intake report, never modify labels."""
import collections
import gzip
import json
import struct
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def audit():
    report = {"datasets": {}, "policy": {
        "raw_sources_modified": False, "modalities_merged": False,
        "test_set_for_tuning": False, "training_complete": False}}
    dca = ROOT / "Database_134_Angiograms"
    rows, issues = [], []
    for image in sorted(dca.glob("*.pgm")):
        if image.stem.endswith("_gt"):
            continue
        mask = image.with_name(image.stem + "_gt.pgm")
        if not mask.exists():
            issues.append(f"missing mask: {image.name}")
            continue
        with Image.open(image) as im, Image.open(mask) as gt:
            im.load(); gt.load()
            values = np.unique(np.asarray(gt)).tolist()
            if im.size != gt.size:
                issues.append(f"shape mismatch: {image.name}")
            rows.append({"image": str(image.relative_to(ROOT)), "mask": str(mask.relative_to(ROOT)),
                         "size": im.size, "mask_values": values})
    report["datasets"]["dca1"] = {"pairs": len(rows), "issues": issues, "manifest": rows,
        "gates": ["Verify reuse licence", "Establish patient-disjoint partition; no split inferred from filenames"]}
    cad = ROOT / "CADICA/selectedVideos"
    selected, classes, errors = [], collections.Counter(), []
    for listing in sorted(cad.glob("p*/v*/*_selectedFrames.txt")):
        video = listing.parent
        for name in listing.read_text().split():
            stem = Path(name).stem
            image = video / "input" / (stem + ".png")
            if not image.exists():
                errors.append(f"missing selected image: {image.relative_to(ROOT)}")
                continue
            ann = video / "groundtruth" / (stem + ".txt")
            boxes = []
            if ann.exists():
                for line in ann.read_text().splitlines():
                    fields = line.split()
                    if not fields:
                        continue
                    if len(fields) != 5:
                        errors.append(f"unexpected annotation: {ann.relative_to(ROOT)}")
                        continue
                    x, y, w, h = map(float, fields[:4])
                    with Image.open(image) as im:
                        width, height = im.size
                    if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
                        errors.append(f"invalid box: {ann.relative_to(ROOT)}")
                    classes[fields[4]] += 1
                    boxes.append({"xywh": [x,y,w,h], "source_class": fields[4]})
            else:
                negatives = video.parent / "nonlesionVideos.txt"
                if not negatives.exists() or video.name not in negatives.read_text().split():
                    errors.append(f"unverified negative: {image.relative_to(ROOT)}")
            selected.append({"image": str(image.relative_to(ROOT)), "patient": video.parent.name,
                             "video": video.name, "boxes": boxes})
    report["datasets"]["cadica"] = {"selected_frames": len(selected),
        "patients": len({r["patient"] for r in selected}), "classes": dict(classes),
        "issues": errors, "manifest": selected,
        "gates": ["Verify local release provenance and licence", "Resolve intake issues before patient-level splitting"]}
    msd = ROOT / "Task08_HepaticVessel"
    meta = json.loads((msd / "dataset.json").read_text())
    missing, geometry, errors, warnings = [], [], [], []
    def header(path):
        with gzip.open(path, "rb") as stream:
            data = stream.read(348)
        endian = "<" if struct.unpack("<i", data[:4])[0] == 348 else ">"
        return {"dim": struct.unpack(endian+"8h", data[40:56]),
                "pixdim": struct.unpack(endian+"8f", data[76:108]),
                "transform_bytes": data[252:348].hex()}
    for entry in meta["training"]:
        paths = [msd / entry[k] for k in ("image", "label")]
        if not all(p.is_file() for p in paths):
            missing.extend(str(p.relative_to(ROOT)) for p in paths if not p.is_file())
            continue
        try:
            image, label = map(header, paths)
            if image != label:
                warnings.append(f"Header difference requires affine comparison: {paths[0].name}")
            geometry.append({"case": paths[0].name, **image})
        except Exception as exc:
            errors.append(f"{paths[0].name}: {exc}")
    report["datasets"]["msd_hepaticvessel"] = {
        "licence": meta["licence"], "labels": meta["labels"], "expected_training": meta["numTraining"],
        "paired_headers_checked": len(geometry), "expected_test": meta["numTest"],
        "test_present": sum((msd/p).is_file() for p in meta["test"]),
        "missing": missing, "issues": errors, "header_warnings": warnings, "geometry": geometry,
        "gates": ["Full voxel integrity and label-value audit still required", "3D-only pipeline; hold official test separate"]}
    nested = ROOT / "Angiographic dataset for stenosis detection/Stenosis detection.zip"
    with zipfile.ZipFile(nested) as archive:
        names = archive.namelist()
        report["datasets"]["mendeley_stenosis"] = {"archive_entries": len(names),
            "extensions": dict(collections.Counter(Path(n).suffix.lower() for n in names if not n.endswith('/'))),
            "sample_paths": names[:40], "annotation_samples": {
                n: archive.read(n).decode("utf-8", errors="replace")[:2000]
                for n in names if Path(n).suffix.lower() in {".txt", ".csv", ".json", ".xml"}
                and archive.getinfo(n).file_size < 10000 and not n.startswith("__MACOSX")
            }, "gates": ["Extract and validate annotations", "Verify patient mapping and licence"]}
    target = ROOT / "reports/local_training_intake.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=2))
    print(target)
    for name, row in report["datasets"].items():
        print(name, {k:v for k,v in row.items() if k not in {"manifest", "geometry", "annotation_samples", "sample_paths"}})


if __name__ == "__main__":
    audit()
