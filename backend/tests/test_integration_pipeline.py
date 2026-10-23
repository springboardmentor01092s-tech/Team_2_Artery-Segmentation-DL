from io import BytesIO
import json
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app import main
from app.analysis_result import build_result, candidate_coordinates
from app.database import SessionLocal
from app.inference_jobs import InferenceWorker
from app.models import AnalysisJob, AnalysisEvent, Image as ImageRecord, User
from test_rbac_system import make_user
from PIL import Image


def inputs(client):
    suffix = uuid4().hex
    account, owner = make_user(f'pipeline-{suffix}@example.org', 'researcher')
    _, outsider = make_user(f'other-{suffix}@example.org', 'researcher')
    case = client.post('/api/cases', headers=owner, json={'case_code': 'SYNTHETIC-'+suffix}).json()
    stream = BytesIO()
    Image.new('RGB', (512, 512), (128, 128, 128)).save(stream, format='PNG')
    uploaded = client.post(f"/api/cases/{case['id']}/images", headers=owner,
                           files={'file': ('synthetic.png', stream.getvalue(), 'image/png')})
    assert uploaded.status_code == 201
    return account, owner, outsider, uploaded.json()['id']


def fake_analysis(path, spacing):
    # Synthetic adapter output verifies pipeline behavior, not model performance.
    return (Path(path).read_bytes(), 0, 0, {'quality_flags': [{'code': 'empty_prediction', 'severity': 'warning', 'message': 'Empty mask'}]},
            None, None, None, None, {'calibration': 'uncalibrated_raw_scores', 'instance_detections': []}, None)


def test_jobs_idempotency_saved_explanation_history_and_access(monkeypatch):
    monkeypatch.setattr(main, 'models_ready', lambda: True)
    monkeypatch.setattr(main, 'analyze', fake_analysis)
    with TestClient(main.app) as client:
        _, owner, outsider, identity = inputs(client)
        url = f'/api/images/{identity}/analysis/jobs'
        key = {'idempotency_key': uuid4().hex}
        first = client.post(url, headers=owner, json=key)
        assert first.status_code == 202 and first.json()['status'] == 'pending'
        job_id = first.json()['id']
        assert client.post(url, headers=owner, json=key).json()['id'] == job_id
        assert client.post(url, headers=owner, json={'idempotency_key': uuid4().hex}).json()['id'] == job_id
        assert client.get(f'/api/analysis/jobs/{job_id}', headers=outsider).status_code == 404
        assert client.post(url, headers=outsider, json=key).status_code == 404
        assert client.post(f'/api/images/{identity}/analyze', headers=owner).status_code == 409
        worker = InferenceWorker(main.execute_analysis_job)
        assert worker.tick()
        job = client.get(f'/api/analysis/jobs/{job_id}', headers=owner).json()
        assert job['status'] == 'completed' and job['progress'] == 100
        result = client.get(job['result_url'], headers=owner).json()
        structured = result['structured_result']
        assert structured['job_id'] == job_id and structured['result_id'] == result['id']
        assert structured['severity']['status'] == 'insufficient_evidence'
        assert structured['severity']['narrowing_percent'] is None
        assert structured['measurements']['vessel_analysis'] is None
        assert structured['stages']['vessel_analysis']['status'] == 'skipped'
        assert 'healthy case' in structured['explanation']['sections'][3]['text']
        assert client.get(job['result_url'], headers=outsider).status_code == 404
        assert client.get(result['overlay_url'], headers=outsider).status_code == 404
        for section in structured['explanation']['sections']:
            for reference in section['source_refs']:
                value = structured
                for part in reference.split('.'):
                    value = value[part]
        assert client.post(url, headers=owner, json=key).json()['id'] == job_id
        second = client.post(url, headers=owner, json={'idempotency_key': uuid4().hex}).json()
        assert second['id'] != job_id
        assert worker.tick()
        assert client.get(job['result_url'], headers=owner).json() == result
        history = client.get(f'/api/images/{identity}/analyses', headers=owner).json()
        assert len(history) == 2
    # Restart does not fabricate another historical event for the latest run.
    with TestClient(main.app) as client:
        assert len(client.get(f'/api/images/{identity}/analyses', headers=owner).json()) == 2


