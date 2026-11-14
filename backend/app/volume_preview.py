"""Bounded point preview of the saved source-grid vessel mask."""
from threading import BoundedSemaphore

PREVIEW_SLOTS = BoundedSemaphore(1)
MAX_PREVIEW_POINTS = 16_000
MAX_PREVIEW_FACES = 20_000


def mask_preview(path):
    import nibabel as nib
    import numpy as np

    from .volume_inference import MAX_VOXELS

    image = nib.load(path)
    if (len(image.shape) != 3 or image.get_data_dtype() != np.dtype('uint8')
            or np.prod(image.shape) > MAX_VOXELS or image.dataobj.slope != 1 or image.dataobj.inter != 0):
        raise ValueError('Unsupported saved mask geometry')
    if not np.isfinite(image.affine).all() or image.header.get_xyzt_units()[0] != 'mm':
        raise ValueError('Saved mask has no usable spatial geometry')

    source_mask = np.asarray(image.dataobj) > 0
    count = int(np.count_nonzero(source_mask))
    if not count:
        return {'foreground_voxels': 0, 'component_count': 0, 'component_sizes_voxels': [],
                'largest_component_voxels': 0, 'largest_component_fraction': None,
                'isolated_fragment_voxels': 0, 'isolated_fragment_volume_mm3': 0,
                'voxel_spacing_mm': nib.affines.voxel_sizes(image.affine).round(6).tolist(),
                'quality_status': 'abstained_empty_prediction', 'measurement_eligible': False,
                'mesh': {'vertices': [], 'faces': []}, 'components': [], 'points': []}

    from scipy.ndimage import label
    labels, component_count = label(source_mask, structure=np.ones((3, 3, 3), dtype=np.uint8))
    sizes = np.bincount(labels.ravel())[1:]
    ordered = np.argsort(sizes)[::-1]

    # Use one common physical-space normalization for every component so that
    # filtering in the browser never changes their relative placement.
    occupied = np.argwhere(source_mask)
    occupied_world = nib.affines.apply_affine(image.affine, occupied)
    centre = (occupied_world.min(axis=0) + occupied_world.max(axis=0)) / 2
    radius = np.linalg.norm(occupied_world - centre, axis=1).max()
    radius = float(radius or 1)

    # Extract an actual bounded isosurface from the preserved binary mask. The
    # point sample remains for older clients and as a low-cost fallback.
    mesh = {'vertices': [], 'faces': []}
    if min(source_mask.shape) >= 2:
        from skimage.measure import marching_cubes
        lower = np.maximum(occupied.min(axis=0) - 1, 0)
        upper = np.minimum(occupied.max(axis=0) + 2, source_mask.shape)
        cropped = source_mask[tuple(slice(int(a), int(b)) for a, b in zip(lower, upper))]
        padded = np.pad(cropped.astype(np.uint8), 1)
        vertices, faces, _, _ = marching_cubes(padded, level=.5)
        vertices += lower - 1
        world_vertices = nib.affines.apply_affine(image.affine, vertices)
        normalized = ((world_vertices - centre) / radius).round(5)
        if len(faces) > MAX_PREVIEW_FACES:
            selected_faces = np.linspace(0, len(faces)-1, MAX_PREVIEW_FACES, dtype=np.int64)
            faces = faces[selected_faces]
            used = np.unique(faces)
            remap = np.full(len(vertices), -1, dtype=np.int64)
            remap[used] = np.arange(len(used))
            normalized = normalized[used]
            faces = remap[faces]
        mesh = {'vertices': normalized.tolist(), 'faces': faces.astype(int).tolist()}

    components = []
    remaining = MAX_PREVIEW_POINTS
    remaining_voxels = count
    for rank, component_index in enumerate(ordered, start=1):
        identity = int(component_index + 1)
        voxels = np.argwhere(labels == identity)
        size = int(sizes[component_index])
        # Allocate samples proportionally while guaranteeing representation of
        # each component. Exact voxel counts remain available separately.
        slots = min(size, max(0, round(remaining * size / remaining_voxels)))
        if remaining and not slots:
            slots = 1
        if slots:
            indices = np.linspace(0, size - 1, slots, dtype=np.int64)
            world = nib.affines.apply_affine(image.affine, voxels[indices])
            points = ((world - centre) / radius).round(5).tolist()
        else:
            points = []
        components.append({'id': rank, 'foreground_voxels': size, 'points': points})
        remaining -= slots
        remaining_voxels -= size

    largest = components[0]['foreground_voxels']
    voxel_volume = float(abs(np.linalg.det(image.affine[:3, :3])))
    return {'foreground_voxels': count, 'component_count': int(component_count),
            'component_sizes_voxels': [component['foreground_voxels'] for component in components],
            'largest_component_voxels': largest,
            'largest_component_fraction': largest / count,
            'isolated_fragment_voxels': count - largest,
            'isolated_fragment_volume_mm3': (count - largest) * voxel_volume,
            'voxel_spacing_mm': nib.affines.voxel_sizes(image.affine).round(6).tolist(),
            'quality_status': 'abstained_disconnected_prediction' if component_count > 1
                              else 'research_geometry_only',
            'measurement_eligible': component_count == 1,
            'mesh': mesh,
            'components': components,
            # Preserve the legacy field for older clients.
            'points': [point for component in components for point in component['points']]}
