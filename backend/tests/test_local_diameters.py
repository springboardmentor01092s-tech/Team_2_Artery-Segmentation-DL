import numpy as np
from app.local_diameters import METHOD_ID, candidate_diameters


def fixture(contrast=1):
    mask=np.zeros((80,120),bool);mask[28:52,4:116]=True;mask[28:34,45:76]=False;mask[46:52,45:76]=False
    image=.2+contrast*.7*mask
    return dict(mask=mask,image=image,path_xy=[[x,39.5] for x in range(10,110)],
        candidate_xyxy=[48,30,72,50],run_id='synthetic',candidate_id='fixture',
        association_verified=True,overlap_known=False)


def test_local_known_widths_and_reference():
    result=candidate_diameters(**fixture())
    assert result['algorithm'] == METHOD_ID
    assert result['method_source']=='Centerline distance-transform widths with nearby-reference comparison'
    assert result['status']=='experimental_measurement'
    assert abs(result['minimum_diameter']-12)<1
    assert abs(result['reference_diameter']-24)<1
    assert abs(result['narrowing_percent']-50)<3
    assert result['category'] is None


def test_low_contrast_overlap_and_association_abstain():
    assert candidate_diameters(**fixture(.1))['reasons']==['low_local_boundary_contrast']
    assert candidate_diameters(**{**fixture(),'overlap_known':True})['status']=='abstained'
    assert candidate_diameters(**{**fixture(),'association_verified':False})['status']=='abstained'
    assert candidate_diameters(**{**fixture(),'branch_points':[(60,39)]})['reasons']==['branch_ambiguity_in_candidate_region']
