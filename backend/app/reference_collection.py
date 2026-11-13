"""Convert manual drafts and create new immutable-by-convention cohort snapshots."""
import csv
from hashlib import sha256
import json
import math
from pathlib import Path

from .severity_reference import REQUIRED_FIELDS, validate_reference_rows


def convert_draft(draft, image_path):
    required = ('source_dataset', 'case_id', 'study_id', 'lesion_id', 'reference_segment_id',
                'reviewer', 'notes', 'frame_id', 'measured_at')
    if any(not isinstance(draft.get(key), str) or not draft[key].strip() for key in required):
        raise ValueError('Complete source, case, study, lesion, segment and reviewer context required')
    if draft.get('blinded') is not True or draft.get('quality') != 'eligible':
        raise ValueError('Only completed eligible model-blinded measurements may be locked')
    image_path = Path(image_path)
    if image_path.name != draft['frame_id'] or sha256(image_path.read_bytes()).hexdigest() != draft.get('source_image_sha256'):
        raise ValueError('Original frame filename or image hash mismatch')
    from PIL import Image
    with Image.open(image_path) as image:
        width, height = image.size
    pairs = {}
    for tool in ('mld', 'rvd'):
        points = [point for point in draft.get('endpoints', []) if point.get('tool') == tool]
        if len(points) != 2:
            raise ValueError('Exactly two endpoints per measurement required')
        for point in points:
            x, y = point.get('x'), point.get('y')
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in (x,y)) or not (0 <= x < width and 0 <= y < height):
                raise ValueError('Endpoints must lie within the original image')
        pairs[tool] = points
    def distance(tool):
        a,b = pairs[tool]
        return math.hypot(a['x']-b['x'], a['y']-b['y'])
    for tool, field in (('mld','minimum_diameter'), ('rvd','reference_diameter')):
        value = draft.get(field)
        if type(value) not in (int,float) or not math.isclose(value,distance(tool),abs_tol=1e-8):
            raise ValueError('Recorded width differs from endpoint geometry')
    row = {key:draft[key] for key in ('source_dataset','case_id','study_id','lesion_id','frame_id','source_image_sha256','measured_at')}
    row.update(reference_schema_version='1', modality='XCA', anatomy='coronary artery lesion',
        lesion_location_original_xy=json.dumps(pairs['mld']), reference_location_original_xy=json.dumps(pairs['rvd']),
        minimum_diameter=distance('mld'), reference_diameter=distance('rvd'), diameter_unit='source_px',
        reference_method=draft['reference_method'], reference_method_version=draft['reference_method_version'],
        reviewer_or_method_id=draft['reviewer'], quality_status='eligible', independent_of_corovision='true',
        calibration_id='', exclusion_reason='', source_notes=json.dumps({'reference_segment_id':draft['reference_segment_id'],
            'notes':draft['notes'], 'checkpoint_exposure':draft.get('checkpoint_exposure'), 'expert_qca':False}))
    validate_reference_rows([row])
    return row


def lock_cohort(rows, output, version):
    validate_reference_rows(rows)
    if not isinstance(version,str) or not version.strip():
        raise ValueError('Cohort version required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    fields = list(REQUIRED_FIELDS) + ['calibration_id','exclusion_reason','source_notes']
    with (output/'references.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    receipt={'version':version,'rows':len(rows),'sha256':sha256((output/'references.csv').read_bytes()).hexdigest(),
        'evaluation_scope':'exploratory; checkpoint independence must be separately established',
        'clinical_validated':False}
    (output/'lock_receipt.json').write_text(json.dumps(receipt,indent=2))
    return receipt


def import_and_lock_csv(csv_path, image_directory, output, version):
    """Verify browser CSV against original images before creating a snapshot."""
    with Path(csv_path).open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    validate_reference_rows(rows)
    root = Path(image_directory).resolve(strict=True)
    verified = []
    for row in rows:
        filename = row['frame_id']
        if Path(filename).name != filename or '/' in filename or '\\' in filename:
            raise ValueError('Frame ID must be an original image filename')
        path = (root / filename).resolve(strict=True)
        if path.parent != root:
            raise ValueError('Image must remain within the supplied image directory')
        notes = json.loads(row.get('source_notes') or '{}')
        draft = dict(row, reviewer=row['reviewer_or_method_id'], quality=row['quality_status'],
            blinded=row['independent_of_corovision'].lower() == 'true',
            reference_segment_id=notes.get('reference_segment_id'), notes=notes.get('notes'),
            endpoints=json.loads(row['lesion_location_original_xy']) + json.loads(row['reference_location_original_xy']),
            minimum_diameter=float(row['minimum_diameter']), reference_diameter=float(row['reference_diameter']),
            checkpoint_exposure=notes.get('checkpoint_exposure'))
        if row['diameter_unit'] != 'source_px':
            raise ValueError('Manual endpoint import currently supports source_px only')
        converted = convert_draft(draft, path)
        # Keep the exported evidence byte values after geometric verification.
        verified.append(row)
    receipt = lock_cohort(verified, output, version)
    reopened = verify_locked_cohort(output)
    if reopened != verified:
        raise ValueError('Locked CSV differs from verified imported rows')
    return receipt


def verify_locked_cohort(directory):
    directory = Path(directory)
    receipt = json.loads((directory/'lock_receipt.json').read_text())
    payload = (directory/'references.csv').read_bytes()
    if sha256(payload).hexdigest() != receipt['sha256']:
        raise ValueError('Locked cohort SHA-256 mismatch')
    with (directory/'references.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    validate_reference_rows(rows)
    if len(rows) != receipt['rows']:
        raise ValueError('Locked cohort row count mismatch')
    return rows


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Verify browser reference CSV and create a new cohort snapshot')
    parser.add_argument('--csv', required=True)
    parser.add_argument('--images', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    print(json.dumps(import_and_lock_csv(args.csv, args.images, args.output, args.version), indent=2))
