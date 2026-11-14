"""Research geometry of an explicit binary 3D mask; no inference or diagnosis."""
from itertools import product

import numpy as np


def analyze_volume_mask(mask, affine=None, *, spatial_unit=None, max_voxels=128**3):
    """Use array-index (i,j,k) coordinates; affine maps these to world (x,y,z).

    This is not SimpleITK's implicit z,y,x layout. Callers must supply the
    affine for the actual array, including any crop/resampling transform.
    """
    from scipy import ndimage
    from skimage.morphology import skeletonize

    values = np.asarray(mask)
    if values.ndim != 3 or not values.size or values.size > max_voxels:
        raise ValueError("mask must be a nonempty 3D array within max_voxels")
    if not np.isfinite(values).all() or not np.isin(values, (0, 1)).all():
        raise ValueError("explicit binary labels 0/1 required; select the anatomical class first")
    binary = values.astype(bool)
    if affine is None:
        if spatial_unit is not None:
            raise ValueError("physical units require an explicit array-to-world affine")
        transform, unit = np.eye(4), "voxel"
    else:
        transform = np.asarray(affine, dtype=float)
        if (transform.shape != (4, 4) or not np.isfinite(transform).all()
                or not np.allclose(transform[3], [0, 0, 0, 1])):
            raise ValueError("affine must be a finite homogeneous 4x4 matrix")
        if spatial_unit != "mm":
            raise ValueError("physical spacing must have explicitly verified mm units")
        unit = "mm"
    axes = transform[:3, :3]
    spacing = np.linalg.norm(axes, axis=0)
    if np.any(spacing <= 0):
        raise ValueError("affine axes must be nonzero")
    directions = axes / spacing
    if not np.allclose(directions.T @ directions, np.eye(3), atol=1e-6, rtol=0):
        raise ValueError("sheared geometry requires a separately validated resampling protocol")
    skeleton = skeletonize(binary, method="lee")
    points = sorted(map(tuple, np.argwhere(skeleton)))
    if len(points) > 100_000:
        raise ValueError("centerline exceeds bounded graph size; no truncated measurement returned")
    point_set = set(points)
    offsets = [offset for offset in product((-1, 0, 1), repeat=3) if any(offset)]
    neighbors = {}
    for point in points:
        adjacent = []
        for offset in offsets:
            other = tuple(p + d for p, d in zip(point, offset))
            if other not in point_set:
                continue
            # Do not add a diagonal shortcut where a face-adjacent skeleton
            # voxel already provides a two-edge route around the corner.
            if sum(abs(x) for x in offset) > 1:
                # All intermediate corners of the edge's bounding cell are
                # symmetric from either endpoint, including 3-axis diagonals.
                bridges = [tuple(p + d for p, d in zip(point, partial))
                           for partial in product(*[(0, d) if d else (0,) for d in offset])
                           if any(partial) and partial != offset]
                if any(bridge in point_set for bridge in bridges):
                    continue
            adjacent.append(other)
        neighbors[point] = adjacent
    length = sum(float(np.linalg.norm(axes @ (np.array(q) - point)))
                 for point in points for q in neighbors[point] if point < q)
    endpoints = [point for point in points if len(neighbors[point]) == 1]
    junction_mask = np.zeros(binary.shape, dtype=bool)
    for point in points:
        if len(neighbors[point]) >= 3:
            junction_mask[point] = True
    _, branches = ndimage.label(junction_mask, np.ones((3, 3, 3)))
    component_labels, components = ndimage.label(binary, np.ones((3, 3, 3)))
    component_sizes = np.bincount(component_labels.ravel())[1:].astype(int)
    ordered_component_sizes = sorted(component_sizes.tolist(), reverse=True)
    largest_component_voxels = ordered_component_sizes[0] if ordered_component_sizes else 0
    largest_component_fraction = (largest_component_voxels / int(binary.sum())
                                  if binary.any() else None)
    widths = []
    sample_points = points[::max(1, (len(points) + 1499)//1500)]
    if points and (~binary).any():
        distance = ndimage.distance_transform_edt(binary, sampling=spacing)
        widths = [2 * float(distance[point]) for point in sample_points]
    flags = []
    if not binary.any():
        flags.append("empty_prediction_not_evidence_of_healthy_case")
    elif not points:
        flags.append("nonempty_mask_without_centerline_review_required")
    if components > 1:
        flags.append("disconnected_mask_review_required")
    if any(np.take(binary, index, axis=axis).any() for axis in range(3) for index in (0, -1)):
        flags.append("mask_touches_boundary_measurements_may_be_clipped")
    world = [(axes @ np.array(point) + transform[:3, 3]).tolist() for point in points]
    point_index = {point: index for index, point in enumerate(points)}
    edges = [[point_index[point], point_index[other]]
             for point in points for other in neighbors[point] if point < other]
    if not binary.any():
        abstention_status, abstention_reasons = "abstained", ["empty_prediction"]
    elif components > 1:
        abstention_status, abstention_reasons = "abstained", ["disconnected_prediction"]
    elif "mask_touches_boundary_measurements_may_be_clipped" in flags:
        abstention_status, abstention_reasons = "abstained", ["prediction_touches_volume_boundary"]
    else:
        abstention_status, abstention_reasons = "eligible_for_research_geometry_only", []
    return dict(mask_voxels=int(binary.sum()), connected_components=int(components),
                component_sizes_voxels=ordered_component_sizes,
                largest_component_voxels=largest_component_voxels,
                largest_component_fraction=largest_component_fraction,
                isolated_fragment_voxels=int(binary.sum())-largest_component_voxels,
                isolated_fragment_volume=float((int(binary.sum())-largest_component_voxels)
                                               * abs(np.linalg.det(axes))),
                reference_centerline_coverage=None, reference_branch_length_coverage=None,
                reference_coverage_status="unavailable_without_qualified_reference_centerlines",
                centerline_voxels=len(points), centerline_indices_ijk=[list(map(int, p)) for p in points],
                centerline_coordinates_xyz=world, array_axis_convention="ijk_to_world_xyz",
                centerline_edges=edges,
                centerline_edge_convention="undirected_pairs_of_zero_based_centerline_point_indices",
                centerline_length=length, length_unit=unit, endpoint_count=len(endpoints),
                grouped_branch_points=int(branches),
                mask_volume=float(binary.sum()*abs(np.linalg.det(axes))),
                volume_unit="mm3" if unit == "mm" else "voxel3",
                minimum_mask_width=min(widths) if widths else None,
                mean_mask_width=float(np.mean(widths)) if widths else None,
                maximum_mask_width=max(widths) if widths else None,
                width_samples=len(widths), width_unit=unit,
                width_method="twice_sampled_centerline_distance_to_background_voxel_center",
                cross_section_area=None, narrowing_percent=None, severity_category=None,
                measurement_scope="discrete_mask_geometry_not_validated_lumen_or_stenosis_measurement",
                quality_flags=flags, review_required=True,
                measurement_eligibility=abstention_status,
                abstention_reasons=abstention_reasons)
