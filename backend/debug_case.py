import glob
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from app.stenosis_pipeline import load_mask, url_to_path
from app.classifier import stenosis_probability

BASE = Path(__file__).resolve().parent
case_id = int(sys.argv[1]) if len(sys.argv) > 1 else 3
R = f"/uploads/results/case_{case_id}"

sten = load_mask(url_to_path(f"{R}_stenosis_mask.png"))
vess = load_mask(url_to_path(f"{R}_syntax_mask.png"))
scans = [f for f in glob.glob(str(BASE / "uploads" / f"case_{case_id}_*"))
         if f.lower().endswith((".png", ".jpg", ".jpeg"))]
scans.sort(key=lambda f: Path(f).stat().st_mtime)
scan = Image.open(scans[-1]).convert("L").resize((sten.shape[1], sten.shape[0]))

lab, n = ndimage.label(sten, structure=np.ones((3, 3)))
print("blobs in stenosis mask:", n)
for i, sl in enumerate(ndimage.find_objects(lab), start=1):
    comp = lab[sl] == i
    area = int(comp.sum())
    overlap = float((comp & vess[sl]).sum()) / area
    x0, y0 = sl[1].start, sl[0].start
    w, h = sl[1].stop - x0, sl[0].stop - y0
    p = stenosis_probability(scan, [x0 - 8, y0 - 8, w + 16, h + 16])
    print(f"blob {i}: box=({x0},{y0},{w},{h}) area={area} "
          f"on_vessel={overlap:.2f} classifier={p}")