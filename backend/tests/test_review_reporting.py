"""Deterministic integration tests, not model accuracy measurements."""
from io import BytesIO
import csv
import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image
from app import main
from app.database import SessionLocal
from app.models import AnalysisEvent
from test_rbac_system import make_user


def test_review_run_binding_reports_exports_and_immutable_history(monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'models_ready', lambda: True)
    raw = BytesIO()
    Image.new('L', (512, 512), 128).save(raw, 'PNG')
    monkeypatch.setattr(main, 'analyze', lambda path, spacing=None: (
        raw.getvalue(), 123, 0, {'mean_diameter': None, 'centerline_length': 4, 'diameter_unit': 'px',
        'quality_flags': [{'code': 'test', 'severity': 'warning', 'message': 'Synthetic test evidence only'}]},
        None, None, None, None, {'calibration': 'unavailable'}, None))
    suffix = uuid4().hex
    with TestClient(main.app) as client:
        _, owner = make_user(f'report-owner-{suffix}@example.org', 'doctor')
        _, outsider = make_user(f'report-outsider-{suffix}@example.org', 'doctor')
        _, viewer = make_user(f'report-viewer-{suffix}@example.org', 'viewer')
        case = client.post('/api/cases', headers=owner, json={'case_code': 'REPORT-'+suffix}).json()
        case_id = case['id']
        base = f'/api/cases/{case_id}'
        im = client.post(base+'/images', headers=owner, files={'file': ('test.png', raw.getvalue(), 'image/png')}).json()
        analysis = client.post(f"/api/images/{im['id']}/analyze", headers=owner).json()
        assert 'id' in analysis, analysis
        event_id = analysis['id']
        panels_url = f"/api/images/{im['id']}/analyses/{event_id}/panels"
        manifest = client.get(panels_url, headers=owner).json()
        assert manifest['analysis_run_id'] == event_id
        assert manifest['model_version'] == analysis['model_version']
        assert len(manifest['panels']) == 7
        assert not next(p for p in manifest['panels'] if p['key'] == 'landmarks')['available']
        assert client.get(panels_url, headers=outsider).status_code == 404
        assert client.get(panels_url).status_code == 401
        assert client.get(panels_url+'/landmarks', headers=owner).status_code == 404
        assert client.get(panels_url+'/overlay', headers=owner).status_code == 200
        assert client.get(panels_url+'/unknown', headers=owner).status_code == 404
        evidence = {'image_id': im['id'], 'analysis_event_id': event_id}
        assert client.post(base+'/review', headers=owner, json={**evidence, 'decision': 'reviewed', 'stenosis_severity': 'insufficient_evidence'}).status_code == 422
        reviewed = client.post(base+'/review', headers=owner, json={**evidence, 'decision': 'reviewed', 'stenosis_severity': 'insufficient_evidence', 'notes': 'No calibrated reference diameter'})
        assert reviewed.status_code == 201, reviewed.text
        review = reviewed.json()['latest_review']
        assert review['analysis_event_id'] == event_id and review['reviewer_role'] == 'doctor'
        payload = {**evidence, 'sections': ['images', 'measurements', 'candidates', 'review']}
        response = client.post(base+'/research-reports', headers=owner, json=payload)
        assert response.status_code == 201, response.text
        snapshot = response.json()
        assert snapshot['image_panels'] == manifest['panels']
        assert snapshot['analysis']['id'] == event_id
        assert snapshot['human_review']['id'] == review['id']
        assert snapshot['analysis']['vessel_analysis']['mean_diameter'] is None
        path = base+'/research-reports/'+snapshot['report_id']
        assert client.get(path, headers=outsider).status_code == 404
        assert client.get(path).status_code == 401
        for format in ['json', 'csv', 'pdf']:
            export = client.get(path+'/export/'+format, headers=owner)
            assert export.status_code == 200, export.text[:300] if format != 'pdf' else export.status_code
            if format == 'json':
                assert export.json() == snapshot
            elif format == 'csv':
                row = next(csv.DictReader(export.text.splitlines()))
                assert row['analysis_run_id'] == event_id and row['artery_pixels'] == '123'
                assert row['mean_diameter'] == 'Unavailable'
            else:
                assert export.content.startswith(b'%PDF-')
                if main.os.getenv('CV_REPORT_TEST_PDF'):
                    Path(main.os.environ['CV_REPORT_TEST_PDF']).write_bytes(export.content)
        # Rerun and reassess: neither changes the old snapshot.
        newer = client.post(f"/api/images/{im['id']}/analyze", headers=owner).json()
        assert newer['id'] != event_id
        client.post(base+'/review', headers=owner, json={**evidence, 'decision': 'reviewed', 'notes': 'New human review'})
        assert client.get(path, headers=owner).json() == snapshot
        second = client.post(base+'/research-reports', headers=owner, json=payload).json()
        assert second['version'] == snapshot['version'] + 1
        assert second['human_review']['id'] != review['id']
        assert len(client.get(base+'/research-reports', headers=owner).json()) == 2
        # Different image/case cannot be paired with this event.
        other = client.post('/api/cases', headers=owner, json={'case_code': 'OTHER-'+suffix}).json()['id']
        assert client.post(f'/api/cases/{other}/research-reports', headers=owner, json=payload).status_code == 422
        assert client.post(f'/api/cases/{other}/review', headers=owner, json={**evidence, 'decision': 'reviewed'}).status_code == 422
        assert client.post(base+'/research-reports', headers=owner, json={**payload, 'image_id': 'missing'}).status_code == 422
        second_raw = BytesIO()
        Image.new('L', (512, 512), 129).save(second_raw, 'PNG')
        second_image = client.post(base+'/images', headers=owner, files={'file': ('other-image.png', second_raw.getvalue(), 'image/png')}).json()
        assert client.get(f"/api/images/{second_image['id']}/analyses", headers=owner).json() == []
        assert client.post(base+'/research-reports', headers=owner, json={**payload, 'image_id': second_image['id']}).status_code == 422
        assert client.get(f"/api/images/{second_image['id']}/analyses/{event_id}/panels", headers=owner).status_code == 404
        assert client.post(base+'/review', headers=owner, json={**evidence, 'image_id': second_image['id'], 'decision': 'reviewed'}).status_code == 422
        assert client.get(f"/api/images/{im['id']}/analysis", headers=owner).json()['id'] == newer['id']
        assert client.post(base+'/research-reports', headers=viewer, json=payload).status_code in {403, 404}
        # A broken artifact still leaves numeric evidence/report available and PDF explicit.
        with SessionLocal() as db:
            row = db.get(AnalysisEvent, event_id)
            row.overlay_path = str(tmp_path/'absent.png')
            db.commit()
        assert client.get(analysis['overlay_url'], headers=owner).status_code == 404
        assert client.get(path+'/export/pdf', headers=owner).status_code == 200


def test_csv_formula_protection_and_missing_values():
    from app.research_reporting import tabular
    snapshot = {'report_id': 'test', 'version': 1, 'generated_at': 'today', 'sections': [],
                'case': {'id': 'case', 'case_code': '=HYPERLINK("bad")'}, 'image': {'id': 'image'},
                'analysis': {'id': 'event', 'model_version': 'test', 'artery_pixels': 0, 'stenosis_pixels': 0}, 'human_review': None}
    row = next(csv.DictReader(tabular(snapshot).splitlines()))
    assert row['case_code'].startswith("'=")
    assert row['artery_pixels'] == '0'


def test_boundary_is_derived_without_changing_mask(tmp_path):
    from app.image_panels import boundary_png
    mask = Image.new('L', (12, 12))
    for x in range(3, 9):
        for y in range(3, 9):
            mask.putpixel((x, y), 255)
    source = tmp_path/'mask.png'
    mask.save(source)
    before = source.read_bytes()
    edge = Image.open(BytesIO(boundary_png(source)))
    assert edge.size == mask.size
    assert edge.getpixel((3, 3)) == 255
    assert edge.getpixel((5, 5)) == 0
    assert source.read_bytes() == before
