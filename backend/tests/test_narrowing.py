import pytest
from app.narrowing import diameter_reduction


def inputs():
    return dict(minimum=2., reference=4., unit='mm', measurement_frame='source-calibrated',
                candidate_id='synthetic-candidate', reference_segment_id='synthetic-reference',
                protocol_id='synthetic-test-only', calibration_verified=True,
                reference_selection_reviewed=True)


@pytest.mark.parametrize('minimum,expected', [(0,100), (2,50), (4,0)])
def test_research_arithmetic_without_invented_category(minimum, expected):
    args=inputs();args['minimum']=minimum
    result=diameter_reduction(**args)
    assert result['narrowing_percent']==expected
    assert result['category'] is None and not result['clinical_validated']
    assert result['candidate_id']==args['candidate_id']


@pytest.mark.parametrize('key,value', [('minimum',-1), ('minimum',5), ('reference',0),
    ('minimum',float('nan')), ('reference',float('inf')), ('minimum',True),
    ('unit','pixels'), ('candidate_id',''), ('protocol_id',None),
    ('measurement_frame',''), ('reference_segment_id',''),
    ('calibration_verified',False), ('reference_selection_reviewed',False)])
def test_missing_or_invalid_evidence_fails_closed(key,value):
    args=inputs();args[key]=value
    with pytest.raises(ValueError):diameter_reduction(**args)
