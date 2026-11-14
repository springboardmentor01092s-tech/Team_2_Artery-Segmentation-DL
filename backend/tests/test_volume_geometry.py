import numpy as np
import pytest

from app.volume_geometry import analyze_volume_mask


def line():
    mask = np.zeros((9, 9, 9), dtype=bool)
    mask[4, 4, 2:7] = True
    return mask


def test_known_line_uses_array_axes_spacing_and_world_translation():
    affine = np.diag([.5, .7, 2., 1.])
    affine[:3, 3] = [10, 20, 30]
    result = analyze_volume_mask(line(), affine, spatial_unit="mm")
    assert result["centerline_length"] == pytest.approx(8.)
    assert result["mask_volume"] == pytest.approx(3.5)
    assert result["endpoint_count"] == 2
    assert result["grouped_branch_points"] == 0
    assert result["minimum_mask_width"] == pytest.approx(1.)
    np.testing.assert_allclose(result["centerline_coordinates_xyz"][0], [12, 22.8, 34])
    assert result["severity_category"] is None and result["narrowing_percent"] is None


def test_rotation_and_reflection_preserve_lengths_and_volume():
    affine = np.array([[0, -.7, 0, 2], [.5, 0, 0, 3], [0, 0, -2, 4], [0, 0, 0, 1]])
    result = analyze_volume_mask(line(), affine, spatial_unit="mm")
    assert result["centerline_length"] == pytest.approx(8.)
    assert result["mask_volume"] == pytest.approx(3.5)


def test_grid_only_results_are_not_given_physical_units():
    result = analyze_volume_mask(line())
    assert result["length_unit"] == "voxel"
    assert result["centerline_length"] == pytest.approx(4.)


def test_empty_mask_keeps_unknown_width_and_no_healthy_claim():
    result = analyze_volume_mask(np.zeros((9, 9, 9), dtype=bool))
    assert result["minimum_mask_width"] is None
    assert result["centerline_coordinates_xyz"] == []
    assert "empty_prediction_not_evidence_of_healthy_case" in result["quality_flags"]


def test_disconnected_lines_are_not_joined():
    mask = line()
    mask[1, 1, 2:7] = True
    result = analyze_volume_mask(mask)
    assert result["connected_components"] == 2
    assert result["endpoint_count"] == 4
    assert result["centerline_length"] == pytest.approx(8.)
    assert result["component_sizes_voxels"] == [5, 5]
    assert result["largest_component_fraction"] == pytest.approx(.5)
    assert result["isolated_fragment_voxels"] == 5
    assert result["measurement_eligibility"] == "abstained"
    assert result["abstention_reasons"] == ["disconnected_prediction"]
    assert result["reference_centerline_coverage"] is None


def test_exported_graph_edges_reconstruct_world_length_without_duplicates():
    affine = np.diag([.5, .7, 2., 1.])
    result = analyze_volume_mask(line(), affine, spatial_unit="mm")
    points = np.asarray(result["centerline_coordinates_xyz"])
    edges = result["centerline_edges"]
    assert len(edges) == 4
    assert all(a < b for a, b in edges)
    assert len({tuple(edge) for edge in edges}) == len(edges)
    assert sum(np.linalg.norm(points[b] - points[a]) for a, b in edges) == pytest.approx(result["centerline_length"])


def test_exported_graph_does_not_bridge_disconnected_structures():
    mask = line(); mask[1, 1, 2:7] = True
    result = analyze_volume_mask(mask)
    points = result["centerline_indices_ijk"]
    assert len(result["centerline_edges"]) == 8
    assert all(points[a][0] == points[b][0] for a, b in result["centerline_edges"])
    assert analyze_volume_mask(np.zeros((3, 3, 3), dtype=bool))["centerline_edges"] == []


@pytest.mark.parametrize("mask", [np.ones((2, 2)), np.full((3, 3, 3), 2),
                                  np.full((3, 3, 3), np.nan)])
def test_invalid_masks_are_rejected(mask):
    with pytest.raises(ValueError):
        analyze_volume_mask(mask)


def test_shear_unverified_units_and_memory_overflow_are_rejected():
    affine = np.eye(4)
    affine[0, 1] = .1
    with pytest.raises(ValueError, match="sheared"):
        analyze_volume_mask(line(), affine, spatial_unit="mm")
    with pytest.raises(ValueError, match="units"):
        analyze_volume_mask(line(), np.eye(4))
    with pytest.raises(ValueError, match="max_voxels"):
        analyze_volume_mask(line(), max_voxels=10)
