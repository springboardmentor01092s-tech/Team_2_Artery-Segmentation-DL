"""Validation and evaluation helpers for independent research references.

This module never creates reference measurements and never activates a grading
protocol. It rejects circular or untraceable rows before any comparison.
"""
from collections import Counter
import math


REQUIRED_FIELDS = (
    'reference_schema_version', 'case_id', 'study_id', 'frame_id', 'lesion_id',
    'source_dataset', 'source_image_sha256', 'modality', 'anatomy',
    'lesion_location_original_xy', 'reference_location_original_xy',
    'minimum_diameter', 'reference_diameter', 'diameter_unit', 'reference_method',
    'reference_method_version', 'reviewer_or_method_id', 'measured_at',
    'quality_status', 'independent_of_corovision',
)


def validate_reference_rows(rows):
    """Return normalized eligible rows; fail on missing or circular evidence."""
    if not isinstance(rows, list) or not rows:
        raise ValueError('At least one independent reference row is required')
    normalized, identities = [], set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Row {index} must be an object')
        missing = [key for key in REQUIRED_FIELDS if not str(row.get(key, '')).strip()]
        if missing:
            raise ValueError(f'Row {index} missing required fields: {", ".join(missing)}')
        if str(row['independent_of_corovision']).lower() not in {'true', '1', 'yes'}:
            raise ValueError(f'Row {index} is not independently measured')
        if str(row['quality_status']).lower() != 'eligible':
            raise ValueError(f'Row {index} is not marked eligible')
        digest = str(row['source_image_sha256']).lower()
        if len(digest) != 64 or any(character not in '0123456789abcdef' for character in digest):
            raise ValueError(f'Row {index} has invalid source image SHA-256')
        unit = str(row['diameter_unit']).lower()
        if unit not in {'source_px', 'mm'}:
            raise ValueError(f'Row {index} has unsupported diameter unit')
        if unit == 'mm' and not str(row.get('calibration_id', '')).strip():
            raise ValueError(f'Row {index} requires calibration provenance for millimetres')
        try:
            minimum, reference = float(row['minimum_diameter']), float(row['reference_diameter'])
        except (TypeError, ValueError):
            raise ValueError(f'Row {index} has nonnumeric diameters')
        if not all(math.isfinite(value) for value in (minimum, reference)) or reference <= 0 or not 0 <= minimum <= reference:
            raise ValueError(f'Row {index} has inconsistent diameters')
        identity = tuple(str(row[key]) for key in ('source_dataset', 'study_id', 'frame_id', 'lesion_id'))
        if identity in identities:
            raise ValueError(f'Row {index} duplicates a lesion identity')
        identities.add(identity)
        normalized.append({**row, 'minimum_diameter': minimum, 'reference_diameter': reference,
            'reference_narrowing_percent': (reference - minimum) / reference * 100})
    return normalized


def agreement_metrics(reference, predicted, labels):
    """Compute categorical metrics only for already paired independent labels."""
    if not reference or len(reference) != len(predicted) or not labels:
        raise ValueError('Paired labels and an ordered label set are required')
    if any(value not in labels for value in reference + predicted):
        raise ValueError('Unknown category in paired labels')
    matrix = [[0 for _ in labels] for _ in labels]
    index = {label: position for position, label in enumerate(labels)}
    for actual, estimate in zip(reference, predicted):
        matrix[index[actual]][index[estimate]] += 1
    recalls, f1s = [], []
    for position in range(len(labels)):
        tp = matrix[position][position]
        fn = sum(matrix[position]) - tp
        fp = sum(row[position] for row in matrix) - tp
        recalls.append(tp / (tp + fn) if tp + fn else None)
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0)
    total = len(reference)
    actual_counts, predicted_counts = Counter(reference), Counter(predicted)
    observed = sum((index[a] - index[b]) ** 2 for a, b in zip(reference, predicted)) / total
    expected = sum(((index[a] - index[b]) ** 2) * actual_counts[a] * predicted_counts[b]
                   for a in labels for b in labels) / (total * total)
    return {'n': total, 'accuracy': sum(a == b for a, b in zip(reference, predicted)) / total,
        'macro_f1': sum(f1s) / len(f1s), 'class_recall': dict(zip(labels, recalls)),
        'weighted_kappa': 1 - observed / expected if expected else (1.0 if observed == 0 else None),
        'confusion_matrix': matrix, 'labels': labels}
