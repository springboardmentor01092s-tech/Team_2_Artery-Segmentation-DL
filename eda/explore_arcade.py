
import json
from pathlib import Path
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image

DATA_DIR = Path(r"D:\artery_app\data\arcade")
OUT_DIR = Path(r"D:\artery_app\eda_output")
OUT_DIR.mkdir(exist_ok=True)

image_index = {
    p.name: p
    for p in DATA_DIR.rglob("*")
    if p.suffix.lower() in (".png", ".jpg", ".jpeg")
}
print("Image files found:", sum(1 for _ in DATA_DIR.rglob("*.png")))
json_files = sorted(DATA_DIR.rglob("*.json"))
print("JSON files found:", len(json_files))

for jf in json_files:
    with open(jf, encoding="utf-8") as f:
        data = json.load(f)
    if not all(k in data for k in ("images", "annotations", "categories")):
        continue

    images = data["images"]
    anns = data["annotations"]
    cats = {c["id"]: c["name"] for c in data["categories"]}
    rel = jf.relative_to(DATA_DIR)

    print("=" * 60)
    print("File:", rel)
    print("Images:", len(images), "| Annotations:", len(anns), "| Categories:", len(cats))
    print("Image sizes:", dict(Counter((im["width"], im["height"]) for im in images)))
    per_cat = Counter(cats.get(a["category_id"], a["category_id"]) for a in anns)
    print("Top categories:", per_cat.most_common(10))

    ann_by_img = {}
    for a in anns:
        ann_by_img.setdefault(a["image_id"], []).append(a)
    print("Images with annotations:", len(ann_by_img), "of", len(images))

    tag = "_".join(rel.with_suffix("").parts)
    shown = 0
    for im in images:
        if im["id"] not in ann_by_img:
            continue
        path = jf.parent.parent / "images" / Path(im["file_name"]).name
        if not path.exists():
            continue
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(Image.open(path).convert("L"), cmap="gray")
        for a in ann_by_img[im["id"]]:
            seg = a.get("segmentation")
            if isinstance(seg, list):
                for poly in seg:
                    pts = [(poly[i], poly[i + 1]) for i in range(0, len(poly) - 1, 2)]
                    ax.add_patch(Polygon(pts, fill=False, edgecolor="red", linewidth=1.5))
        ax.set_title(f"{tag} | {im['file_name']}", fontsize=8)
        ax.axis("off")
        fig.savefig(OUT_DIR / f"{tag}_{shown}.png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        shown += 1
        if shown == 3:
            break

print("=" * 60)
print("Done. Open the folder:", OUT_DIR)