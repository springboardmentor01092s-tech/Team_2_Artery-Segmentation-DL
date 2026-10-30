"""Research arithmetic for reviewed local measurements, not a severity model.

No automatic extraction, clinical thresholds, global-mask diameter substitution,
prediction mutation or approval is performed here.
"""
import math


def severity_from_protocol(percent, protocol):
    """Apply a trusted configured research protocol; no default clinical cutoffs."""
    if protocol is None:
        return dict(status='not_assessable', category=None,
                    reason='No approved referenced severity protocol configured.')
    if (not isinstance(protocol, dict) or protocol.get('status') != 'approved_for_research' or
            not all(isinstance(protocol.get(k), str) and protocol[k].strip()
                    for k in ('id', 'reference', 'approved_by', 'version'))):
        raise ValueError('Referenced approved research protocol required')
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
                reference=protocol['reference'], clinical_validated=False)


def diameter_reduction(*, minimum, reference, unit, measurement_frame,
                       candidate_id, reference_segment_id, protocol_id,
                       calibration_verified, reference_selection_reviewed):
    """Calculate only from explicit, compatible, reviewed diameter evidence.

    Both inputs must use the same unit/frame. Callers must obtain these from a
    persisted reviewed measurement record, not model confidence or global means.
    The function does not independently certify those source attestations.
    """
    if calibration_verified is not True or reference_selection_reviewed is not True:
        raise ValueError('Verified calibration and reviewed reference selection required')
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
                formula='100 * (reference - minimum) / reference',
                category=None, clinical_validated=False,
                limitation='Arithmetic from supplied reviewed measurements; not validated automatic grading or diagnosis.')
