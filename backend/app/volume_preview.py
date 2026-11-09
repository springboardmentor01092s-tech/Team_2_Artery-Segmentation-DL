"""Bounded point preview of the saved source-grid vessel mask."""
from threading import BoundedSemaphore

PREVIEW_SLOTS = BoundedSemaphore(1)
MAX_PREVIEW_POINTS = 16_000


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

    mask = np.asarray(image.dataobj).ravel(order='F')
    count = int(np.count_nonzero(mask))
    if not count:
        return {'foreground_voxels': 0, 'points': []}

    # Sample evenly through the occupied voxels without materializing a coordinate
    # array for the entire mask. Preserve the source affine for spatial proportions.
    ranks = np.linspace(0, count - 1, min(count, MAX_PREVIEW_POINTS), dtype=np.int64)
    coords = []
    start = 0
    block_size = 256 * 1024
    for offset in range(0, mask.size, block_size):
        indices = np.flatnonzero(mask[offset:offset + block_size])
        end = start + indices.size
        left, right = ranks.searchsorted([start, end])
        if right > left:
            coords.append(indices[ranks[left:right] - start] + offset)
        start = end

    voxels = np.column_stack(np.unravel_index(np.concatenate(coords), image.shape, order='F'))
    points = nib.affines.apply_affine(image.affine, voxels)
    points -= (points.min(axis=0) + points.max(axis=0)) / 2
    radius = np.linalg.norm(points, axis=1).max()
    if radius > 0:
        points /= radius
    return {'foreground_voxels': count, 'points': points.round(5).tolist()}
