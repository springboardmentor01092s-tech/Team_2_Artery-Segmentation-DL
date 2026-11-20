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


def test_disconnected_prediction_is_measured_within_each_component(tmp_path):
    mask = np.zeros((31, 31, 31), dtype=np.uint8)
    mask[6:10, 6:10, 5:25] = 1
    mask[20:24, 20:24, 5:25] = 1
    image = nib.Nifti1Image(mask, np.diag([.6, .8, 1.2, 1]))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'disconnected.nii.gz'
    nib.save(image, path)
    result = measure(path)
    assert result['status'] == 'experimental_mask_geometry'
    assert result['component_count'] == 2
    assert result['quality_warnings'] == ['disconnected_prediction_component_local_measurement']
    assert result['measurement_scope'] == 'component_local_experimental_mask_geometry'
    assert isinstance(result['paths'], list)
    assert all(path['component_id'] in {1, 2} for path in result['paths'])
    assert all(candidate['component_id'] in {1, 2} for candidate in result['candidates'])


def test_boundary_clipped_prediction_abstains_before_measurement(tmp_path):
    mask = np.zeros((15, 15, 15), dtype=np.uint8)
    mask[0:4, 5:9, 2:13] = 1
    image = nib.Nifti1Image(mask, np.eye(4))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'clipped.nii.gz'
    nib.save(image, path)
    assert measure(path)['reasons'] == ['prediction_touches_volume_boundary']


def test_local_bilateral_reference_and_step_sensitivity(tmp_path):
    grid = np.indices((65, 65, 65))
    radius = np.full(65, 6.0)
    radius[29:36] = 3.0
    mask = (((grid[0]-32)**2 + (grid[1]-32)**2) <= radius[grid[2]]**2) & (grid[2] >= 5) & (grid[2] < 60)
    image = nib.Nifti1Image(mask.astype(np.uint8), np.diag([.5, .5, .8, 1]))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'local-reference.nii.gz'
    nib.save(image, path)
    result = measure(path)
    candidate, = result['candidates']
    assert candidate['reference_status'] == 'experimental_local_bilateral_same_path_selection'
    assert set(candidate['reference_indices']) == {'proximal', 'distal'}
    assert candidate['uncertainty_status'] == 'quantified_step_size_sensitivity'
    assert len(candidate['sensitivity']['values']) == 3
    assert candidate['severity'] in {'mild', 'moderate', 'severe', None}


def test_taper_disagreement_does_not_create_candidate(tmp_path):
    grid = np.indices((65, 65, 65))
    radius = 7.0 - 3.5 * grid[2] / 64
    mask = (((grid[0]-32)**2 + (grid[1]-32)**2) <= radius**2) & (grid[2] >= 5) & (grid[2] < 60)
    image = nib.Nifti1Image(mask.astype(np.uint8), np.diag([.5, .5, .8, 1]))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'taper.nii.gz'
    nib.save(image, path)
    assert measure(path)['candidates'] == []


def test_short_path_without_reference_window_is_retained_without_crashing(tmp_path):
    mask = np.zeros((35, 35, 35), dtype=np.uint8)
    mask[15:20, 15:20, 4:31] = 1
    image = nib.Nifti1Image(mask, np.eye(4))
    image.header.set_xyzt_units('mm')
    path = tmp_path / 'short-reference-window.nii.gz'
    nib.save(image, path)
    result = measure(path)
    assert result['status'] == 'experimental_mask_geometry'
    assert result['paths']
    assert result['candidates'] == []
