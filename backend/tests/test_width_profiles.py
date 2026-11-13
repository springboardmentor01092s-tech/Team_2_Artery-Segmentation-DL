"""Known synthetic mask/coordinate fixtures, never patient image evaluation."""
import numpy as np
import pytest
from app.width_profiles import source_width_profiles


def setup():
    mask = np.zeros((20, 30), dtype=np.uint8)
    mask[8:12, 4:26] = 1
    path = dict(path_id='P1', path_type='centerline', coordinates_xy=[[x, 9] for x in range(5, 25)])
    geometry = dict(padding_left_top_xy=[0, 0], content_size_xy=[30, 20],
                    source_pixels_per_content_pixel_xy=[1, 1], source_roi_origin_xy=[0, 0])
    return mask, [path], dict(resize_geometry=geometry, source_size_xy=[30, 20],
        analysis_run_id='synthetic-run', mask_sha256='a'*64)


def test_known_rectangle_width_and_ordered_arclength():
    mask, paths, args = setup()
    result = source_width_profiles(mask, paths, **args)
    profile, = result['profiles']
    assert all(s['width'] == 4 for s in profile['samples'])
    assert profile['samples'][0]['x'] == 5
    assert profile['samples'][-1]['arc_length'] == 19
    assert profile['unit'] == 'pixels' and profile['lumen_diameter_validated'] is False


def test_synthetic_narrowing_has_expected_wide_and_narrow_plateaus():
    mask = np.zeros((80, 120), dtype=np.uint8)
    mask[28:52, 4:116] = 1
    mask[:34, 48:84] = 0
    mask[46:, 48:84] = 0
    path = dict(path_id='P1', path_type='centerline', coordinates_xy=[[x, 39] for x in range(5, 115)])
    geometry = dict(padding_left_top_xy=[0, 0], content_size_xy=[120, 80],
                    source_pixels_per_content_pixel_xy=[1, 1], source_roi_origin_xy=[0, 0])
    profile, = source_width_profiles(mask, [path], resize_geometry=geometry, source_size_xy=[120, 80],
                                     analysis_run_id='synthetic-taper', mask_sha256='b'*64)['profiles']
    by_x = {sample['x']: sample['width'] for sample in profile['samples']}
    assert by_x[25] == 24 and by_x[66] == 12
    assert 100 * (1 - by_x[66] / by_x[25]) == 50
    assert not profile['lumen_diameter_validated']


def test_anisotropic_source_scale_and_roi_origin():
    mask, paths, args = setup()
    args['resize_geometry'].update(source_pixels_per_content_pixel_xy=[2, 3], source_roi_origin_xy=[10, 20])
    args['source_size_xy'] = [70, 80]
    profile, = source_width_profiles(mask, paths, **args)['profiles']
    sample = profile['samples'][5]
    assert sample['width'] == 12
    assert sample['x'] == 30.5 and sample['y'] == 48
    assert profile['samples'][-1]['arc_length'] == 38


def test_branch_warning_and_non_open_path_retained_as_rejection():
    mask, paths, args = setup()
    paths.append(dict(path_id='P2', path_type='cycle', coordinates_xy=[]))
    result = source_width_profiles(mask, paths, branch_points_xy=[[10, 9]], **args)
    assert 'branch_proximity' in result['profiles'][0]['samples'][5]['quality_flags']
    assert result['rejected_paths'][0]['path_id'] == 'P2'


def test_path_discontinuity_is_not_joined():
    mask, paths, args = setup()
    paths[0]['coordinates_xy'] = [[5, 9], [20, 9]]
    result = source_width_profiles(mask, paths, **args)
    assert result['profiles'] == []
    assert result['rejected_paths'][0]['reason'] == 'path_not_adjacent_or_contains_duplicate_points'


def test_missing_or_inconsistent_geometry_fails_closed():
    mask, paths, args = setup()
    args['resize_geometry']['source_pixels_per_content_pixel_xy'] = [2, 2]
    with pytest.raises(ValueError):
        source_width_profiles(mask, paths, **args)
    with pytest.raises(ValueError):
        source_width_profiles(np.ones((20, 30)), paths, **args)


def test_profile_adapter_feeds_separate_generator_without_clinical_claims():
    from app.geometry_candidates import ProfilePolicy, extract_profile_candidates
    mask, paths, args = setup()
    profile, = source_width_profiles(mask, paths, **args)['profiles']
    result = extract_profile_candidates(samples=profile['samples'],
        policy=ProfilePolicy('synthetic-only', .7, 0, 2, 1, 1, 0, .2),
        analysis_run_id=profile['analysis_run_id'], vessel_path_id=profile['vessel_path_id'],
        source_profile_id=profile['profile_id'], coordinate_frame=profile['coordinate_frame'], unit=profile['unit'])
    assert result['candidates'] == [] and result['clinical_validated'] is False
