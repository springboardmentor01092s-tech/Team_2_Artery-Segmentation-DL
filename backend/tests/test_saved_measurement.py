import numpy as np
from app.saved_measurement import measure_candidate


def test_unique_vessel_measurement_and_sensitivity():
    mask=np.zeros((80,120),bool);mask[28:52,4:116]=True
    mask[28:34,45:76]=False;mask[46:52,45:76]=False
    candidate={'candidate_id':'synthetic-C1','bbox_source_xyxy':[48,25,72,55]}
    result=measure_candidate(mask,.2+.7*mask,candidate,'synthetic-run')
    assert result['status']=='experimental_measurement',result
    assert abs(result['narrowing_percent']-50)<3
    assert result['association']['status']=='unique_geometric_path'
    assert len(result['sensitivity']['variants'])==2
    assert result['severity']['category'] is None
    informed=measure_candidate(mask,.2+.7*mask,candidate,'synthetic-run',authorization=dict(
        protocol_id='COROVISION_CADRADS_INFORMED_XCA',protocol_version='1.0.0',
        status='researcher_authorized',authorized_by='synthetic-test',authorized_at='2026-11-11'))
    assert informed['severity']['protocol_id']=='COROVISION_CADRADS_INFORMED_XCA'
    assert informed['severity']['category'] is None
    assert 'crosses' in informed['severity']['reason']


def test_ambiguous_and_missing_source_mapping():
    mask=np.zeros((80,120),bool);mask[20:30,4:116]=True;mask[45:55,4:116]=True
    result=measure_candidate(mask,.2+.7*mask,{'candidate_id':'C','bbox_source_xyxy':[40,10,80,60]},'r')
    assert result['status']=='abstained'
    assert measure_candidate(mask,.2+.7*mask,{'candidate_id':'C'},'r')['reasons']==['original_coordinate_mapping_unreliable']


def test_truncated_candidate_reference_on_narrow_plateau_abstains():
    mask=np.zeros((80,120),bool);mask[28:52,4:116]=True
    mask[28:34,35:86]=False;mask[46:52,35:86]=False
    result=measure_candidate(mask,.2+.7*mask,{'candidate_id':'partial','bbox_source_xyxy':[50,25,70,55]},'r')
    assert result['status']=='abstained'
    assert result['narrowing_percent'] is None
    assert 'reference_suitability_unconfirmed_equal_widths' in result['reasons']
