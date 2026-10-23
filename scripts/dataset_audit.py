"""Read-only ARCADE inventory and annotation integrity check."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "arcade"


def audit():
    for task in ("syntax", "stenosis"):
        print(f"\n{task.upper()}")
        hashes = {}
        for split in ("train", "val", "test"):
            base = ROOT / task / split
            data = json.loads((base / "annotations" / f"{split}.json").read_text())
            images = {p.name: p for p in (base / "images").glob("*.png")}
            listed = {item["file_name"] for item in data["images"]}
            ids = {str(item["id"]) for item in data["images"]}
            categories = Counter(str(item["category_id"]) for item in data["annotations"])
            missing = listed - set(images)
            unlisted = set(images) - listed
            bad_refs = sum(str(item["image_id"]) not in ids for item in data["annotations"])
            empty_polygons = sum(not item.get("segmentation") for item in data["annotations"])
            print(
                f"{split}: files={len(images)} listed={len(listed)} annotations={len(data['annotations'])} "
                f"missing={len(missing)} unlisted={len(unlisted)} bad_refs={bad_refs} "
                f"empty_polygons={empty_polygons} classes={dict(categories)}"
            )
            hashes[split] = {hashlib.sha256(p.read_bytes()).hexdigest() for p in images.values()}
        for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
            print(f"identical images in {left}/{right}: {len(hashes[left] & hashes[right])}")


if __name__ == "__main__":
    audit()
