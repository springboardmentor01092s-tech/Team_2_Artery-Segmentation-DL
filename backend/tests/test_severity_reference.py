import pytest

from app.severity_reference import agreement_metrics, validate_reference_rows


def row(**changes):
    value = dict(reference_schema_version='1', case_id='case', study_id='study', frame_id='frame',
        lesion_id='L1', source_dataset='public-fixture', source_image_sha256='a' * 64,
        modality='XCA', anatomy='coronary artery lesion', lesion_location_original_xy='10,10',
        reference_location_original_xy='20,20', minimum_diameter='2', reference_diameter='4',
        diameter_unit='source_px', calibration_id='', reference_method='independent manual trace',
        reference_method_version='1', reviewer_or_method_id='blinded-reviewer-1',
        measured_at='2026-11-10T00:00:00Z', quality_status='eligible', exclusion_reason='',
        independent_of_corovision='true', source_notes='synthetic test row')
    value.update(changes)
    return value


def test_independent_reference_validation_and_narrowing():
    result = validate_reference_rows([row()])
    assert result[0]['reference_narrowing_percent'] == 50


@pytest.mark.parametrize('changes', [
    {'independent_of_corovision':'false'}, {'quality_status':'excluded'},
    {'source_image_sha256':'bad'}, {'minimum_diameter':'5'}, {'reference_diameter':'0'},
    {'diameter_unit':'mm'}, {'diameter_unit':'pixels'}, {'reference_method':''},
])
def test_reference_rows_fail_closed(changes):
    with pytest.raises(ValueError):
        validate_reference_rows([row(**changes)])


def test_duplicate_lesion_identity_rejected():
    with pytest.raises(ValueError):
        validate_reference_rows([row(), row(case_id='other')])


def test_agreement_metrics_known_values():
    labels = ['Normal', 'Mild', 'Moderate', 'Severe', 'Critical']
    result = agreement_metrics(['Normal', 'Mild', 'Moderate'], ['Normal', 'Moderate', 'Moderate'], labels)
    assert result['n'] == 3 and result['accuracy'] == pytest.approx(2 / 3)
    assert result['confusion_matrix'][1][2] == 1
    assert result['weighted_kappa'] is not None
