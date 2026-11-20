"""Measure source-pixel mask widths on deterministic, synthetic vessels."""
import csv
from hashlib import sha256
from statistics import mean
import sys

import numpy as np
from scipy.ndimage import gaussian_filter

from app.width_profiles import source_width_profiles


def measure(kind, local_measurement=False):
    x = np.arange(120)
    center = np.full_like(x, 39)
    width = np.full_like(x, 24)
    if kind == 'curved':
        center += np.round(8 * np.sin(x / 22)).astype(int)
    if kind == 'tapered':
        width -= 2 * (x // 16)
    if kind in {'eccentric', 'two-lesions', 'boundary-perturbation', 'blur-noise', 'low-contrast'}:
        width[45:76] = 12
    if kind == 'eccentric':
        center[45:76] += 3
    if kind == 'two-lesions':
        width[85:106] = 16

    y = np.arange(80)[:, None]
    lower = center - width // 2 + 1
    upper = center + width // 2
    mask = (y >= lower) & (y <= upper)
    mask[:, :4] = mask[:, 116:] = False
    image = .2 + .7 * mask.astype(float)
    branch_points = []
    if kind == 'branch':
        mask[15:40, 53:66] = True
        branch_points.append((59, 39))
    if kind == 'boundary-perturbation':
        mask[lower[::4], x[::4]] = False
    if kind in {'blur-noise', 'low-contrast'}:
        contrast = 0.7 if kind == 'blur-noise' else 0.15
        image = 0.2 + contrast * gaussian_filter(mask.astype(float), sigma=1.4)
        image += np.random.default_rng(42).normal(0, 0.06, mask.shape)
        mask = image >= 0.2 + contrast / 2

    if local_measurement:
        from app.local_diameters import candidate_diameters
        return candidate_diameters(mask, np.clip(image, 0, 1),
            [[int(i), float(center[i])] for i in range(10,110)], [48,0,72,79],
            run_id=f'synthetic-{kind}', candidate_id='declared-synthetic-region',
            association_verified=True, overlap_known=False,
            branch_points=branch_points)

    # Sample predefined cross-sections well inside plateaus where applicable.
    # The supplied path tests the width adapter independently of path extraction.
    sites = (25, 60, 95)
    paths = [
        dict(path_id=f'P{site}', path_type='centerline',
             coordinates_xy=[[i, int(center[i])] for i in range(site - 1, site + 2)])
        for site in sites
    ]
    result = source_width_profiles(
        mask, paths,
        resize_geometry=dict(padding_left_top_xy=[0, 0], content_size_xy=[120, 80],
                             source_pixels_per_content_pixel_xy=[1, 1], source_roi_origin_xy=[0, 0]),
        source_size_xy=[120, 80], analysis_run_id=f'synthetic-{kind}',
        mask_sha256=sha256(mask.tobytes()).hexdigest(), branch_points_xy=branch_points,
    )
    measured = {int(sample['x']): sample for profile in result['profiles']
                for sample in profile['samples'] if sample['x'] in sites}
    eligible = [i for i in sites if i in measured and not measured[i]['quality_flags']]
    errors = [measured[i]['width'] - int(width[i]) for i in eligible]
    lesion_sites = {
        'eccentric': [60], 'two-lesions': [60, 95], 'boundary-perturbation': [60],
        'blur-noise': [60], 'low-contrast': [60],
    }.get(kind, [])
    narrowing_errors = [
        100 * (width[i] / width[25] - measured[i]['width'] / measured[25]['width'])
        for i in lesion_sites if 25 in eligible and i in eligible
    ]
    return dict(phantom=kind, mask_sha256=result['mask_sha256'], planned_sites=len(sites),
                eligible_sites=len(eligible), rejected_paths=len(result['rejected_paths']),
                excluded_sites=len(sites) - len(eligible),
                width_mae_px=mean(map(abs, errors)) if errors else None,
                width_rmse_px=mean(e**2 for e in errors)**.5 if errors else None,
                signed_bias_px=mean(errors) if errors else None, measured_lesions=len(narrowing_errors),
                narrowing_mae_percentage_points=mean(map(abs, narrowing_errors)) if narrowing_errors else None)


if __name__ == '__main__':
    rows = []
    for kind in ('straight', 'curved', 'tapered', 'branch', 'eccentric',
                 'two-lesions', 'boundary-perturbation', 'blur-noise', 'low-contrast'):
        result = measure(kind)
        assert result == measure(kind), f'Non-reproducible output for {kind}'
        rows.append(result)
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
