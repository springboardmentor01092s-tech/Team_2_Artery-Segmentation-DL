import nibabel as nib
import numpy as np

from app.volume_preview import mask_preview


def test_preview_preserves_component_identity_and_orders_largest(tmp_path):
    mask = np.zeros((18, 18, 18), dtype=np.uint8)
    mask[2:8, 2:8, 2:8] = 1
    mask[13:15, 13:15, 13:15] = 1
    image = nib.Nifti1Image(mask, np.diag([.7, .8, 1.5, 1]))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'mask.nii.gz'
    nib.save(image, path)

    result = mask_preview(path)

    assert result['foreground_voxels'] == 224
    assert result['component_count'] == 2
    assert [item['foreground_voxels'] for item in result['components']] == [216, 8]
    assert result['largest_component_voxels'] == 216
    assert len(result['points']) == sum(len(item['points']) for item in result['components'])
    assert max(abs(value) for point in result['points'] for value in point) <= 1
