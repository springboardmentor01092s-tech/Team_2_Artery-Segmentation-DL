"""Immutable research snapshot rendering. No clinical approval or inferred grading."""
import csv
from io import BytesIO, StringIO
import json
from pathlib import Path
from xml.sax.saxutils import escape

SECTIONS = {'images', 'measurements', 'candidates', 'review', 'appendix'}
NOTICE = ('Research output, not a standalone diagnosis. Model scores are uncalibrated. '
          'Mask pixels do not establish narrowing or clinical severity. Missing measurements are unavailable, not zero. '
          'This research snapshot is not a clinically approved report.')


def tabular(snapshot):
    result = snapshot['analysis']
    vessel = result.get('vessel_analysis') or {}
    review = snapshot.get('human_review') or {}
    fields = {'report_id': snapshot['report_id'], 'report_version': snapshot['version'],
              'generated_at': snapshot['generated_at'], 'case_id': snapshot['case']['id'],
              'case_code': snapshot['case']['case_code'], 'image_id': snapshot['image']['id'],
              'analysis_run_id': result['id'], 'model_version': result['model_version'],
              'artery_pixels': result['artery_pixels'], 'stenosis_pixels': result['stenosis_pixels'],
              'centerline_length': vessel.get('centerline_length'), 'mean_diameter': vessel.get('mean_diameter'),
              'measurement_unit': vessel.get('diameter_unit'), 'human_review_id': review.get('id'),
              'human_assessed_severity': review.get('stenosis_severity'),
              'automated_severity': 'unavailable', 'notice': NOTICE}
    if 'measurements' not in snapshot['sections']:
        for key in ['centerline_length', 'mean_diameter', 'measurement_unit']:
            fields.pop(key)
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
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether
    from reportlab.lib.utils import ImageReader
    output = BytesIO()
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(output, title='CoroVision AI Research Analysis Report',
                                 rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    story = []
    def paragraph(text, style='BodyText'):
        story.append(Paragraph(escape(str(text)).replace('\n', '<br/>'), styles[style]))
        if style not in {'Heading2', 'Heading3', 'Title'}:
            story.append(Spacer(1, 8))
    paragraph('CoroVision AI — Research Analysis Report', 'Title')
    paragraph(f"{snapshot['case']['case_code']} · research snapshot v{snapshot['version']}", 'Heading2')
    paragraph(NOTICE)
    for key in ['report_id', 'generated_at']:
        paragraph(f'{key}: {snapshot[key]}')
    paragraph(f"Case: {snapshot['case']['id']} | Image: {snapshot['image']['id']} | Analysis run: {snapshot['analysis']['id']}")
    paragraph(f"Modality: {snapshot['case'].get('modality', 'Unavailable')} | Anatomy: {snapshot['case'].get('anatomy', 'Unavailable')} | Source dimensions: {snapshot['image'].get('width', 'Unavailable')} x {snapshot['image'].get('height', 'Unavailable')}")
    paragraph(f"Model: {snapshot['analysis']['model_version']} | Analysis timestamp: {snapshot['analysis']['created_at']}")
    paragraph('Model and preprocessing provenance', 'Heading2')
    provenance = snapshot['provenance']
    models = provenance.get('models') or {}
    paragraph('Model/checkpoint references: ' + json.dumps(models, ensure_ascii=False))
    processing = provenance.get('preprocessing') or {}
    paragraph('Preprocessing: ' + json.dumps({key: processing.get(key, 'Unavailable') for key in
        ['pipeline_version', 'profile', 'standard_pipeline', 'model_input_resize', 'source_format', 'options', 'steps']}, ensure_ascii=False))
    paragraph('Full exact preprocessing configuration and hashes are preserved in the JSON export.')
    if 'images' in snapshot['sections']:
        for label, path in image_paths:
            try:
                if path is None:
                    raise ValueError('No saved artifact')
                source = str(path) if isinstance(path, Path) else path
                width, height = ImageReader(source).getSize()
                scale = min(6.5 * inch / width, 3.7 * inch / height)
                if hasattr(source, 'seek'):
                    source.seek(0)
                story.append(KeepTogether([Paragraph(escape(label), styles['Heading3']), Spacer(1, 8),
                                          Image(source, width=width*scale, height=height*scale)]))
            except Exception:
                paragraph(label, 'Heading3')
                paragraph('Artifact unavailable or source format not renderable. No substitute prediction is shown.')
    paragraph('Saved model outputs', 'Heading2')
    paragraph(f"Artery mask: {snapshot['analysis']['artery_pixels']} px; stenosis mask: {snapshot['analysis']['stenosis_pixels']} px.")
    vessel = snapshot['analysis'].get('vessel_analysis') or {}
    measurements = {key: vessel.get(key, 'Unavailable') for key in ['centerline_length', 'mean_diameter',
        'minimum_diameter', 'maximum_diameter', 'diameter_unit', 'branching_points', 'endpoints',
        'connected_components', 'continuity_ratio', 'tortuosity', 'calibration']}
    for section, title, value in [
        ('measurements', 'Derived vessel measurements', measurements),
        ('candidates', 'Model candidates (not confirmed disease)', [
            {key: candidate.get(key, 'Unavailable') for key in ['candidate_id', 'model_score',
             'bbox_prepared_xyxy', 'bbox_source_xyxy', 'association_status', 'coordinate_warning']}
            for candidate in (snapshot['analysis'].get('structured_result') or {}).get('candidates', [])]),
        ('review', 'Run-linked human assessment', snapshot.get('human_review') or 'No human assessment linked to this run'),
    ]:
        if section in snapshot['sections']:
            paragraph(title, 'Heading2')
            if isinstance(value, dict):
                for key, item in value.items():
                    paragraph(f"{key.replace('_', ' ').capitalize()}: {'Unavailable' if item is None else item}")
            elif isinstance(value, list):
                if not value:
                    paragraph('No localized candidates recorded. This does not establish absence of disease.')
                for item in value:
                    paragraph(json.dumps(item, ensure_ascii=False))
            else:
                paragraph(value)
    paragraph('Warnings, missing stages and limitations', 'Heading2')
    for warning in snapshot['limitations']:
        paragraph(warning)
    for flag in vessel.get('quality_flags', []):
        paragraph(flag.get('message', str(flag)))
    structured = snapshot['analysis'].get('structured_result') or {}
    for section in structured.get('explanation', {}).get('sections', []):
        paragraph(section['title'], 'Heading3')
        paragraph(section['text'])
    if 'appendix' in snapshot['sections']:
        paragraph('Technical appendix: recorded evaluation references', 'Heading2')
        paragraph(json.dumps(snapshot['analysis'].get('validation', {}), ensure_ascii=False, indent=2))
    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(42, 23, f"Research only · {snapshot['report_id']} · Page {doc.page}")
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
