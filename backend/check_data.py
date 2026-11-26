import json
from pathlib import Path

p = Path(r"D:\artery_app\data\arcade\stenosis\test\annotations\test.json")
d = json.load(open(p))
print("keys:", list(d.keys()))
print("images:", len(d["images"]), "| annotations:", len(d["annotations"]))
print("categories:", d.get("categories"))
print("first image:", d["images"][0])
print("first annotation:", {k: (v if k != "segmentation" else "...") for k, v in d["annotations"][0].items()})