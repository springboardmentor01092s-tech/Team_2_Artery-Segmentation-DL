import numpy as np
import torch
from PIL import Image, ImageDraw

from .classifier import load_model

SIZE = 64


def _crop(img: Image.Image, box):
    x, y, w, h = [int(round(v)) for v in box]
    W, H = img.size
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return None
    return img.convert("L").crop((x0, y0, x1, y1)).resize((SIZE, SIZE))


def _tensor(crop):
    a = (np.asarray(crop, dtype=np.float32) / 255.0 - 0.5) / 0.5
    return torch.tensor(a)[None, None]


def _jet(v):
    r = np.clip(1.5 - np.abs(4 * v - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * v - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * v - 1), 0, 1)
    return np.stack([r, g, b], -1)


def _cams(crop):
    """Return (Grad-CAM, Grad-CAM++) maps for the 'stenosis' score."""
    model = load_model()
    store = {}
    layer = model[3][2]                       # last ReLU, before the final pooling

    def hook(_m, _i, out):
        out.retain_grad()
        store["a"] = out

    handle = layer.register_forward_hook(hook)
    model.zero_grad()
    out = model(_tensor(crop))
    out[0, 1].backward()
    handle.remove()

    A = store["a"].detach()
    g = store["a"].grad.detach()

    # Grad-CAM: average the gradients per channel
    w = g.mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((w * A).sum(1))[0].numpy()

    # Grad-CAM++: pixel-wise weighting of the gradients
    g2 = g ** 2
    g3 = g2 * g
    sumA = A.sum(dim=(2, 3), keepdim=True)
    alpha = g2 / (2 * g2 + sumA * g3 + 1e-8)
    alpha = torch.where(g != 0, alpha, torch.zeros_like(alpha))
    wpp = (alpha * torch.relu(g)).sum(dim=(2, 3), keepdim=True)
    campp = torch.relu((wpp * A).sum(1))[0].numpy()
    return cam, campp


def _overlay(base, cam, size):
    cam = cam / (cam.max() + 1e-8)
    c = Image.fromarray((cam * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)
    v = np.asarray(c, dtype=np.float32) / 255.0
    alpha = (0.65 * v)[..., None]             # colour only where the model focused
    return (base * (1 - alpha) + _jet(v) * alpha).clip(0, 1)


def _label(arr, text):
    im = Image.fromarray((arr * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 16], fill=(0, 0, 0))
    d.text((4, 3), text, fill=(255, 255, 255))
    return im


def explain(img: Image.Image, box, size=192):
    """Crop | Grad-CAM | Grad-CAM++ side by side."""
    crop = _crop(img, box)
    if crop is None:
        return None
    cam, campp = _cams(crop)

    # display image: stretch the contrast and darken it so the vessel stands out
    base = np.asarray(crop.resize((size, size)), dtype=np.float32) / 255.0
    lo, hi = np.percentile(base, [1, 99])
    base = np.clip((base - lo) / (hi - lo + 1e-6), 0, 1) ** 2.2
    base = np.stack([base] * 3, -1)

    panels = [_label(base, "Crop"),
              _label(_overlay(base, cam, size), "Grad-CAM"),
              _label(_overlay(base, campp, size), "Grad-CAM++")]
    canvas = Image.new("RGB", (size * 3, size))
    for i, p in enumerate(panels):
        canvas.paste(p, (i * size, 0))
    return canvas