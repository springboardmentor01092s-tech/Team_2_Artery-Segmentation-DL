"""Ordered source-coordinate 2D mask-width profiles; no clinical measurements.

This adapter is inactive unless explicitly called with a mask, saved paths and
the exact resize geometry. It does not perform inference or select thresholds.
"""
import hashlib
import json
import math


def source_width_profiles(mask, paths, *, resize_geometry, source_size_xy,
                          analysis_run_id, mask_sha256, branch_points_xy=(),
                          branch_review_radius=3.):
    import numpy as np
    from scipy.ndimage import distance_transform_edt
    binary = np.asarray(mask)
    if binary.ndim != 2 or not np.isin(binary, [0, 1]).all():
        raise ValueError('Binary 2D mask required')
    binary = binary.astype(bool)
    if not analysis_run_id or len(mask_sha256) != 64 or any(c not in '0123456789abcdef' for c in mask_sha256):
        raise ValueError('Saved run and SHA256 mask artifact identity required')
    try:
        left, top = resize_geometry['padding_left_top_xy']
        cw, ch = resize_geometry['content_size_xy']
        sx, sy = resize_geometry['source_pixels_per_content_pixel_xy']
        ox, oy = resize_geometry['source_roi_origin_xy']
        width, height = source_size_xy
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('Complete resize/source geometry required') from error
    numbers = [left, top, cw, ch, sx, sy, ox, oy, width, height, branch_review_radius]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in numbers):
        raise ValueError('Finite geometry required')
    if min(cw, ch, sx, sy, width, height) <= 0 or min(left, top, ox, oy, branch_review_radius) < 0:
        raise ValueError('Invalid scale/content/source geometry')
    if left+cw > binary.shape[1] or top+ch > binary.shape[0]:
        raise ValueError('Content lies outside prepared mask')
    if ox+cw*sx > width+1e-6 or oy+ch*sy > height+1e-6:
        raise ValueError('Mapped content exceeds source bounds')
    if binary.all():
        raise ValueError('All-foreground mask has no usable background reference')
    radii = distance_transform_edt(binary, sampling=(sy, sx))
    profiles, rejected = [], []
    seen = set()
    for path in paths:
        identity = path.get('path_id')
        if not identity or identity in seen:
            raise ValueError('Unique path identifiers required')
        seen.add(identity)
        if path.get('path_type') != 'centerline':
            rejected.append(dict(path_id=identity, reason='only_open_ordered_centerline_paths_supported'))
            continue
        points = path.get('coordinates_xy', [])
        samples, reason, previous, arc = [], None, None, 0.
        for point in points:
            if len(point) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) or int(v) != v for v in point):
                reason = 'invalid_prepared_grid_coordinate'
                break
            x, y = map(int, point)
            if not (left <= x < left+cw and top <= y < top+ch and 0 <= y < binary.shape[0] and 0 <= x < binary.shape[1]):
                reason = 'path_intersects_padding_or_outside_content'
                break
            if not binary[y, x]:
                reason = 'path_point_outside_foreground'
                break
            if previous is not None:
                dx, dy = x-previous[0], y-previous[1]
                if max(abs(dx), abs(dy)) != 1:
                    reason = 'path_not_adjacent_or_contains_duplicate_points'
                    break
                arc += math.hypot(dx*sx, dy*sy)
            flags = []
            if any(math.hypot((x-bx)*sx, (y-by)*sy) <= branch_review_radius for bx, by in branch_points_xy):
                flags.append('branch_proximity')
            if min((x-left)*sx, (left+cw-1-x)*sx, (y-top)*sy, (top+ch-1-y)*sy) <= branch_review_radius:
                flags.append('image_border_proximity')
            # Positions are pixel centres; source boxes use pixel edges elsewhere.
            samples.append(dict(x=ox+(x-left+.5)*sx-.5, y=oy+(y-top+.5)*sy-.5,
                arc_length=arc, width=float(2*radii[y, x]), quality_flags=flags))
            previous = (x, y)
        if reason or len(samples) < 2:
            rejected.append(dict(path_id=identity, reason=reason or 'fewer_than_two_points'))
            continue
        profiles.append(dict(profile_id=f'{analysis_run_id}:{identity}:mask-width-v1',
            analysis_run_id=analysis_run_id, vessel_path_id=identity, coordinate_frame='source_image_xy',
            coordinate_convention='pixel_centres_xy', unit='pixels', samples=samples,
            mask_sha256=mask_sha256, method='twice_distance_to_background_pixel_centre_source_metric',
            clinical_validated=False, lumen_diameter_validated=False,
            uncertainty=None, physical_calibration='not_used'))
    binding = json.dumps(dict(resize_geometry=resize_geometry, source_size_xy=source_size_xy,
                             paths=paths), sort_keys=True, allow_nan=False).encode()
    return dict(schema_version='corovision.width_profiles.v1', analysis_run_id=analysis_run_id,
        mask_sha256=mask_sha256, geometry_sha256=hashlib.sha256(binding).hexdigest(),
        profiles=profiles, rejected_paths=rejected, coordinate_frame='source_image_xy',
        source_size_xy=list(source_size_xy), physical_units=False,
        limitation='EDT mask widths are not validated lumen diameters; branches, projection, raster boundaries and segmentation errors affect estimates')
