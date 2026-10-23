"""Model-input preparation kept separate from deterministic dataset conversion."""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image, ImageFilter, ImageOps


@dataclass(frozen=True)
class ModelInputConfig:
    """Conservative, reproducible model-input settings."""

    noise_reduction: bool = True
    median_filter_size: int = 3
    contrast_enhancement: bool = True
    contrast_clip_percent: float = 1.0


def prepare_2d_model_input(path: Path, config: ModelInputConfig = ModelInputConfig()) -> np.ndarray:
    """Return one grayscale angiogram as normalized float32 ``[1,H,W]`` data."""
    with Image.open(path) as opened:
        image = opened.convert("L")
    if config.noise_reduction:
        if config.median_filter_size < 3 or config.median_filter_size % 2 == 0:
            raise ValueError("median_filter_size must be an odd integer >= 3")
        image = image.filter(ImageFilter.MedianFilter(config.median_filter_size))
    if config.contrast_enhancement:
        image = ImageOps.autocontrast(image, cutoff=config.contrast_clip_percent)
    array = np.asarray(image, dtype=np.float32) / 255.0
    return array[np.newaxis, ...]


def extract_roi(image: Image.Image, box: tuple[int, int, int, int],
                mask: Image.Image | None = None) -> tuple[Image.Image, Image.Image | None]:
    """Crop an explicitly supplied ROI from an image and its aligned mask."""
    left, top, right, bottom = box
    if left < 0 or top < 0 or right > image.width or bottom > image.height or left >= right or top >= bottom:
        raise ValueError("ROI is outside the image or empty")
    if mask is not None and mask.size != image.size:
        raise ValueError("image and mask dimensions differ")
    return image.crop(box), mask.crop(box) if mask is not None else None


def augment_training_pair(image: Image.Image, mask: Image.Image, seed: int,
                          max_rotation_degrees: float = 5.0, *, split: str = "train") -> tuple[Image.Image, Image.Image]:
    """Apply a seeded, small rotation identically to a training image/mask pair."""
    if split != "train":
        raise ValueError("Augmentation is permitted only for the training split")
    if image.size != mask.size:
        raise ValueError("image and mask dimensions differ")
    angle = random.Random(seed).uniform(-max_rotation_degrees, max_rotation_degrees)
    augmented_image = image.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=0)
    augmented_mask = mask.rotate(angle, resample=Image.Resampling.NEAREST, fillcolor=0)
    return augmented_image, augmented_mask


def prepare_volume(slice_paths: Sequence[Path], spacing_mm: tuple[float, float, float] | None) -> np.ndarray:
    """Stack explicitly ordered 2D slices; refuses volumes without physical spacing."""
    if not slice_paths:
        raise ValueError("at least one ordered slice is required")
    if spacing_mm is None or any(value <= 0 for value in spacing_mm):
        raise ValueError("valid z/y/x voxel spacing is required for 3D preparation")
    slices = [prepare_2d_model_input(path)[0] for path in slice_paths]
    if len({item.shape for item in slices}) != 1:
        raise ValueError("all volume slices must have identical dimensions")
    return np.stack(slices, axis=0)
