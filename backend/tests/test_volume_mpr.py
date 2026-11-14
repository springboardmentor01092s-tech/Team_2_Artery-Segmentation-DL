import nibabel as nib
import numpy as np
import pytest
from PIL import Image
from io import BytesIO

from app.volume_mpr import render_mpr


def test_mpr_window_overlay_and_axis_geometry(tmp_path):
    values = np.arange(8*10*12, dtype=np.int16).reshape(8, 10, 12)-300
    mask = np.zeros_like(values, dtype=np.uint8)
    mask[2:6, 3:7, 4:8] = 1
    affine = np.diag([.7, .9, 1.4, 1])
    source = nib.Nifti1Image(values, affine); source.header.set_xyzt_units('mm')
    label = nib.Nifti1Image(mask, affine); label.header.set_xyzt_units('mm')
    source_path, mask_path = tmp_path/'source.nii.gz', tmp_path/'mask.nii.gz'
    nib.save(source, source_path); nib.save(label, mask_path)
    payload = render_mpr(source_path, mask_path, axis=2, index=5, window=800, level=100, opacity=.5)
    image = np.asarray(Image.open(BytesIO(payload)))
    assert image.shape == (10, 8, 3)
    assert np.any(image[..., 1] != image[..., 0])


def test_mpr_rejects_invalid_controls_and_geometry(tmp_path):
    source = nib.Nifti1Image(np.zeros((4, 4, 4)), np.eye(4))
    mask = nib.Nifti1Image(np.zeros((5, 4, 4), dtype=np.uint8), np.eye(4))
    a, b = tmp_path/'a.nii.gz', tmp_path/'b.nii.gz'
    nib.save(source, a); nib.save(mask, b)
    with pytest.raises(ValueError, match='geometry'):
        render_mpr(a, b, axis=2, index=0, window=1, level=0, opacity=.5)
    nib.save(nib.Nifti1Image(np.zeros((4, 4, 4), dtype=np.uint8), np.eye(4)), b)
    with pytest.raises(ValueError, match='outside'):
        render_mpr(a, b, axis=2, index=9, window=1, level=0, opacity=.5)
    with pytest.raises(ValueError, match='Opacity|opacity'):
        render_mpr(a, b, axis=2, index=1, window=1, level=0, opacity=2)
