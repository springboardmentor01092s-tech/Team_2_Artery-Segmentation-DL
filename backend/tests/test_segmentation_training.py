from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image
from torch.utils.data import DataLoader, TensorDataset

from ml.preprocessing.pipeline import rasterize
from scripts.train_segmentation_models import (
    _pixel_digest,
    dice_loss,
    exclude_training_validation_duplicates,
    score,
)


def test_pixel_digest_matches_same_pixels_with_different_png_encoding(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    image = Image.new("RGB", (12, 9), (20, 80, 140))
    image.save(first, compress_level=0)
    image.save(second, compress_level=9)

    assert first.read_bytes() != second.read_bytes()
    assert _pixel_digest(first) == _pixel_digest(second)


def test_exact_validation_duplicate_is_removed_from_train_without_removing_validation(tmp_path):
    train = tmp_path / "raw-train"
    validation = tmp_path / "raw-validation"
    processed = tmp_path / "processed-train"
    train.mkdir()
    validation.mkdir()
    processed.mkdir()

    Image.new("RGB", (8, 8), (255, 0, 0)).save(train / "duplicate.png")
    Image.new("RGB", (8, 8), (0, 255, 0)).save(train / "keep.png")
    Image.new("RGB", (8, 8), (255, 0, 0)).save(validation / "different-name.png")
    (processed / "duplicate.png").touch()
    (processed / "keep.png").touch()

    kept, excluded = exclude_training_validation_duplicates(
        sorted(processed.glob("*.png")), train, validation
    )

    assert [path.name for path in kept] == ["keep.png"]
    assert excluded == ["duplicate.png"]


def test_rasterization_preserves_syntax_categories_and_stenosis_union():
    image_row = {"width": 12, "height": 12}
    annotations = [
        {"category_id": 5, "segmentation": [[1, 1, 8, 1, 8, 8, 1, 8]]},
        {"category_id": 6, "segmentation": [[4, 4, 10, 4, 10, 10, 4, 10]]},
    ]

    syntax = np.asarray(rasterize(image_row, annotations, "syntax"))
    stenosis = np.asarray(rasterize(image_row, annotations, "stenosis"))

    assert set(np.unique(syntax)) == {0, 5, 6}
    assert set(np.unique(stenosis)) == {0, 1}
    assert stenosis[5, 5] == 1
    assert syntax[2, 2] == 5
    assert syntax[9, 9] == 6


def test_dice_loss_is_finite_and_differentiable_for_binary_targets():
    logits = torch.zeros((1, 1, 2, 2), requires_grad=True)
    targets = torch.ones((1, 1, 2, 2))

    loss = dice_loss(logits, targets)
    loss.backward()

    assert float(loss.detach()) == pytest.approx(2 / 7, abs=1e-6)
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()
    assert torch.count_nonzero(logits.grad) > 0


def test_binary_pixel_score_returns_perfect_metrics_for_perfect_logits():
    targets = torch.tensor([[[[1.0, 0.0], [0.0, 1.0]]]])
    logits = torch.where(targets > 0, 10.0, -10.0)

    class FixedModel(torch.nn.Module):
        def forward(self, images):
            return logits.expand(images.shape[0], -1, -1, -1)

    loader = DataLoader(TensorDataset(torch.zeros_like(targets), targets), batch_size=1)
    metrics = score(FixedModel(), loader, "cpu", 1.0, thresholds=(0.5,))

    for metric in ("dice", "iou", "precision", "recall", "sensitivity", "specificity", "pixel_accuracy", "auc_roc"):
        assert metrics[metric] == pytest.approx(1.0)
