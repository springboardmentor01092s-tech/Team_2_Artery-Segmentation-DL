import numpy as np
from app.volume_measurements import cross_section


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
