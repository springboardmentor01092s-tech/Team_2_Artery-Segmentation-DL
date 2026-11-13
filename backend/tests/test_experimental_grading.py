import pytest

from app.narrowing import experimental_research_grade


AUTH = {'status':'researcher_authorized', 'authorized_by':'synthetic-test-owner',
        'authorized_at':'2026-11-11T00:00:00Z'}


@pytest.mark.parametrize('percent,category', [(0,'Normal'),(.00001,'Mild'),(49.95,'Mild'),
    (50,'Moderate'),(69.999,'Moderate'),(70,'Severe'),(89.999,'Severe'),(90,'Critical'),(99.999,'Critical')])
def test_full_precision_boundaries(percent, category):
    result = experimental_research_grade(percent, authorization=AUTH, uncertainty_percentage_points=0)
    assert result['category'] == category
    assert result['clinical_validated'] is False


@pytest.mark.parametrize('percent,uncertainty', [(0,.1),(.01,.02),(49.95,.1),(70,.1),(99.9,.2)])
def test_uncertainty_crossing_boundary_abstains(percent, uncertainty):
    assert experimental_research_grade(percent, authorization=AUTH,
        uncertainty_percentage_points=uncertainty)['category'] is None


def test_occlusion_missing_authorization_and_uncertainty():
    assert experimental_research_grade(100, authorization=AUTH)['status'] == 'possible_occlusion_requires_assessment'
    assert experimental_research_grade(50, authorization=None, uncertainty_percentage_points=0)['category'] is None
    assert experimental_research_grade(50, authorization=AUTH)['category'] is None


@pytest.mark.parametrize('value', [-1,101,float('nan'),float('inf'),True,None])
def test_invalid_measurement_abstains(value):
    assert experimental_research_grade(value, authorization=AUTH, uncertainty_percentage_points=0)['category'] is None
