"""Inactive spatial association of saved source boxes and ordered source paths.

Pure coordinate software. No images, model scores, clinical artery identity,
lesion severity, path interpolation or live detector activation.
"""
import math


def associate_candidate_paths(*, candidate, paths, analysis_run_id, minimum_fraction,
                              minimum_points, ambiguity_margin):
    """Record sampled-path evidence; abstain when evidence is absent or ambiguous.

    Fraction = supplied path samples inside the source bbox / all supplied path
    samples. Sampling density affects it; it is not confidence or lesion IoU.
    Bbox edges are half-open, matching the saved candidate coordinate contract.
    All thresholds must be supplied by a separately versioned caller policy.
    """
    if not isinstance(analysis_run_id, str) or not analysis_run_id.strip():
        raise ValueError('Analysis run identity required')
    if (type(minimum_points) is not int or minimum_points < 1
            or type(minimum_fraction) not in (int, float)
            or not math.isfinite(minimum_fraction) or not 0 < minimum_fraction <= 1
            or type(ambiguity_margin) not in (int, float)
            or not math.isfinite(ambiguity_margin) or not 0 <= ambiguity_margin <= 1):
        raise ValueError('Explicit finite association thresholds required')
    if (candidate.get('analysis_run_id') != analysis_run_id
            or candidate.get('coordinate_frame') != 'source_image_xy'):
        raise ValueError('Candidate run/source coordinate mismatch')
    if not isinstance(candidate.get('candidate_id'), str) or not candidate['candidate_id']:
        raise ValueError('Candidate identity required')
    source_image_id = candidate.get('source_image_id')
    if not isinstance(source_image_id, str) or not source_image_id.strip():
        raise ValueError('Candidate source image identity required')
    box = candidate.get('bbox_source_xyxy')
    if (not isinstance(box, (list, tuple)) or len(box) != 4
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in box)
            or box[0] < 0 or box[1] < 0 or box[2] <= box[0] or box[3] <= box[1]):
        raise ValueError('Valid source bbox required')
    evidence = []
    seen = set()
    for path in paths:
        if (path.get('analysis_run_id') != analysis_run_id
                or path.get('coordinate_frame') != 'source_image_xy'):
            raise ValueError('Path run/source coordinate mismatch')
        if path.get('source_image_id') != source_image_id:
            raise ValueError('Path source image identity mismatch')
        identity = path.get('path_id')
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError('Unique saved path identities required')
        seen.add(identity)
        points = path.get('points')
        if not isinstance(points, list) or not points:
            raise ValueError('Nonempty ordered source points required')
        inside = []
        for index, point in enumerate(points):
            if (not isinstance(point, (list, tuple)) or len(point) != 2
                    or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in point)):
                raise ValueError('Finite nonnegative source points required')
            if box[0] <= point[0] < box[2] and box[1] <= point[1] < box[3]:
                inside.append(index)
        fraction = len(inside) / len(points)
        evidence.append(dict(path_id=identity, total_supplied_points=len(points),
                             inside_point_indices=inside, inside_fraction=fraction,
                             eligible=len(inside) >= minimum_points and fraction >= minimum_fraction))
    eligible = sorted((r for r in evidence if r['eligible']), key=lambda r: (-r['inside_fraction'], r['path_id']))
    selected = None
    if not eligible:
        status = 'unassociated'
    elif len(eligible) > 1 and eligible[0]['inside_fraction'] - eligible[1]['inside_fraction'] <= ambiguity_margin:
        status = 'ambiguous_requires_review'
    else:
        selected = eligible[0]['path_id']
        status = 'spatial_path_association_requires_review'
    return dict(schema_version='corovision.candidate_path_association.v2',
                analysis_run_id=analysis_run_id, candidate_id=candidate['candidate_id'],
                source_image_id=source_image_id,
                coordinate_frame='source_image_xy', selected_path_id=selected,
                status=status, anatomical_artery_identity=None, clinical_validation=False,
                evidence=evidence, policy=dict(minimum_fraction=minimum_fraction,
                minimum_points=minimum_points, ambiguity_margin=ambiguity_margin),
                limitation='Sampled source-box/path coincidence only; not confidence, lesion overlap or anatomical validation.')
