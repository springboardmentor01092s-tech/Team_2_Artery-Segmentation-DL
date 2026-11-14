import nibabel as nib
import numpy as np
from app.volume_measurements import cross_section, measure


def test_physical_cylinder_area_and_reversed_direction():
    grid = np.indices((41,41,41))
    affine = np.diag([.5,.5,1.,1.])
    mask = ((grid[0]-20)*.5)**2 + ((grid[1]-20)*.5)**2 <= 9
    section = cross_section(mask,affine,[10,10,20],[0,0,1],step_mm=.1)
    reverse = cross_section(mask,affine,[10,10,20],[0,0,-1],step_mm=.1)
    assert section['status'] == 'experimental_section'
    assert abs(section['area_mm2']-np.pi*9) < 2
    assert abs(section['area_mm2']-reverse['area_mm2']) < .5


def test_missing_lumen_and_truncation():
    assert cross_section(np.zeros((9,9,9)),np.eye(4),[4,4,4],[0,0,1])['status']=='centre_outside_lumen'
    assert cross_section(np.ones((31,31,31)),np.eye(4),[15,15,15],[0,0,1],radius_mm=2)['status']=='truncated_section'


def test_disconnected_prediction_abstains_before_measurement(tmp_path):
    mask = np.zeros((31, 31, 31), dtype=np.uint8)
    mask[6:10, 6:10, 5:25] = 1
    mask[20:24, 20:24, 5:25] = 1
    image = nib.Nifti1Image(mask, np.diag([.6, .8, 1.2, 1]))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'disconnected.nii.gz'
    nib.save(image, path)
    result = measure(path)
    assert result['status'] == 'abstained'
    assert result['reasons'] == ['disconnected_prediction']
    assert result['component_count'] == 2
    assert result['paths'] == [] and result['candidates'] == []


def test_boundary_clipped_prediction_abstains_before_measurement(tmp_path):
    mask = np.zeros((15, 15, 15), dtype=np.uint8)
    mask[0:4, 5:9, 2:13] = 1
    image = nib.Nifti1Image(mask, np.eye(4))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'clipped.nii.gz'
    nib.save(image, path)
    assert measure(path)['reasons'] == ['prediction_touches_volume_boundary']
