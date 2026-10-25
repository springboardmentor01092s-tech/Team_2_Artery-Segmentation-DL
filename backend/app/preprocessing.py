import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps

MODEL_SIZE = 256


def run_pipeline(src_path: str, out_dir: str, prefix: str):
    os.makedirs(out_dir, exist_ok=True)
    stages = []

    def save(name, img):
        fname = f"{prefix}_{name}.png"
        img.save(os.path.join(out_dir, fname))
        stages.append({"name": name, "file": fname})

    # 1. Validation
    img = Image.open(src_path)
    img.verify()
    img = Image.open(src_path).convert("L")
    if min(img.size) < 64:
        raise ValueError("Image is too small (minimum 64 px)")
    save("1_original", img)

    # 2. Normalization (clip 1-99 percentile, scale to 0-255)
    arr = np.asarray(img, dtype=np.float32)
    lo, hi = np.percentile(arr, (1, 99))
    arr = np.clip((arr - lo) / max(hi - lo, 1e-6), 0, 1) * 255
    img = Image.fromarray(arr.astype(np.uint8))
    save("2_normalized", img)

    # 3. Noise reduction
    img = img.filter(ImageFilter.MedianFilter(3))
    save("3_denoised", img)

    # 4. Contrast enhancement
    img = ImageOps.equalize(img)
    save("4_contrast", img)

    # 5. ROI extraction (crop away empty border)
    arr = np.asarray(img)
    ys, xs = np.where(arr > 15)
    if len(ys) > 0:
        m = 8
        box = (
            max(xs.min() - m, 0),
            max(ys.min() - m, 0),
            min(xs.max() + m, img.width),
            min(ys.max() + m, img.height),
        )
        img = img.crop(box)
    save("5_roi", img)

    # 6. Model input (resize to training size)
    img = img.resize((MODEL_SIZE, MODEL_SIZE), Image.BILINEAR)
    save("6_model_input", img)
    return stages