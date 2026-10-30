"""Append-only reviewed measurements, separate from immutable AI predictions."""
import hashlib
import json
import os
from pathlib import Path

from .narrowing import diameter_reduction, severity_from_protocol


def calculate(data):
    result = diameter_reduction(minimum=data.minimum_diameter_mm,
        reference=data.reference_diameter_mm, unit='mm',
        measurement_frame=data.measurement_frame, candidate_id=data.candidate_id,
        reference_segment_id=data.reference_segment_id, protocol_id=data.protocol_id,
        calibration_verified=data.calibration_verified,
        reference_selection_reviewed=data.reference_selection_reviewed)
    protocol = None
    path = os.getenv('STENOSIS_SEVERITY_PROTOCOL')
    protocol_hash = None
    if path:
        raw = Path(path).read_bytes()
        if len(raw) > 65536:
            raise ValueError('Severity protocol exceeds size limit')
        protocol = json.loads(raw)
        protocol_hash = hashlib.sha256(raw).hexdigest()
    result['severity'] = severity_from_protocol(result['narrowing_percent'], protocol)
    result['severity_protocol_sha256'] = protocol_hash
    result['calibration_evidence'] = data.calibration_evidence
    result['measurement_evidence'] = data.measurement_evidence
    result['explanation'] = dict(method='reviewed_diameter_arithmetic_v1',
        text=f"Reviewed minimum diameter {result['minimum_diameter']} mm and reference "
             f"{result['reference_diameter']} mm yield {result['narrowing_percent']:.2f}% "
             "estimated diameter reduction. Supplied measurements are reviewer attestations; "
             "this is separate from model scores and is not automatic clinical grading.",
        source_refs=['minimum_diameter', 'reference_diameter', 'formula',
                     'calibration_evidence', 'measurement_evidence'])
    return result
