import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"D:\artery_app\data\arcade\stenosis")
OUT = Path(r"D:\artery_app\data\crops")
STENOSIS_ID = 26
SIZE = 64          # every crop is resized to 64x64
PAD = 8            # extra pixels around each box
NEG_PER_POS = 2    # normal crops per stenosis crop
random.seed(0)


def overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def save_crop(img, box, path):
    x, y, w, h = [int(round(v)) for v in box]
    W, H = img.size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return False
    img.crop((x0, y0, x1, y1)).resize((SIZE, SIZE)).save(path)
    return True


def build(split):
    sdir = ROOT / split
    if not sdir.exists():
        print(f"[{split}] folder not found, skipping")
        return
    ann_file = next((sdir / "annotations").glob("*.json"))
    data = json.load(open(ann_file))
    boxes = {}
    for a in data["annotations"]:
        if a["category_id"] == STENOSIS_ID:
            boxes.setdefault(a["image_id"], []).append(a["bbox"])
    sizes = [(b[2], b[3]) for bl in boxes.values() for b in bl]

    for cls in ("stenosis", "normal"):
        (OUT / split / cls).mkdir(parents=True, exist_ok=True)

    n_pos = n_neg = 0
    for im in data["images"]:
        if im["id"] not in boxes:
            continue                      # only images with a stenosis box
        img = Image.open(sdir / "images" / im["file_name"]).convert("L")
        W, H = img.size
        pos = boxes[im["id"]]

        for b in pos:                     # stenosis crops (padded)
            pb = [b[0] - PAD, b[1] - PAD, b[2] + 2 * PAD, b[3] + 2 * PAD]
            if save_crop(img, pb, OUT / split / "stenosis" / f"{im['id']}_{n_pos}.png"):
                n_pos += 1

        made = 0                          # normal crops: no overlap with any stenosis box
        for _ in range(60):
            if made >= NEG_PER_POS * len(pos):
                break
            w, h = random.choice(sizes)
            w, h = w + 2 * PAD, h + 2 * PAD
            x, y = random.randint(0, int(W - w)), random.randint(0, int(H - h))
            if any(overlaps((x, y, w, h), b) for b in pos):
                continue
            patch = np.array(img.crop((x, y, x + int(w), y + int(h))))
            if patch.std() < 12:          # skip flat background
                continue
            if save_crop(img, (x, y, w, h), OUT / split / "normal" / f"{im['id']}_{n_neg}.png"):
                n_neg += 1
                made += 1
    print(f"[{split}] stenosis crops: {n_pos} | normal crops: {n_neg}")


if __name__ == "__main__":
    for s in (sys.argv[1:] or ["train", "val", "test"]):
        build(s)