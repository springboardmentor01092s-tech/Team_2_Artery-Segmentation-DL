import pytest
from app.candidate_path_association import associate_candidate_paths


def run(paths, **kwargs):
    return associate_candidate_paths(candidate=dict(candidate_id='C1', analysis_run_id='R1',
        source_image_id='I1', coordinate_frame='source_image_xy', bbox_source_xyxy=[0, 0, 10, 10]),
        paths=paths, analysis_run_id='R1', minimum_fraction=.5, minimum_points=2,
        ambiguity_margin=.05, **kwargs)


def path(identity, points, run_id='R1'):
    return dict(path_id=identity, points=points, source_image_id='I1', analysis_run_id=run_id, coordinate_frame='source_image_xy')


def test_source_edge_contract_and_evidence_preserved():
    result=run([path('P1', [[0,0],[5,5],[10,5]])])
    assert result['selected_path_id']=='P1'
    assert result['evidence'][0]['inside_point_indices']==[0,1]
    assert result['anatomical_artery_identity'] is None
    assert result['clinical_validation'] is False


def test_tied_paths_abstain_instead_of_arbitrary_identity():
    result=run([path('P2',[[1,1],[2,2]]),path('P1',[[3,3],[4,4]])])
    assert result['status']=='ambiguous_requires_review'
    assert result['selected_path_id'] is None


def test_absent_or_insufficient_spatial_evidence_abstains():
    assert run([])['status']=='unassociated'
    assert run([path('P1',[[1,1],[20,20],[21,21]])])['selected_path_id'] is None


def test_cross_run_and_duplicate_path_identity_blocked():
    with pytest.raises(ValueError, match='mismatch'):
        run([path('P1',[[1,1]],run_id='OLD')])
    with pytest.raises(ValueError, match='Unique'):
        run([path('P1',[[1,1]]),path('P1',[[2,2]])])


def test_same_run_different_source_image_is_rejected():
    other = path('P1', [[1,1],[2,2]])
    other['source_image_id'] = 'I2'
    with pytest.raises(ValueError, match='source image identity mismatch'):
        run([other])


def test_missing_source_image_identity_is_rejected():
    other = path('P1', [[1,1],[2,2]])
    del other['source_image_id']
    with pytest.raises(ValueError, match='source image identity mismatch'):
        run([other])


def test_output_preserves_source_identity():
    result = run([path('P1', [[1,1],[2,2]])])
    assert result['source_image_id'] == 'I1'
    assert result['schema_version'].endswith('.v2')