@pytest.mark.parametrize('failure', ['runtime', 'revoked', 'input_changed', 'model_changed'])
def test_job_failures_never_produce_completed_output(monkeypatch, failure):
    monkeypatch.setattr(main, 'models_ready', lambda: True)
    with TestClient(main.app) as client:
        account, owner, _, identity = inputs(client)
        job = client.post(f'/api/images/{identity}/analysis/jobs', headers=owner,
                          json={'idempotency_key': uuid4().hex}).json()
        if failure == 'revoked':
            with SessionLocal() as db:
                db.get(User, account['id']).status = 'disabled'
                db.commit()
        elif failure == 'input_changed':
            with SessionLocal() as db:
                Path(db.get(ImageRecord, identity).preview_path).write_bytes(b'tampered')
        elif failure == 'model_changed':
            monkeypatch.setattr(main, 'model_version', lambda: 'different-version')
        else:
            def fail(*args):
                raise RuntimeError('private-path-or-sensitive-internal-error')
            monkeypatch.setattr(main, 'analyze', fail)
        InferenceWorker(main.execute_analysis_job).tick()
        with SessionLocal() as db:
            saved = db.get(AnalysisJob, job['id'])
            assert saved.status == 'failed' and saved.active_image_id is None
            assert 'private-path' not in saved.error_detail
            assert saved.result_event_id is None
            assert db.scalar(select(AnalysisEvent).where(AnalysisEvent.image_id == identity)) is None


def test_interrupted_worker_requires_explicit_new_run(monkeypatch):
    monkeypatch.setattr(main, 'models_ready', lambda: True)
    with TestClient(main.app) as client:
        _, owner, _, identity = inputs(client)
        job = client.post(f'/api/images/{identity}/analysis/jobs', headers=owner,
                          json={'idempotency_key': uuid4().hex}).json()
        with SessionLocal() as db:
            db.get(AnalysisJob, job['id']).status = 'processing'
            db.commit()
        worker = InferenceWorker(main.execute_analysis_job)
        worker.start()
        worker.close()
        saved = client.get(job['status_url'], headers=owner).json()
        assert saved['status'] == 'failed' and saved['error_code'] == 'worker_interrupted'
        assert client.get(f"/api/analysis/jobs/{job['id']}/result", headers=owner).status_code == 409


def test_candidate_mapping_padding_roi_and_missing_geometry():
    geometry = dict(padding_left_top_xy=[0, 128], content_size_xy=[512, 256],
                    source_pixels_per_content_pixel_xy=[2, 2], source_roi_origin_xy=[10, 20])
    row = candidate_coordinates({'bbox_prepared_xyxy': [5, 130, 15, 140]}, geometry, 1100, 600)
    assert row['bbox_source_xyxy'] == [20, 24, 40, 44]
    outside = candidate_coordinates({'bbox_prepared_xyxy': [5, 0, 15, 10]}, geometry, 1100, 600)
    assert outside['bbox_source_xyxy'] is None and outside['coordinate_warning']
    clipped = candidate_coordinates({'bbox_prepared_xyxy': [5, 120, 15, 140]}, geometry, 1100, 600)
    assert clipped['bbox_source_xyxy'] == [20, 20, 40, 44] and clipped['coordinate_warning']
    assert candidate_coordinates({}, None, 10, 10)['bbox_source_xyxy'] is None


def test_nonfinite_measurements_rejected_and_no_severity_from_global_diameter():
    image = SimpleNamespace(id='asset', width=512, height=512, source_sha256=None,
                            processed_sha256=None, preprocessing_config_json='{}')
    arguments = dict(event_id='event', job_id=None, image=image, case=SimpleNamespace(id='case', modality='XCA', anatomy='coronary'),
                     version='synthetic', scores={}, artery_pixels=10, stenosis_pixels=2, evidence={}, artifacts={}, timestamp='2026-10-23')
    result = build_result(**arguments, vessel={'mean_diameter': 10, 'minimum_diameter': 1, 'diameter_unit': 'mm'})
    assert result['severity']['narrowing_percent'] is None
    with pytest.raises(ValueError):
        build_result(**arguments, vessel={'mean_diameter': float('nan')})
