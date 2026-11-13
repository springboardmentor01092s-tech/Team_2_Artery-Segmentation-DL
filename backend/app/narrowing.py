"""Research arithmetic for reviewed local measurements, not a severity model.

No automatic extraction, clinical thresholds, global-mask diameter substitution,
prediction mutation or approval is performed here.
"""
import math


def experimental_research_grade(percent, *, authorization, uncertainty_percentage_points=None, protocol_id=None):
    """Owner-defined five-category draft; never infers occlusion or clinical validity.

    Caller supplies measurement uncertainty from recorded evidence. A missing
    uncertainty estimate cannot support a quantitative category.
    """
    selected = protocol_id or (authorization or {}).get('protocol_id', 'COROVISION_XCA_RESEARCH_5CLASS')
    informed = selected == 'COROVISION_CADRADS_INFORMED_XCA'
    result = dict(protocol_id=selected, protocol_version='1.0.0',
        authority='researcher_defined', validation_status='experimental_unvalidated',
        clinical_validated=False, category=None, status='indeterminate')
    if selected not in ('COROVISION_XCA_RESEARCH_5CLASS','COROVISION_CADRADS_INFORMED_XCA'):
        return {**result,'reason':'Unknown research protocol.'}
    if informed:
        result.update(protocol_name='CAD-RADS-informed XCA Research Severity',
            reference='https://www.jacc.org/doi/10.1016/j.jcmg.2022.07.002',
            adaptation='Continuous per-lesion XCA research bands; not official CCTA CAD-RADS reporting.')
        if not isinstance(authorization,dict) or authorization.get('protocol_id')!=selected or authorization.get('protocol_version')!='1.0.0':
            return {**result,'reason':'Exact selected protocol authorization is not recorded.'}
    if (not isinstance(authorization, dict) or authorization.get('status') != 'researcher_authorized'
            or not all(isinstance(authorization.get(key), str) and authorization[key].strip()
                       for key in ('authorized_by', 'authorized_at'))):
        return {**result, 'reason':'Researcher authorization is not recorded.'}
    result['authorization'] = dict(authorization)
    if type(percent) not in (int, float) or not math.isfinite(percent) or not 0 <= percent <= 100:
        return {**result, 'reason':'Invalid narrowing measurement.'}
    if percent == 100:
        return {**result, 'status':'possible_occlusion_requires_assessment',
            'reason':'A 100% calculation does not independently establish occlusion.'}
    uncertainty = uncertainty_percentage_points
    if type(uncertainty) not in (int, float) or not math.isfinite(uncertainty) or uncertainty < 0:
        return {**result, 'reason':'Recorded measurement uncertainty is required.'}
    def label(value):
        if informed:
            if value == 0:return 'No measured narrowing'
            if value < 25:return 'Minimal'
            if value < 50:return 'Mild'
            if value < 70:return 'Moderate'
            if value < 100:return 'Severe'
            return None
        if value == 0:
            return 'Normal'
        if value < 50:
            return 'Mild'
        if value < 70:
            return 'Moderate'
        if value < 90:
            return 'Severe'
        if value < 100:
            return 'Critical'
        return None
    lower, upper = max(0, percent - uncertainty), min(100, percent + uncertainty)
    category = label(percent)
    if label(lower) != category or label(upper) != category:
        return {**result, 'reason':'Measurement uncertainty crosses a category boundary.',
            'interval_percentage_points':[lower, upper]}
    return {**result, 'category':category, 'status':'experimental_research_classification',
        'narrowing_percent':percent, 'uncertainty_percentage_points':uncertainty,
        'interval_percentage_points':[lower, upper],
        'reason':'Full-precision researcher-defined diameter-narrowing classification.'}


