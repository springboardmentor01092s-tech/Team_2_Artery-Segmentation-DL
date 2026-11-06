"""Attach derived geometry to a new analysis event, never to older results."""
import hashlib
from io import BytesIO
import json


def attach_saved_width_profiles(*, vessel, mask_bytes, image, event_id):
    result = dict(vessel)
    config = json.loads(image.preprocessing_config_json or '{}')
    geometry = config.get('resize_geometry')
    if mask_bytes is None or not geometry:
        result['width_profiles'] = dict(status='unavailable', analysis_run_id=event_id,
            reason='Saved artery mask and complete source resize geometry required', profiles=[])
        return result
    try:
        import numpy as np
        from PIL import Image
        from .width_profiles import source_width_profiles
        with Image.open(BytesIO(mask_bytes)) as opened:
            gray = np.asarray(opened.convert('L'))
        if not np.isin(gray, [0, 255]).all():
            raise ValueError('Saved mask PNG must contain only0/255')
        bundle = source_width_profiles(gray > 0, vessel.get('centerline_paths', []),
            resize_geometry=geometry, source_size_xy=[image.width, image.height],
            analysis_run_id=event_id, mask_sha256=hashlib.sha256(mask_bytes).hexdigest(),
            branch_points_xy=[[point['x'], point['y']] for point in vessel.get('branch_points', [])])
        bundle['status'] = 'research_geometry_requires_review'
        bundle['source_image_sha256'] = image.source_sha256
        bundle['prepared_image_sha256'] = image.processed_sha256
        result['width_profiles'] = bundle
    except (OSError, ValueError, TypeError, KeyError) as error:
        # Profile failure cannot masquerade as valid diameter evidence.
        result['width_profiles'] = dict(status='unavailable', analysis_run_id=event_id,
            reason=str(error), profiles=[])
    return result
