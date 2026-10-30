import os
import numpy as np
import torch
import torch.nn as nn
from PIL import Image

MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)

MODEL_INFO = {
    "syntax": {"file": "best_syntax.pt", "size": 256, "threshold": 0.5, "version": "unet-artery-v1"},
    "stenosis": {"file": "best_stenosis.pt", "size": 256, "threshold": 0.5, "version": "unet-stenosis-v1"},
}


def block(i, o):
    return nn.Sequential(
        nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
        nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
    )


class UNet(nn.Module):
    def __init__(self, base=32):
        super().__init__()
        self.e1 = block(1, base)
        self.e2 = block(base, base * 2)
        self.e3 = block(base * 2, base * 4)
        self.e4 = block(base * 4, base * 8)
        self.bott = block(base * 8, base * 16)
        self.pool = nn.MaxPool2d(2)
        self.u4 = nn.ConvTranspose2d(base * 16, base * 8, 2, stride=2)
        self.d4 = block(base * 16, base * 8)
        self.u3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.d3 = block(base * 8, base * 4)
        self.u2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.d2 = block(base * 4, base * 2)
        self.u1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.d1 = block(base * 2, base)
        self.out = nn.Conv2d(base, 1, 1)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(self.pool(e1))
        e3 = self.e3(self.pool(e2))
        e4 = self.e4(self.pool(e3))
        b = self.bott(self.pool(e4))
        d4 = self.d4(torch.cat([self.u4(b), e4], 1))
        d3 = self.d3(torch.cat([self.u3(d4), e3], 1))
        d2 = self.d2(torch.cat([self.u2(d3), e2], 1))
        d1 = self.d1(torch.cat([self.u1(d2), e1], 1))
        return self.out(d1)


_cache = {}


def get_model(task):
    if task not in _cache:
        path = os.path.join(MODELS_DIR, MODEL_INFO[task]["file"])
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        model = UNet()
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
        _cache[task] = model
    return _cache[task]


def predict_mask(image_path, task, out_dir, prefix):
    info = MODEL_INFO[task]
    model = get_model(task)
    os.makedirs(out_dir, exist_ok=True)

    original = Image.open(image_path).convert("L")
    small = original.resize((info["size"], info["size"]), Image.BILINEAR)
    x = torch.from_numpy(np.asarray(small, dtype=np.float32) / 255.0)
    x = x.unsqueeze(0).unsqueeze(0)

    with torch.no_grad():
        prob = torch.sigmoid(model(x))[0, 0].numpy()

    mask_small = (prob > info["threshold"]).astype(np.uint8) * 255
    mask = Image.fromarray(mask_small).resize(original.size, Image.NEAREST)
    mask_arr = np.asarray(mask) > 127

    rgb = np.stack([np.asarray(original)] * 3, axis=-1).astype(np.float32)
    red = np.array([255, 40, 40], dtype=np.float32)
    rgb[mask_arr] = rgb[mask_arr] * 0.55 + red * 0.45
    overlay = Image.fromarray(rgb.astype(np.uint8))

    mask_name = f"{prefix}_mask.png"
    overlay_name = f"{prefix}_overlay.png"
    mask.save(os.path.join(out_dir, mask_name))
    overlay.save(os.path.join(out_dir, overlay_name))

    return {
        "mask": mask_name,
        "overlay": overlay_name,
        "foreground_percent": round(float(mask_arr.mean() * 100), 2),
        "max_probability": round(float(prob.max()), 3),
        "threshold": info["threshold"],
        "model_version": info["version"],
    }