from pathlib import Path

import numpy as np
import pytest

from app.segmentation_metrics import boundary_metrics, segmentation_metrics, summarize


def square(size, start, stop, ndim=2):
    m = np.zeros((size,) * ndim, dtype=bool)
    m[tuple(slice(start, stop) for _ in range(ndim))] = True
    return m


def test_identical_masks_have_zero_distance_and_perfect_overlap():
    m = square(32, 8, 20)
    r = segmentation_metrics(m, m)
    assert r["dice"] == 1 and r["iou"] == 1 and r["specificity"] == 1
    assert r["hausdorff"] == 0 and r["hd95"] == 0 and r["assd"] == 0


def test_known_shift_gives_known_hausdorff():
    a = square(40, 10, 20)
    b = np.roll(a, 3, axis=1)  # shift 3 pixels sideways
    r = boundary_metrics(a, b)
    assert r["hausdorff"] == pytest.approx(3.0)
    assert 0 < r["assd"] <= 3.0


def test_spacing_scales_distances_and_3d_supported():
    a = square(20, 5, 10, ndim=3)
    b = np.roll(a, 2, axis=0)
    r1 = boundary_metrics(a, b)
    r2 = boundary_metrics(a, b, spacing=(0.5, 0.5, 0.5))
    assert r2["hausdorff"] == pytest.approx(r1["hausdorff"] * 0.5)
    assert segmentation_metrics(a, b, spacing=(0.5, 0.5, 0.5))["distance_unit"] == "mm"


def test_empty_masks_are_undefined_not_zero():
    a = np.zeros((16, 16), bool)
    r = segmentation_metrics(a, square(16, 2, 6))
    assert r["hd95"] is None and r["hausdorff"] is None and r["dice"] == 0
    assert segmentation_metrics(a, a)["dice"] is None


def test_shape_mismatch_rejected():
    with pytest.raises(ValueError):
        segmentation_metrics(np.zeros((4, 4)), np.zeros((4, 5)))


def test_summary_reports_support():
    rows = [segmentation_metrics(square(16, 2, 8), square(16, 3, 9)), segmentation_metrics(np.zeros((16, 16), bool), square(16, 2, 6))]
    s = summarize(rows)
    assert s["cases"] == 2 and s["hd95_support"] == 1 and s["dice_support"] == 2


def test_training_copy_matches_application_module():
    root = Path(__file__).resolve().parents[2]
    assert (root / "research_training" / "segmentation_metrics.py").read_text() == (root / "backend" / "app" / "segmentation_metrics.py").read_text()
