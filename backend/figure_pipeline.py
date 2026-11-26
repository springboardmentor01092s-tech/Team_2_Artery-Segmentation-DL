import glob
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from app.stenosis_pipeline import load_mask, url_to_path, extract_candidates

BASE = Path(__file__).resolve().parent          # the backend folder
OUT_DIR = BASE / "uploads" / "pipeline_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

case_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
R = f"/uploads/results/case_{case_id}"

sten = load_mask(url_to_path(f"{R}_stenosis_mask.png"))
vess = load_mask(url_to_path(f"{R}_syntax_mask.png"))
cands = extract_candidates(sten, vess)
H, W = sten.shape

scans = [f for f in glob.glob(str(BASE / "uploads" / f"case_{case_id}_*"))
         if f.lower().endswith((".png", ".jpg", ".jpeg"))]
scans.sort(key=lambda f: Path(f).stat().st_mtime)   # oldest -> newest
panels = [
    ("1. Scan", Image.open(scans[0])),
    ("2. Vessel mask", Image.open(url_to_path(f"{R}_syntax_mask.png"))),
    ("3. Centerline", Image.open(url_to_path(f"{R}_syntax_centerline.png"))),
    ("4. Stenosis mask", Image.open(url_to_path(f"{R}_stenosis_mask.png"))),
    ("5. Candidates", Image.open(url_to_path(f"{R}_stenosis_overlay.png"))),
]

TITLE = 28
fig = Image.new("RGB", (W * len(panels), H + TITLE), "white")
for i, (name, im) in enumerate(panels):
    im = im.convert("RGB").resize((W, H))
    if name.startswith("5"):
        d = ImageDraw.Draw(im)
        for c in cands:
            x, y, w, h = c.bbox
            d.rectangle([x, y, x + w, y + h], outline="red", width=3)
            d.text((x + 4, y + 4), f"{c.score:.2f}", fill="red")
    fig.paste(im, (i * W, TITLE))
    ImageDraw.Draw(fig).text((i * W + 8, 8), name, fill="black")

out = OUT_DIR / f"case_{case_id}_pipeline_figure.png"
fig.save(out)
print("saved:", out, "| candidates:", len(cands))