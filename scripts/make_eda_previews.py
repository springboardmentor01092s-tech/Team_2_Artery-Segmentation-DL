"""Create two labeled samples for visual verification of ARCADE polygons."""
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "eda"


def preview(task: str):
    base = ROOT / "arcade" / task / "train"
    data = json.loads((base / "annotations" / "train.json").read_text())
    by_image = defaultdict(list)
    for annotation in data["annotations"]:
        by_image[str(annotation["image_id"])].append(annotation)
    # Pick a frame with multiple annotations for a useful visual check.
    item = max(data["images"][:100], key=lambda row: len(by_image[str(row["id"])]))
    image = Image.open(base / "images" / item["file_name"]).convert("RGB")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for annotation in by_image[str(item["id"])]:
        color = (32, 181, 195, 85) if task == "syntax" else (240, 88, 62, 110)
        outline = (17, 143, 157, 255) if task == "syntax" else (214, 49, 35, 255)
        for polygon in annotation["segmentation"]:
            points = [(polygon[i], polygon[i + 1]) for i in range(0, len(polygon), 2)]
            if len(points) >= 3:
                draw.polygon(points, fill=color, outline=outline, width=2)
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / f"{task}_train_example.png"
    Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB").save(output)
    print(f"{task}: {item['file_name']} with {len(by_image[str(item['id'])])} annotations -> {output}")


if __name__ == "__main__":
    preview("syntax")
    preview("stenosis")
