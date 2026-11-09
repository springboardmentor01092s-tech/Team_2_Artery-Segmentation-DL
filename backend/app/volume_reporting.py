"""Read-only explanations of saved 3D runs; never infer missing stages."""
import csv
import hashlib
import json
from io import StringIO

from .report_pdf import ResearchPDF


def snapshot(run):
    result = run.get('result')
    if run.get('status') != 'completed' or not isinstance(result, dict) or not result.get('model_id'):
        raise ValueError('A completed persisted volume result is required')
    stages = {
        'segmentation': {'status': 'review_required', 'reason': 'Saved model prediction; anatomical accuracy not established.'},
        'vessel_graph': {'status': 'unavailable', 'reason': 'No validated saved 3D centerline or graph in this run.'},
        'diameter_measurement': {'status': 'not_assessable', 'reason': 'No validated candidate-local cross-sectional measurement.'},
        'stenosis_detection': {'status': 'unavailable', 'reason': 'No compatible 3D stenosis checkpoint output in this run. No 2D substitution.'},
        'severity': {'status': 'not_assessable', 'reason': 'Valid local/reference diameters and approved severity protocol absent.'},
    }
    document = {'schema_version': 'corovision.volume-report.v1', 'case_id': run['case_id'],
        'analysis_run_id': run['id'], 'source_sha256': run.get('source_sha256'),
        'created_at': run.get('created_at'), 'input_kind': run.get('input_kind'),
        'model_id': result['model_id'], 'checkpoint_sha256': result.get('checkpoint_sha256'),
        'preprocessing': result.get('preprocessing'), 'source_shape': result.get('source_shape'),
        'source_affine_ras_mm': result.get('source_affine_ras_mm'),
        'execution_seconds': result.get('duration_seconds'),
        'predicted_coarse_foreground_voxels': result.get('coarse_foreground_voxels'),
        'stages': stages, 'narrowing_percent': None, 'severity_category': None,
        'human_assessment': None, 'clinical_validated': False,
        'explanation': {'method': 'deterministic_saved_volume_template',
            'text': 'This saved volume run contains a segmentation prediction and orthogonal previews. '
                    'Foreground voxel count is not accuracy, lumen diameter, disease probability or stenosis severity. '
                    'Downstream unavailable stages were not executed. Review the original volume and model limitations.'},
        'artifacts': run.get('artifacts', {}), 'limitations': result.get('limitations', [])}
    document['snapshot_sha256'] = hashlib.sha256(json.dumps(document, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return document


def csv_text(document):
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(['case_id', 'analysis_run_id', 'model_id', 'checkpoint_sha256', 'stage', 'status', 'reason'])
    def safe(value):
        text = '' if value is None else str(value)
        return "'" + text if text.startswith(('=', '+', '-', '@', '\t', '\r')) else text
    for stage, item in document['stages'].items():
        writer.writerow([safe(x) for x in [document['case_id'],document['analysis_run_id'],document['model_id'],
            document['checkpoint_sha256'],stage,item['status'],item['reason']]])
    return stream.getvalue()


def pdf_bytes(document):
    report = ResearchPDF('3D vessel analysis report')
    report.field('Case', document['case_id'])
    report.field('Saved run', document['analysis_run_id'])
    report.field('Model', document['model_id'])
    report.field('Study type', (document.get('input_kind') or 'Unavailable').replace('_', ' ').capitalize())

    report.section('Findings')
    report.field('Predicted vessel voxels (coarse grid)', document.get('predicted_coarse_foreground_voxels'))
    if document.get('source_shape'):
        report.field('Source volume dimensions', ' × '.join(map(str, document['source_shape'])) + ' voxels')
    for title, key in [('Vessel mask', 'segmentation'), ('Centerline', 'vessel_graph'),
                       ('Diameter', 'diameter_measurement'), ('Stenosis', 'stenosis_detection'),
                       ('Severity', 'severity')]:
        stage = document['stages'][key]
        report.field(title, stage['status'].replace('_', ' ').capitalize())

    report.section('Interpretation')
    report.paragraph('The saved vessel mask is a research prediction. Voxel count describes the predicted mask size. '
                     'Anatomical accuracy and clinical severity require separate validation.')
    for limitation in document['limitations']:
        report.paragraph(limitation)
    report.paragraph('See the JSON export for source geometry, checkpoint hashes and detailed stage notes.')
    return report.build()
