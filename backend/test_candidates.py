from PIL import Image, ImageDraw
from app.stenosis_pipeline import load_mask, url_to_path, extract_candidates

sten = load_mask(url_to_path("/uploads/results/case_2_stenosis_mask.png"))

cands = extract_candidates(sten)
print("candidates found:", len(cands))
for c in cands:
    print(c)

img = Image.open(url_to_path("/uploads/results/case_2_stenosis_overlay.png")).convert("RGB")
d = ImageDraw.Draw(img)
for c in cands:
    x, y, w, h = c.bbox
    d.rectangle([x, y, x + w, y + h], outline="red", width=3)
img.save("box_check.png")
print("saved box_check.png")