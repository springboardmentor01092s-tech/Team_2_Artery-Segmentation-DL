import csv
from io import StringIO
from app.research_reporting import tabular, stenosis_count_text


def test_missing_mask_export_does_not_claim_zero():
    result = dict(id='synthetic-run', model_version='synthetic', artery_pixels=0,
                  stenosis_pixels=0, model_scores={'pixel_counts_unavailable': True})
    snapshot = dict(report_id='synthetic-report', version=1, generated_at='2026-11-05',
                    case={'id':'synthetic-case', 'case_code':'SYNTHETIC'}, image={'id':'synthetic-image'},
                    analysis=result, sections=[])
    row = next(csv.DictReader(StringIO(tabular(snapshot))))
    assert row['stenosis_pixels'] == 'Unavailable'
    assert row['stenosis_mask_status'] == 'not_saved'
    assert stenosis_count_text(result) == 'Not saved'
    result['model_scores']['pixel_counts_unavailable'] = False
    row = next(csv.DictReader(StringIO(tabular(snapshot))))
    assert row['stenosis_pixels'] == '0'
    assert stenosis_count_text(result) == '0 px'


def test_skipped_pdf_text_and_missing_count_are_explicit():
    result = {'stenosis_pixels':0, 'structured_result':{'stages':{'stenosis_detection':{'status':'skipped'}}}}
    assert stenosis_count_text(result) == 'Not assessed'
    assert stenosis_count_text({}) == 'Unavailable'
