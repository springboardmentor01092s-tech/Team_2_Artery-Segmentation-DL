"""Immutable research snapshot rendering. No clinical approval or inferred grading."""
import csv
from io import StringIO
import json
from pathlib import Path
from xml.sax.saxutils import escape
from .evidence_status import stenosis_mask_status
from .report_pdf import ResearchPDF

SECTIONS = {'images', 'measurements', 'candidates', 'review', 'appendix'}
NOTICE = ('Research output, not a standalone diagnosis. Model scores are uncalibrated. '
          'Mask pixels do not establish narrowing or clinical severity. Missing measurements are unavailable, not zero. '
          'This research snapshot is not a clinically approved report.')


def stenosis_count_text(result):
    status = stenosis_mask_status(result)
    if status == 'not_assessed':
        return 'Not assessed'
    if status == 'not_saved':
        return 'Not saved'
    count = result.get('stenosis_pixels') if isinstance(result, dict) else None
    return f'{count} px' if count is not None else 'Unavailable'


def tabular(snapshot):
    result = snapshot['analysis']
    vessel = result.get('vessel_analysis') or {}
    review = snapshot.get('human_review') or {}
    fields = {'report_id': snapshot['report_id'], 'report_version': snapshot['version'],
              'generated_at': snapshot['generated_at'], 'case_id': snapshot['case']['id'],
              'case_code': snapshot['case']['case_code'], 'image_id': snapshot['image']['id'],
              'analysis_run_id': result['id'], 'model_version': result['model_version'],
              'artery_pixels': result['artery_pixels'],
              'stenosis_pixels': result['stenosis_pixels'] if stenosis_mask_status(result) == 'recorded' else None,
              'stenosis_mask_status': stenosis_mask_status(result),
              'centerline_length': vessel.get('centerline_length'), 'mean_diameter': vessel.get('mean_diameter'),
              'measurement_unit': vessel.get('diameter_unit'), 'human_review_id': review.get('id'),
              'human_assessed_severity': review.get('stenosis_severity'),
              'automated_severity': 'unavailable', 'notice': NOTICE}
    if 'measurements' not in snapshot['sections']:
        for key in ['centerline_length', 'mean_diameter', 'measurement_unit']:
            fields.pop(key)
    else:
        fields['reviewed_stenosis_measurements'] = json.dumps(snapshot.get('reviewed_stenosis_measurements', []), ensure_ascii=False)
    if 'review' not in snapshot['sections']:
        for key in ['human_review_id', 'human_assessed_severity']:
            fields.pop(key)
    if 'images' in snapshot['sections']:
        fields['image_panels'] = json.dumps(snapshot.get('image_panels', []), ensure_ascii=False)
    def safe(value):
        text = 'Unavailable' if value is None else str(value)
        return "'" + text if text.startswith(('=', '+', '-', '@', '\t', '\r')) else text
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(fields.keys())
    writer.writerow([safe(v) for v in fields.values()])
    return output.getvalue()


def pdf_bytes(snapshot, image_paths):
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image, Paragraph, Table, TableStyle

    report = ResearchPDF('Coronary analysis report')
    case, image, result = (snapshot[key] for key in ('case', 'image', 'analysis'))
    sections = snapshot['sections']
    structured = result.get('structured_result') or {}
    vessel = result.get('vessel_analysis') or {}
    report.field('Case', case['case_code'])
    report.field('Study', image.get('original_name'))
    if case.get('modality'):
        report.field('Modality', case['modality'])
    report.field('Saved run', result['id'])
    report.field('Report version', snapshot['version'])
    report.field('Snapshot date (UTC)', snapshot['generated_at'].replace('T', ' ').split('.')[0].removesuffix('+00:00'))

    report.section('Findings')
    report.field('Artery mask', f"{result['artery_pixels']:,} px")
    report.field('Stenosis mask', stenosis_count_text(result))
    if 'measurements' in sections:
        for label, key in [('Centerline length', 'centerline_length'), ('Mean sampled width', 'mean_diameter')]:
            value = vessel.get(key)
            unit = vessel.get('diameter_unit')
            report.field(label, f'{value} {unit}' if value is not None and unit else None)
    if 'candidates' in sections:
        candidates = structured.get('candidates') or []
        report.field('Saved candidate locations', len(candidates) if 'candidates' in structured else None)
        for candidate in candidates:
            box = candidate.get('bbox_source_xyxy')
            if box:
                report.field(str(candidate.get('candidate_id') or 'Candidate'), f'Source-image bounds (px) {box}')

    if 'measurements' in sections:
        records = snapshot.get('reviewed_stenosis_measurements') or []
        report.section('Reviewed narrowing measurements')
        if not records:
            report.paragraph('No calibrated lesion and reference measurements are saved for this run.')
        for record in records:
            measurement = record['result']
            report.field(f"Candidate {measurement['candidate_id']}",
                         f"{measurement['narrowing_percent']:.2f}% reduction from reviewed measurements")
            report.field('Research grade', measurement['severity'].get('category') or 'Not assessable')

    if 'review' in sections:
        report.section('Human review')
        review = snapshot.get('human_review')
        if review:
            for label, key in [('Reviewer', 'reviewer_name'), ('Decision', 'decision'),
                               ('Assessed severity', 'stenosis_severity'), ('Notes', 'notes')]:
                if review.get(key):
                    value = review[key].replace('_', ' ').capitalize() if key in {'decision', 'stenosis_severity'} else review[key]
                    report.field(label, value)
        else:
            report.paragraph('No human review is linked to this run.')

    report.section('Interpretation')
    report.paragraph('Model predictions are for research review. Automated clinical severity is unavailable. '
                     'Pixel measurements require calibration to support physical diameter estimates. '
                     'An empty result does not establish absence of disease.')
    for flag in vessel.get('quality_flags', []):
        if flag.get('message'):
            report.paragraph(flag['message'])

    if 'images' in sections:
        figures = []
        column_width = report.document.width / 2 - 6
        for label, path in image_paths:
            if path is None or (isinstance(path, Path) and not path.is_file()):
                continue
            source = str(path) if isinstance(path, Path) else path
            try:
                width, height = ImageReader(source).getSize()
            except (OSError, ValueError, TypeError):
                continue
            scale = min((column_width - 12) / width, 144 / height)
            if hasattr(source, 'seek'):
                source.seek(0)
            figures.append([Image(source, width=width * scale, height=height * scale),
                            Paragraph(escape(label), report.body)])
        report.section('Saved images')
        if figures:
            report.story.append(Table([figures], colWidths=[column_width] * len(figures),
                hAlign='LEFT', style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')])))
        else:
            report.paragraph('No selected saved images could be rendered.')

    if 'appendix' in sections:
        report.section('Technical reference')
        report.field('Report ID', snapshot['report_id'])
        report.field('Model version', result['model_version'])
        report.field('Analysis date', result.get('created_at'))
        report.paragraph('See the JSON export for checkpoint hashes, preprocessing and evaluation references.')

    return report.build()
