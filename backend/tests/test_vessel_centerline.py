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


@pytest.mark.parametrize("spacing", [(0.4, 0.7), None])
def test_diameter_extrema_and_percentiles_match_independent_distance_reference(spacing):
    from app.analysis_model import _skeletonize, postprocess_mask

    mask = np.zeros((48, 48), dtype=bool)
    mask[5:40, 20:27] = True
    mask[18:30, 15:32] = True
    binary = postprocess_mask(mask)
    skeleton = sorted(map(tuple, np.argwhere(_skeletonize(binary))))
    points = skeleton[::max(1, len(skeleton) // 1500)]
    background = np.argwhere(~binary)
    sy, sx = spacing or (1.0, 1.0)
    widths = [2 * np.hypot((background[:, 0] - y) * sy,
                          (background[:, 1] - x) * sx).min() for y, x in points]
    result = analyze_vessel_geometry(mask, spacing)
    assert result["minimum_diameter"] == round(float(np.min(widths)), 2)
    assert result["maximum_diameter"] == round(float(np.max(widths)), 2)
    assert result["mean_diameter"] == round(float(np.mean(widths)), 2)
    assert result["diameter_p10"] == round(float(np.percentile(widths, 10)), 2)
    assert result["diameter_p90"] == round(float(np.percentile(widths, 90)), 2)
    assert result["diameter_unit"] == ("mm" if spacing else "px")


@pytest.mark.parametrize("spacing", [(float("inf"), 1), (float("nan"), 1),
                                     (0, 1), (-1, 1), (1,), (1, 2, 3)])
def test_invalid_spacing_cannot_produce_calibrated_measurements(spacing):
    with pytest.raises(ValueError, match="spacing_mm"):
        analyze_vessel_geometry(_y_vessel(), spacing)


@pytest.mark.parametrize("mask", [np.zeros((2, 2, 2)), np.zeros((0, 2)),
                                  np.array([[float("nan")]])])
def test_invalid_mask_cannot_produce_measurements(mask):
    with pytest.raises(ValueError, match="mask"):
        analyze_vessel_geometry(mask)


@pytest.mark.parametrize("spacing", [(float("inf"), 1), (float("nan"), 1),
                                    (0, 1), (-1, 1), (1,), ("invalid", 1)])
def test_invalid_spacing_never_claims_physical_measurements(spacing):
    mask = np.zeros((32, 32), dtype=bool)
    mask[16, 5:26] = True
    with pytest.raises(ValueError):
        analyze_vessel_geometry(mask, spacing_mm=spacing)


def test_straight_centerline_has_known_length_and_anisotropic_axis_scaling():
    mask = np.zeros((40, 40), dtype=bool)
    mask[20, 5:36] = True
    horizontal = analyze_vessel_geometry(mask, spacing_mm=(2, 0.5))
    vertical = analyze_vessel_geometry(mask.T, spacing_mm=(2, 0.5))
    assert horizontal["centerline_length"] == 15
    assert vertical["centerline_length"] == 60
    assert horizontal["tortuosity"] == vertical["tortuosity"] == 1
    assert horizontal["endpoints"] == vertical["endpoints"] == 2
    assert horizontal["projected_mask_area"] == 31
    assert horizontal["cross_section_area"] is None


def test_bent_centerline_uses_path_length_not_endpoint_distance():
    mask = np.zeros((40, 40), dtype=bool)
    mask[10, 5:26] = True
    mask[10:31, 25] = True
    result = analyze_vessel_geometry(mask)
    assert result["centerline_length"] == 40
    assert result["tortuosity"] == pytest.approx(2 ** 0.5, abs=0.001)
    assert result["branching_points"] == 0


def test_width_estimate_scales_with_calibration_without_claiming_exact_diameter():
    mask = np.zeros((64, 64), dtype=bool)
    mask[10:54, 28:36] = True
    pixels = analyze_vessel_geometry(mask)
    physical = analyze_vessel_geometry(mask, spacing_mm=(0.5, 0.5))
    # Nearest-background-pixel distance is a discretized width approximation.
    assert pixels["mean_diameter"] == pytest.approx(8, abs=1)
    assert physical["mean_diameter"] == pytest.approx(pixels["mean_diameter"] / 2, abs=0.01)
    assert physical["centerline_length"] == pytest.approx(pixels["centerline_length"] / 2, abs=0.01)
    assert physical["projected_mask_area"] == pixels["projected_mask_area"] / 4
    assert physical["diameter_summary_semantics"]["minimum_diameter"] == "minimum_sampled_width"
    assert physical["diameter_summary_semantics"]["maximum_diameter"] == "maximum_sampled_width"
    assert physical["diameter_summary_semantics"]["diameter_p10"] == "10th_percentile"
    assert physical["diameter_summary_semantics"]["diameter_p90"] == "90th_percentile"
    assert physical["diameter_method"] == "twice_centerline_distance_to_background_pixel_center"
    assert physical["diameter_uncertainty"] is None
    assert physical["suitable_for_automatic_severity"] is False
