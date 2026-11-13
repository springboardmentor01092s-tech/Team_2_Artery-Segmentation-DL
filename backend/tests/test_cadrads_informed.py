import pytest
from app.narrowing import experimental_research_grade

ID='COROVISION_CADRADS_INFORMED_XCA'
AUTH=dict(protocol_id=ID,protocol_version='1.0.0',status='researcher_authorized',
    authorized_by='synthetic-test-owner',authorized_at='2026-11-11T00:00:00Z')

@pytest.mark.parametrize('value,expected',[(0,'No measured narrowing'),(.001,'Minimal'),
    (24.999,'Minimal'),(25,'Mild'),(49.999,'Mild'),(50,'Moderate'),(69.999,'Moderate'),
    (70,'Severe'),(90,'Severe'),(99.999,'Severe')])
def test_continuous_unrounded_bands(value,expected):
    r=experimental_research_grade(value,authorization=AUTH,uncertainty_percentage_points=0)
    assert r['category']==expected and r['protocol_id']==ID
    assert r['clinical_validated'] is False

@pytest.mark.parametrize('value,uncertainty',[(0,.1),(.01,.02),(24.99,.02),(49.99,.02),(69.99,.02),(99.99,.02)])
def test_uncertain_boundary_withholds(value,uncertainty):
    assert experimental_research_grade(value,authorization=AUTH,uncertainty_percentage_points=uncertainty)['category'] is None

def test_authorization_and_occlusion():
    assert experimental_research_grade(100,authorization=AUTH)['status']=='possible_occlusion_requires_assessment'
    assert experimental_research_grade(62,authorization=None,protocol_id=ID,uncertainty_percentage_points=1)['category'] is None
    assert experimental_research_grade(62,authorization=AUTH,uncertainty_percentage_points=1)['category']=='Moderate'
    assert experimental_research_grade(62,authorization={**AUTH,'protocol_version':'2'},uncertainty_percentage_points=1)['category'] is None
