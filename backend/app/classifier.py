from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

WEIGHTS = Path(__file__).resolve().parent.parent / "weights" / "stenosis_classifier.pt"
SIZE = 64
_model = None


def _block(i, o):
    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o),
                         nn.ReLU(), nn.MaxPool2d(2))


def _build():
    return nn.Sequential(
        _block(1, 16), _block(16, 32), _block(32, 64), _block(64, 128),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Dropout(0.3), nn.Linear(128, 2),
    )


def load_model():
    global _model
    if _model is None:
        m = _build()
        m.load_state_dict(torch.load(WEIGHTS, map_location="cpu"))
        m.eval()
        _model = m
    return _model


def stenosis_probability(img: Image.Image, box) -> float:
    """Probability (0-1) that the box region of the image is a real stenosis."""
    x, y, w, h = [int(round(v)) for v in box]
    W, H = img.size
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return 0.0
    crop = img.convert("L").crop((x0, y0, x1, y1)).resize((SIZE, SIZE))
    a = (np.asarray(crop, dtype=np.float32) / 255.0 - 0.5) / 0.5
    t = torch.tensor(a)[None, None]
    with torch.no_grad():
        p = torch.softmax(load_model()(t), 1)[0, 1].item()
    return round(p, 3)