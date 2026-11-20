"""Physical-space exploratory measurements of a saved predicted volume mask."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.ndimage import distance_transform_edt, convolve, map_coordinates, label
from skimage.morphology import skeletonize

METHOD = 'lee-skeleton-local-bilateral-sections-v5'
REFERENCE_GUARD = 7
REFERENCE_SAMPLES = 4
REFERENCE_MAX_CV = .20
REFERENCE_MAX_SIDE_DIFFERENCE = .25
SECTION_STEPS_MM = (.20, .25, .30)


def cross_section(mask, affine, center, tangent, radius_mm=12, step_mm=.25):
    """Sample a physical plane and retain the lumen component at its centre."""
    tangent = np.asarray(tangent, dtype=float)
    norm = np.linalg.norm(tangent)
    if norm < 1e-8:
        return dict(status='degenerate_tangent')
    tangent /= norm
    seed = np.eye(3)[np.argmin(np.abs(tangent))]
    u = np.cross(tangent, seed)
    u /= np.linalg.norm(u)
    v = np.cross(tangent, u)
    axis = np.arange(-radius_mm, radius_mm+step_mm/2, step_mm)
    a, b = np.meshgrid(axis, axis, indexing='ij')
    world = np.asarray(center) + a[...,None]*u + b[...,None]*v
    voxel = nib.affines.apply_affine(np.linalg.inv(affine), world)
    plane = map_coordinates(mask.astype(np.uint8), voxel.reshape(-1,3).T,
                            order=0, mode='constant', cval=0).reshape(a.shape)>0
    components, _ = label(plane)
    middle = len(axis)//2
    identity = components[middle,middle]
    if not identity:
        return dict(status='centre_outside_lumen')
    lumen = components == identity
    if lumen[0].any() or lumen[-1].any() or lumen[:,0].any() or lumen[:,-1].any():
        return dict(status='truncated_section')
    area = float(lumen.sum()*step_mm**2)
    return dict(status='experimental_section', center_ras_mm=list(center), normal_ras=tangent.tolist(),
        basis_u=u.tolist(),basis_v=v.tolist(),step_mm=step_mm,
        area_mm2=area,equivalent_diameter_mm=float(2*np.sqrt(area/np.pi)),
        diameter_definition='area-equivalent diameter',
        lumen_pixels_ij=np.argwhere(lumen).tolist(),grid_size=len(axis))


def saved_measurement(path):
    """Reuse geometry only when both its source hash and method match."""
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    cache = path.parent / f'geometry-sections-v5-{digest}.json'
    if cache.is_file():
        result = json.loads(cache.read_text())
        if (result.get('mask_sha256') == digest
                and result.get('method') == METHOD):
            return result
    result = measure(path)
    result['mask_sha256'] = digest
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
        json.dump(result, stream, allow_nan=False)
        temporary = stream.name
    os.replace(temporary, cache)
    return result


def measure(path):
    path = Path(path)
    image = nib.load(path)
    mask = np.asarray(image.dataobj) > 0
    component_labels, component_count = label(mask, np.ones((3, 3, 3), dtype=np.uint8))
    component_sizes = sorted(np.bincount(component_labels.ravel())[1:].astype(int).tolist(), reverse=True)
    occupied = np.where(mask)
    if not occupied[0].size:
        return dict(status='abstained', method=METHOD, reasons=['empty_prediction'], component_count=0,
                    component_sizes_voxels=[], paths=[], candidates=[], clinical_validated=False)
    if any(np.take(mask, index, axis=axis).any() for axis in range(3) for index in (0, -1)):
        return dict(status='abstained', method=METHOD, reasons=['prediction_touches_volume_boundary'],
                    component_count=1, component_sizes_voxels=component_sizes,
                    paths=[], candidates=[], clinical_validated=False,
                    measurement_scope='withheld_before_centerline_or_stenosis_measurement')
    origin = np.array([axis.min() for axis in occupied])
    end = np.array([axis.max()+1 for axis in occupied])
    slices = tuple(slice(int(a), int(b)) for a, b in zip(origin, end))
    cropped = np.pad(mask[slices], 1)
    if cropped.size > 32_000_000:
        raise ValueError('Measurement crop exceeds 32 million voxels')
    spacing = nib.affines.voxel_sizes(image.affine)
    if image.header.get_xyzt_units()[0] != 'mm':
        raise ValueError('Physical measurements require millimetre units')
    axes = image.affine[:3, :3] / spacing
    if not np.allclose(axes.T @ axes, np.eye(3), atol=1e-4):
        raise ValueError('Sheared source geometry requires orthogonal resampling')
    distance = distance_transform_edt(cropped, sampling=spacing)
    skeleton = skeletonize(cropped, method='lee') > 0
    degree = convolve(skeleton.astype(np.uint8), np.ones((3,3,3), np.uint8), mode='constant') - skeleton
    coordinates = np.argwhere(skeleton)
    nodes = {tuple(p) for p in coordinates}
    offsets = [tuple(value-1 for value in p) for p in np.ndindex(3,3,3) if p != (1,1,1)]
    def neighbors(point):
        return sorted(tuple(point[i]+offset[i] for i in range(3)) for offset in offsets
                      if tuple(point[i]+offset[i] for i in range(3)) in nodes)
    visited = set()
    paths = []
    starts = sorted(p for p in nodes if degree[p] != 2) + sorted(nodes)
    for start in starts:
        for neighbor in neighbors(start):
            edge = frozenset((start, neighbor))
            if edge in visited:
                continue
            chain = [start, neighbor]
            visited.add(edge)
            while degree[chain[-1]] == 2:
                options = [p for p in neighbors(chain[-1]) if p != chain[-2]]
                if not options or frozenset((chain[-1], options[0])) in visited:
                    break
                visited.add(frozenset((chain[-1], options[0])))
                chain.append(options[0])
            if len(chain) < 3:
                continue
            points = np.array(chain)
            world = nib.affines.apply_affine(image.affine, points+origin-1)
            widths = 2*distance[tuple(points.T)]
            component_id = int(component_labels[tuple((points[0]+origin-1).T)])
            paths.append(dict(id=f'P{len(paths)+1}', points_ras_mm=world.tolist(),
                component_id=component_id, mask_width_mm=widths.tolist(),
                length_mm=float(np.linalg.norm(np.diff(world,axis=0),axis=1).sum())))
    cropped_affine = image.affine.copy()
    cropped_affine[:3,3] = nib.affines.apply_affine(image.affine,origin-1)
    candidates = []
    for path_record in paths:
        widths = np.array(path_record['mask_width_mm'])
        world = np.asarray(path_record['points_ras_mm'])
        eligible_start = REFERENCE_GUARD + REFERENCE_SAMPLES + 2
        eligible_stop = len(widths) - REFERENCE_GUARD - REFERENCE_SAMPLES - 2
        if eligible_start >= eligible_stop:
            continue
        eligible = range(eligible_start, eligible_stop)
        index = min(eligible, key=lambda sample: widths[sample])
        proximal = list(range(index-REFERENCE_GUARD-REFERENCE_SAMPLES, index-REFERENCE_GUARD))
        distal = list(range(index+REFERENCE_GUARD+1, index+REFERENCE_GUARD+1+REFERENCE_SAMPLES))
        proximal_width = float(np.median(widths[proximal]))
        distal_width = float(np.median(widths[distal]))
        reference_profile = np.asarray([*widths[proximal], *widths[distal]], dtype=float)
        profile_cv = float(np.std(reference_profile) / np.mean(reference_profile))
        side_difference = float(abs(proximal_width-distal_width) / max(proximal_width, distal_width))
        if profile_cv > REFERENCE_MAX_CV or side_difference > REFERENCE_MAX_SIDE_DIFFERENCE:
            continue
        proximal_index = proximal[len(proximal)//2]
        distal_index = distal[len(distal)//2]

        def section(sample, step):
            return cross_section(cropped, cropped_affine, world[sample],
                                 world[sample+2]-world[sample-2], step_mm=step)

        sections = [section(index, .25), section(proximal_index, .25), section(distal_index, .25)]
        if any(value['status'] != 'experimental_section' for value in sections):
            continue
        minimum = sections[0]['equivalent_diameter_mm']
        reference = float(np.mean([sections[1]['equivalent_diameter_mm'],
                                   sections[2]['equivalent_diameter_mm']]))
        if reference <= 0:
            continue
        narrowing = float(max(0, (1-minimum/reference)*100))
        if narrowing < 25:
            continue
        sensitivity = []
        for step in SECTION_STEPS_MM:
            sampled = [section(index, step), section(proximal_index, step), section(distal_index, step)]
            if any(value['status'] != 'experimental_section' for value in sampled):
                continue
            local_reference = float(np.mean([sampled[1]['equivalent_diameter_mm'],
                                             sampled[2]['equivalent_diameter_mm']]))
            sensitivity.append(dict(step_mm=step,
                narrowing_percent=float(max(0, (1-sampled[0]['equivalent_diameter_mm']/local_reference)*100))))
        if len(sensitivity) != len(SECTION_STEPS_MM):
            continue
        sensitivity_range = [min(value['narrowing_percent'] for value in sensitivity),
                             max(value['narrowing_percent'] for value in sensitivity)]
        bands = ((25, 50, 'mild'), (50, 70, 'moderate'), (70, float('inf'), 'severe'))
        grade = next((name for lower, upper, name in bands
                      if sensitivity_range[0] >= lower and sensitivity_range[1] < upper), None)
        uncertainty_status = 'quantified_step_size_sensitivity'
        abstention_reasons = [] if grade else ['sensitivity_crosses_severity_boundary']
        candidates.append(dict(id=f'C{len(candidates)+1}', path_id=path_record['id'],
            component_id=path_record['component_id'],
            location_ras_mm=path_record['points_ras_mm'][index], minimum_diameter_mm=minimum,
            reference_diameter_mm=reference, narrowing_percent=narrowing, severity=grade,
            minimum_area_mm2=sections[0]['area_mm2'],
            reference_area_mm2=float(np.mean([sections[1]['area_mm2'], sections[2]['area_mm2']])),
            area_narrowing_percent=max(0,(1-sections[0]['area_mm2']/
                np.mean([sections[1]['area_mm2'], sections[2]['area_mm2']]))*100),
            cross_sections=sections, protocol_id='CCTA_GEOMETRY_RESEARCH_V1',
            reference_indices=dict(proximal=proximal, distal=distal),
            reference_profile_cv=profile_cv, reference_side_difference=side_difference,
            reference_status='experimental_local_bilateral_same_path_selection',
            sensitivity=dict(method='section_grid_step_perturbation', values=sensitivity,
                             narrowing_range_percent=sensitivity_range),
            uncertainty_status=uncertainty_status, abstention_reasons=abstention_reasons))
    return dict(status='experimental_mask_geometry', method=METHOD,
        mask_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        paths=paths, candidates=candidates, unit='mm', clinical_validated=False,
        component_count=int(component_count), component_sizes_voxels=component_sizes,
        quality_warnings=(['disconnected_prediction_component_local_measurement'] if component_count > 1 else []),
        measurement_scope='component_local_experimental_mask_geometry',
        limitations=([f'The predicted mask has {component_count} disconnected components; paths and references are restricted to their own component.'] if component_count > 1 else []) + [
                    'Path profiles use EDT widths. Candidate diameters use area-equivalent perpendicular sections.',
                    'Local references use stable proximal and distal same-path windows separated from the minimum.',
                    'Reference side disagreement or variation above policy limits withholds the candidate.',
                    'Severity is withheld when section-grid sensitivity crosses an experimental 25/50/70 percent boundary.'])