def severity_from_protocol(percent, protocol):
    """Apply a trusted configured research protocol; no default clinical cutoffs."""
    if protocol is None:
        return dict(status='not_assessable', category=None,
                    reason='No approved referenced severity protocol configured.')
    if (not isinstance(protocol, dict) or protocol.get('status') != 'approved_for_research' or
            not all(isinstance(protocol.get(k), str) and protocol[k].strip()
                    for k in ('id', 'reference', 'approved_by', 'version', 'measurement_method'))):
        raise ValueError('Referenced approved research protocol required')
    applicability = protocol.get('applicability')
    if (not isinstance(applicability, dict) or
            not isinstance(applicability.get('modalities'), list) or not applicability['modalities'] or
            not isinstance(applicability.get('anatomies'), list) or not applicability['anatomies'] or
            not all(isinstance(value, str) and value.strip()
                    for value in applicability['modalities'] + applicability['anatomies'])):
        raise ValueError('Protocol modality and anatomy applicability required')
    exclusions = protocol.get('exclusions')
    if not isinstance(exclusions, list) or not all(isinstance(value, str) and value.strip() for value in exclusions):
        raise ValueError('Protocol exclusions must be recorded')
    bands = protocol.get('bands')
    if not isinstance(bands, list) or not bands:
        raise ValueError('Protocol bands required')
    end = 0
    labels = set()
    for band in bands:
        if not isinstance(band, dict):
            raise ValueError('Protocol band must be an object')
        lo, hi, label = band.get('lower'), band.get('upper'), band.get('label')
        if (any(type(v) not in (float, int) or not math.isfinite(v) for v in (lo, hi))
                or lo != end or not lo < hi <= 100 or
                not isinstance(label, str) or not label.strip() or label in labels):
            raise ValueError('Bands must uniquely partition 0 through 100')
        labels.add(label)
        end = hi
    if end != 100 or type(percent) not in (float, int) or not math.isfinite(percent) or not 0 <= percent <= 100:
        raise ValueError('Finite percent and complete protocol required')
    match = next(b for b in bands if b['lower'] <= percent < b['upper'] or percent == b['upper'] == 100)
    return dict(status='research_protocol_classification', category=match['label'],
                protocol_id=protocol['id'], protocol_version=protocol['version'],
                reference=protocol['reference'], measurement_method=protocol['measurement_method'],
                applicability=applicability, exclusions=exclusions, clinical_validated=False)


def diameter_reduction(*, minimum, reference, unit, measurement_frame,
                       candidate_id, reference_segment_id, protocol_id,
                       calibration_verified, reference_selection_reviewed,
                       lumen_boundaries_reviewed=True, reference_segment_suitable=True,
                       anatomy_ambiguous=False, image_quality_acceptable=True):
    """Calculate only from explicit, compatible, reviewed diameter evidence.

    Both inputs must use the same unit/frame. Callers must obtain these from a
    persisted reviewed measurement record, not model confidence or global means.
    The function does not independently certify those source attestations.
    """
    if any(value is not True for value in (calibration_verified, reference_selection_reviewed,
                                            lumen_boundaries_reviewed, reference_segment_suitable,
                                            image_quality_acceptable)) or anatomy_ambiguous is not False:
        raise ValueError('Reviewed calibration, boundaries, image quality and suitable unambiguous reference required')
    if unit != 'mm':
        raise ValueError('Physical diameter measurements in mm required')
    for value in (measurement_frame, candidate_id, reference_segment_id, protocol_id):
        if not isinstance(value, str) or not value.strip() or len(value)>180:
            raise ValueError('Measurement frame, candidate, reference and protocol identity required')
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in (minimum, reference)):
        raise ValueError('Finite numeric diameters required')
    if reference <= 0 or minimum < 0 or minimum > reference:
        raise ValueError('Diameters inconsistent; do not clamp or invent a result')
    return dict(status='research_calculation', narrowing_percent=(reference-minimum)/reference*100,
                minimum_diameter=minimum, reference_diameter=reference, diameter_unit=unit,
                measurement_frame=measurement_frame, candidate_id=candidate_id,
                reference_segment_id=reference_segment_id, protocol_id=protocol_id,
                quality_gate=dict(status='passed', calibration_verified=True,
                    lumen_boundaries_reviewed=True, reference_selection_reviewed=True,
                    reference_segment_suitable=True, anatomy_ambiguous=False,
                    image_quality_acceptable=True),
                formula='100 * (reference - minimum) / reference',
                category=None, clinical_validated=False,
                limitation='Arithmetic from supplied reviewed measurements; not validated automatic grading or diagnosis.')
