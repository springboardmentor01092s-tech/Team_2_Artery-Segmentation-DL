"""Small two-hidden-layer neural baseline with safe NumPy weight loading."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .analysis_model import prepare_input


def pixel_features(path: Path | Image.Image) -> np.ndarray:
    image = prepare_input(path)[0]
    padded = np.pad(image, 2, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (5, 5))
    patches = windows.reshape(-1, 25)
    height, width = image.shape
    y, x = np.indices((height, width))
    positions = np.stack((x.ravel() / width, y.ravel() / height), axis=1)
    return np.concatenate((patches, positions), axis=1).astype(np.float32)


def predict(path: Path, weights: Path) -> np.ndarray:
    features = pixel_features(path)
    with np.load(weights, allow_pickle=False) as data:
        x = (features - data["mean"]) / data["scale"]
        for index in range(3):
            x = x @ data[f"coef{index}"] + data[f"intercept{index}"]
            if index < 2:
                x = np.maximum(x, 0)
        probability = 1 / (1 + np.exp(-np.clip(x, -30, 30)))
        threshold = float(data["threshold"])
    return (probability.reshape(128, 128) >= threshold)
