"""Inactive research candidate generator for supplied ordered mask-width profiles.

No image/model execution, calibrated confidence, clinical grade or detector fusion.
Parameters must be supplied explicitly; no clinical cutoff is built in.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from statistics import median


@dataclass(frozen=True)
class ProfilePolicy:
    version: str
    ratio_threshold: float
    smoothing_radius: int
    reference_points: int
    reference_guard_points: int
    minimum_length: float
    merge_gap: float
    maximum_reference_cv: float

    def validate(self):
        if not self.version or not 0 < self.ratio_threshold < 1:
            raise ValueError('Named version and explicit ratio in (0,1) required')
        for value, lower in [(self.smoothing_radius, 0), (self.reference_points, 1),
                             (self.reference_guard_points, 0)]:
            if type(value) is not int or value < lower:
                raise ValueError('Invalid profile window')
        for value in [self.minimum_length, self.merge_gap, self.maximum_reference_cv]:
            if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
                raise ValueError('Finite nonnegative policy values required')


def extract_profile_candidates(*, samples, policy, analysis_run_id, vessel_path_id,
                               source_profile_id, coordinate_frame, unit,
                               calibration_verified=False):
    """Use proximal/distal median widths; preserve every detected/merged interval.

    Samples contain x,y,arc_length,width and optional quality_flags. Coordinates
    must already be in the declared source frame. This function never maps them.
    Widths are mask-width estimates supplied by an upstream geometry adapter.
    """
    policy.validate()
    if not all(isinstance(v, str) and v.strip() for v in
               [analysis_run_id, vessel_path_id, source_profile_id, coordinate_frame]):
        raise ValueError('Run, path, source profile and coordinate frame required')
    if coordinate_frame != 'source_image_xy':
        raise ValueError('Only explicitly mapped 2D source-image coordinates supported')
    if unit not in ('pixels', 'mm') or (unit == 'mm' and calibration_verified is not True):
        raise ValueError('Physical units require verified calibration')
    values = []
    previous = None
    for sample in samples:
        for key in ['x', 'y', 'arc_length', 'width']:
            value = sample.get(key)
            if type(value) not in (float, int) or not math.isfinite(value):
                raise ValueError('Finite numeric profile samples required')
        if sample['width'] <= 0 or sample['arc_length'] < 0:
            raise ValueError('Positive width and nonnegative arc length required')
        if previous is not None and sample['arc_length'] <= previous:
            raise ValueError('Profile arc lengths must be strictly increasing')
        flags = sample.get('quality_flags', [])
        if not isinstance(flags, list) or any(not isinstance(flag, str) for flag in flags):
            raise ValueError('Quality flags must be a list of strings')
        previous = sample['arc_length']
        values.append(float(sample['width']))
    n = len(values)
    smooth = [median(values[max(0, i-policy.smoothing_radius):min(n, i+policy.smoothing_radius+1)])
              for i in range(n)]

    def references(start, end):
        left_end = max(0, start-policy.reference_guard_points)
        right_start = min(n, end+1+policy.reference_guard_points)
        left = list(range(max(0, left_end-policy.reference_points), left_end))
        right = list(range(right_start, min(n, right_start+policy.reference_points)))
        if len(left) != policy.reference_points or len(right) != policy.reference_points:
            return left, right, None
        # Raw flanking widths prevent smoothing across the candidate from
        # contaminating the separately recorded reference measurements.
        return left, right, (median(values[i] for i in left)+median(values[i] for i in right))/2

    seeds = []
    for i in range(n):
        left, right, reference = references(i, i)
        if reference is not None and smooth[i] / reference <= policy.ratio_threshold:
            seeds.append(i)
    intervals = []
    for i in seeds:
        if intervals and i == intervals[-1][1]+1:
            intervals[-1][1] = i
        else:
            intervals.append([i, i])
    merged = []
    for interval in intervals:
        if merged and samples[interval[0]]['arc_length']-samples[merged[-1]['end']]['arc_length'] <= policy.merge_gap:
            merged[-1]['end'] = interval[1]
            merged[-1]['seed_intervals'].append(interval)
        else:
            merged.append({'start': interval[0], 'end': interval[1], 'seed_intervals': [interval]})
    candidates = []
    for interval in merged:
        start, end = interval['start'], interval['end']
        left, right, reference = references(start, end)
        minimum_index = min(range(start, end+1), key=lambda i: smooth[i])
        length = samples[end]['arc_length']-samples[start]['arc_length']
        reasons = []
        inspected = list(range(start, end+1))+left+right
        flags = sorted({flag for i in inspected for flag in samples[i].get('quality_flags', [])})
        if length < policy.minimum_length:
            reasons.append('candidate_shorter_than_policy_minimum')
        if reference is None:
            reasons.append('complete_proximal_distal_reference_unavailable')
        else:
            reference_values = [values[i] for i in left+right]
            mean = sum(reference_values)/len(reference_values)
            cv = math.sqrt(sum((v-mean)**2 for v in reference_values)/len(reference_values))/mean
            if cv > policy.maximum_reference_cv:
                reasons.append('reference_width_unstable')
            if smooth[minimum_index]/reference > policy.ratio_threshold:
                reasons.append('interval_reference_does_not_confirm_seed_ratio')
        if flags:
            reasons.append('upstream_geometry_quality_flags')
        ratio = smooth[minimum_index]/reference if reference is not None else None
        candidates.append(dict(candidate_id=f'G{len(candidates)+1}',
            analysis_run_id=analysis_run_id, vessel_path_id=vessel_path_id,
            source_profile_id=source_profile_id, generator='mask_width_profile_v1',
            method='mean_of_proximal_and_distal_median_widths', policy_version=policy.version,
            coordinate_frame=coordinate_frame, unit=unit,
            start_point=[samples[start]['x'], samples[start]['y']],
            end_point=[samples[end]['x'], samples[end]['y']],
            minimum_point=[samples[minimum_index]['x'], samples[minimum_index]['y']],
            interval_indices=[start, end], seed_intervals=interval['seed_intervals'],
            reference_indices=dict(proximal=left, distal=right), candidate_length=length,
            reference_mask_width=reference, minimum_smoothed_mask_width=smooth[minimum_index],
            minimum_raw_mask_width=min(values[start:end+1]), relative_mask_width_ratio=ratio,
            status='UNMEASURABLE' if reference is None else ('REJECTED_ARTIFACT' if reasons else 'REQUIRES_HUMAN_REVIEW'),
            rejection_reasons=reasons, quality_flags=flags, model_score=None,
            clinical_severity=None, clinical_narrowing_percent=None,
            measurement_scope='unvalidated_2d_mask_width_geometry_not_lumen_measurement',
            human_review_required=True))
    canonical = json.dumps(samples, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return dict(schema_version='corovision.geometry_candidates.v1', analysis_run_id=analysis_run_id,
        source_profile_id=source_profile_id, source_profile_sha256=hashlib.sha256(canonical).hexdigest(),
        policy=asdict(policy), coordinate_frame=coordinate_frame, unit=unit,
        samples=samples, smoothed_mask_widths=smooth, candidates=candidates,
        coverage=dict(samples=n, samples_without_two_sided_reference=sum(references(i, i)[2] is None for i in range(n))),
        detector_fusion=False, research_validated=False, clinical_validated=False,
        automatic_activation=False, absence_interpretation='No geometric candidates does not establish absence of disease')
