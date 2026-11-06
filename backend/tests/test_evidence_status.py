from app.evidence_status import saved_analysis_metadata, stenosis_mask_status

def test_saved_mask_absence_is_not_a_measured_negative():
    assert stenosis_mask_status({'model_scores': {'pixel_counts_unavailable': True}}) == 'not_saved'
    assert stenosis_mask_status({'structured_result': {'stages': {'stenosis_detection': {'status': 'skipped'}}}}) == 'not_assessed'
    assert stenosis_mask_status({'model_scores': {'pixel_counts_unavailable': False}}) == 'recorded'
    assert stenosis_mask_status(None) == 'unknown'

def test_skipped_stage_takes_precedence_and_malformed_optional_metadata_is_safe():
    assert stenosis_mask_status({'structured_result': {'stages': {'stenosis_detection': {'status': 'skipped'}}}, 'model_scores': {'pixel_counts_unavailable': True}}) == 'not_assessed'
    for value in ([], 'legacy', 1):
        assert stenosis_mask_status({'structured_result': value, 'model_scores': value}) == 'recorded'


def test_non_object_or_invalid_legacy_metadata_remains_unknown():
    for raw in ('[]', 'null', '"legacy"', '42', '{broken'):
        details, vessel = saved_analysis_metadata(raw)
        assert vessel == {}
        assert stenosis_mask_status(details) == 'unknown'


def test_invalid_optional_vessel_object_cannot_break_overview():
    details, vessel = saved_analysis_metadata('{"vessel_analysis": [], "model_scores": {"pixel_counts_unavailable": true}}')
    assert vessel == {}
    assert stenosis_mask_status(details) == 'not_saved'
