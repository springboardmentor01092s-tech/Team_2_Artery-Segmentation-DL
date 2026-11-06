from io import BytesIO
import json
from types import SimpleNamespace
import numpy as np
from PIL import Image
from app.saved_width_profiles import attach_saved_width_profiles


def fixture():
    mask = np.zeros((20, 30), dtype=np.uint8)
    mask[8:12, 4:26] = 255
    stream = BytesIO(); Image.fromarray(mask).save(stream, format='PNG')
    vessel = dict(centerline_paths=[dict(path_id='P1', path_type='centerline',
        coordinates_xy=[[x, 9] for x in range(5, 25)])], branch_points=[])
    geometry = dict(padding_left_top_xy=[0, 0], content_size_xy=[30, 20],
        source_pixels_per_content_pixel_xy=[1, 1], source_roi_origin_xy=[0, 0])
    image = SimpleNamespace(width=30, height=20, source_sha256='source', processed_sha256='prepared',
        preprocessing_config_json=json.dumps(dict(resize_geometry=geometry)))
    return stream.getvalue(), vessel, image


def test_saved_mask_profiles_are_bound_to_event_and_digests_without_mutating_input():
    mask, vessel, image = fixture()
    before = json.dumps(vessel)
    result = attach_saved_width_profiles(vessel=vessel, mask_bytes=mask, image=image, event_id='new-run')
    assert json.dumps(vessel) == before
    bundle = result['width_profiles']
    assert bundle['analysis_run_id'] == 'new-run'
    assert bundle['source_image_sha256'] == 'source'
    assert bundle['prepared_image_sha256'] == 'prepared'
    assert len(bundle['mask_sha256']) == 64
    assert bundle['profiles'][0]['samples'][5]['width'] == 4
    assert bundle['profiles'][0]['lumen_diameter_validated'] is False
    assert 'clinical_narrowing_percent' not in bundle


def test_missing_and_invalid_mask_preserve_unavailable_status():
    mask, vessel, image = fixture()
    result = attach_saved_width_profiles(vessel=vessel, mask_bytes=None, image=image, event_id='run')
    assert result['width_profiles']['status'] == 'unavailable'
    result = attach_saved_width_profiles(vessel=vessel, mask_bytes=b'invalid', image=image, event_id='run')
    assert result['width_profiles']['status'] == 'unavailable'
    assert result['width_profiles']['profiles'] == []
