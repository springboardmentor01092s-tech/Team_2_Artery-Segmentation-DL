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
    cache = path.parent / f'geometry-sections-v2-{digest}.json'
    if cache.is_file():
        result = json.loads(cache.read_text())
        if result.get('mask_sha256') == digest:
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
    occupied = np.where(mask)
    if not occupied[0].size:
        return dict(status='empty_mask', paths=[], candidates=[])
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
            paths.append(dict(id=f'P{len(paths)+1}', points_ras_mm=world.tolist(),
                mask_width_mm=widths.tolist(), length_mm=float(np.linalg.norm(np.diff(world,axis=0),axis=1).sum())))
    cropped_affine = image.affine.copy()
    cropped_affine[:3,3] = nib.affines.apply_affine(image.affine,origin-1)
    candidates = []
    for path_record in paths:
        widths = np.array(path_record['mask_width_mm'])
        if len(widths) < 11:
            continue
        interior = widths[3:-3]
        index = int(np.argmin(interior))+3
        reference = float(np.percentile(interior, 75))
        minimum = float(widths[index])
        world = np.asarray(path_record['points_ras_mm'])
        reference_index = int(np.argmin(np.abs(interior-reference)))+3
        sections = []
        for sample in [index, reference_index]:
            sections.append(cross_section(cropped,cropped_affine,world[sample],world[sample+2]-world[sample-2]))
        if any(section['status'] != 'experimental_section' for section in sections):
            continue
        minimum, reference = [section['equivalent_diameter_mm'] for section in sections]
        if reference <= 0 or index == reference_index:
            continue
        narrowing = float(max(0, (1-minimum/reference)*100))
        if narrowing < 25:
            continue
        grade = 'mild' if narrowing < 50 else 'moderate' if narrowing < 70 else 'severe'
        candidates.append(dict(id=f'C{len(candidates)+1}', path_id=path_record['id'],
            location_ras_mm=path_record['points_ras_mm'][index], minimum_diameter_mm=minimum,
            reference_diameter_mm=reference, narrowing_percent=narrowing, severity=grade,
            minimum_area_mm2=sections[0]['area_mm2'],reference_area_mm2=sections[1]['area_mm2'],
            area_narrowing_percent=max(0,(1-sections[0]['area_mm2']/sections[1]['area_mm2'])*100),
            cross_sections=sections, protocol_id='CCTA_GEOMETRY_RESEARCH_V1',
            uncertainty_status='not_quantified', reference_status='experimental_path_percentile_selection'))
    return dict(status='experimental_mask_geometry', method='lee-skeleton-perpendicular-sections-v2',
        mask_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        paths=paths, candidates=candidates, unit='mm', clinical_validated=False,
        limitations=['Path profiles use EDT widths. Candidate diameters use area-equivalent perpendicular sections.',
                    'Coarse segmentation, tapering, branch junctions and mask errors affect candidate selection.',
                    'Reference is the path interior 75th percentile. Grades use experimental 25/50/70 percent rules.'])
