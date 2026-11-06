"""Synthetic scalar-profile tests only; no medical images/models or research inference."""
from dataclasses import replace
import math
import pytest

from app.geometry_candidates import ProfilePolicy, extract_profile_candidates


POLICY = ProfilePolicy('synthetic-test-only-v1', .7, 0, 2, 2, 2., 0., .2)


def run(widths, policy=POLICY, **changes):
    samples = [dict(x=float(i), y=5., arc_length=float(i), width=float(w), quality_flags=[])
               for i, w in enumerate(widths)]
    options = dict(samples=samples, policy=policy, analysis_run_id='synthetic-run',
                   vessel_path_id='synthetic-path', source_profile_id='synthetic-profile',
                   coordinate_frame='source_image_xy', unit='pixels')
    options.update(changes)
    return extract_profile_candidates(**options)


def widths():
    value = [6.]*30
    value[10:13] = [3.]*3
    return value


def test_constant_width_has_no_candidates_and_does_not_claim_healthy():
    result = run([6.]*30)
    assert result['candidates'] == []
    assert result['coverage']['samples_without_two_sided_reference'] > 0
    assert result['clinical_validated'] is False
    assert 'does not establish' in result['absence_interpretation']


def test_focal_interval_preserves_reference_indices_coordinates_and_scope():
    result = run(widths())
    candidate, = result['candidates']
    assert candidate['interval_indices'] == [10, 12]
    assert candidate['reference_indices'] == {'proximal': [6, 7], 'distal': [15, 16]}
    assert candidate['relative_mask_width_ratio'] == .5
    assert candidate['candidate_length'] == 2
    assert candidate['minimum_point'] == [10., 5.]
    assert candidate['status'] == 'REQUIRES_HUMAN_REVIEW'
    assert candidate['model_score'] is None
    assert candidate['clinical_severity'] is None
    assert candidate['clinical_narrowing_percent'] is None
    assert result['analysis_run_id'] == candidate['analysis_run_id']
    assert len(result['source_profile_sha256']) == 64


def test_merging_is_explicit_and_seed_intervals_preserved():
    value = [6.]*30
    value[10] = value[13] = 3.
    separate = run(value, replace(POLICY, minimum_length=0))
    merged = run(value, replace(POLICY, minimum_length=0, merge_gap=3))
    assert len(separate['candidates']) == 2
    candidate, = merged['candidates']
    assert candidate['interval_indices'] == [10, 13]
    assert candidate['seed_intervals'] == [[10, 10], [13, 13]]


def test_rejected_short_candidate_retained():
    result = run(widths(), replace(POLICY, minimum_length=4))
    candidate, = result['candidates']
    assert candidate['status'] == 'REJECTED_ARTIFACT'
    assert 'candidate_shorter_than_policy_minimum' in candidate['rejection_reasons']


def test_reference_and_interval_quality_flags_are_preserved():
    samples = [dict(x=float(i), y=0., arc_length=float(i), width=w, quality_flags=[])
               for i, w in enumerate(widths())]
    samples[6]['quality_flags'] = ['branch_proximity']
    candidate, = run(widths(), samples=samples)['candidates']
    assert candidate['status'] == 'REJECTED_ARTIFACT'
    assert candidate['quality_flags'] == ['branch_proximity']


@pytest.mark.parametrize('value', [0, -1, math.nan, math.inf, True])
def test_invalid_width_fails_closed(value):
    samples = [dict(x=0., y=0., arc_length=0., width=value)]
    with pytest.raises(ValueError):
        run([], samples=samples)


def test_no_physical_units_without_calibration_or_unmapped_coordinates():
    with pytest.raises(ValueError):
        run(widths(), unit='mm')
    with pytest.raises(ValueError):
        run(widths(), coordinate_frame='prepared_512_xy')
    with pytest.raises(ValueError):
        run(widths(), analysis_run_id='')


def test_smoothing_and_policy_changes_are_explicit_and_recorded():
    value = [6.]*30
    value[10] = 3.
    assert run(value, replace(POLICY, minimum_length=0))['candidates']
    result = run(value, replace(POLICY, smoothing_radius=1, version='synthetic-smoothed-v2'))
    assert result['candidates'] == []
    assert result['policy']['version'] == 'synthetic-smoothed-v2'
