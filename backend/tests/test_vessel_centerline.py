import numpy as np
import pytest
from PIL import Image

from app.analysis_model import analyze_vessel_geometry, centerline_overlay_png


def _y_vessel():
    mask = np.zeros((48, 48), dtype=bool)
    mask[5:24, 22:26] = True
    mask[21:25, 7:25] = True
    mask[21:25, 23:41] = True
    return mask


def test_empty_mask_is_reported_as_reviewable_and_keeps_empty_graph():
    result = analyze_vessel_geometry(np.zeros((40, 40), dtype=bool))

    assert result["mask_pixels"] == 0
    assert result["centerline_paths"] == []
    assert result["quality_status"] == "review_required"
    assert "empty_prediction" in {flag["code"] for flag in result["quality_flags"]}


def test_y_shape_extracts_three_paths_one_grouped_junction_and_three_endpoints():
    result = analyze_vessel_geometry(_y_vessel())

    assert result["branching_points"] == 1
    assert result["endpoints"] == 3
    assert len(result["centerline_paths"]) == 3
    assert all(len(path["coordinates_xy"]) > 1 for path in result["centerline_paths"])
    assert len({point["node_id"] for point in result["branch_points"]}) == 1
    assert len({point["node_id"] for point in result["endpoint_points"]}) == 3


def test_closed_vessel_ring_is_preserved_as_a_cycle():
    mask = np.zeros((48, 48), dtype=bool)
    mask[7:41, 7:41] = True
    mask[14:34, 14:34] = False

    result = analyze_vessel_geometry(mask)

    assert any(path["path_type"] == "cycle" for path in result["centerline_paths"])


def test_disconnected_regions_and_uncertainty_are_flagged_without_auto_joining():
    mask = np.zeros((48, 48), dtype=bool)
    mask[5:17, 7:12] = True
    mask[30:42, 35:40] = True
    probabilities = np.full((48, 48), 0.48, dtype=np.float32)
    probabilities[mask] = 0.53

    result = analyze_vessel_geometry(mask, probability_map=probabilities, threshold=0.5)

    codes = {flag["code"] for flag in result["quality_flags"]}
    assert result["connected_components"] == 2
    assert "disconnected_regions" in codes
    assert "uncertain_pixels" in codes
    assert result["uncertain_pixel_fraction"] > 0
    assert result["mean_foreground_probability"] == pytest.approx(0.53)


def test_centerline_map_contains_mask_paths_and_graph_nodes(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (256, 256), "black").save(source)
    result = analyze_vessel_geometry(_y_vessel())

    rendered = centerline_overlay_png(source, result["centerline_paths"],
                                      result["branch_points"], result["endpoint_points"], _y_vessel())

    with Image.open(__import__("io").BytesIO(rendered)) as image:
        assert image.size == (256, 256)
        assert np.count_nonzero(np.asarray(image)) > 100
