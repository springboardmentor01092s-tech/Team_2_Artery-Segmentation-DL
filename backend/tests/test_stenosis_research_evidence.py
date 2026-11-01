"""Saved-metadata/API tests only; never load models or medical images."""
import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from app import research_progress as progress
from test_rbac_system import make_user


def install_result(monkeypatch, tmp_path):
    monkeypatch.setattr(progress, 'APP_ROOT', tmp_path)
    monkeypatch.setenv('COROVISION_RESEARCH_ROOT', str(tmp_path))
    source = Path(__file__).parent / 'fixtures/stenosis_threshold_run364196526.json'
    path = progress.evidence_paths()['stenosis-threshold-result'][1]
    path.parent.mkdir(parents=True)
    path.write_bytes(source.read_bytes())
    return path


def test_verified_rejection_is_visible_without_inventing_gain(monkeypatch, tmp_path):
    install_result(monkeypatch, tmp_path)
    result = progress.snapshot()
    row = next(r for r in result['experiments'] if r['id'] == 'stenosis-threshold-364196526')
    assert row['status'] == 'rejected_baseline_retained'
    assert row['metric'] == 'Instance F1 at IoU 0.5'
    assert row['count_unit'] == 'instances'
    assert row['delta'] < 0 and row['candidate_fp'] == 492
    assert result['summary']['measured_gains'] == 0
    assert result['telemetry']['confirmed_running_jobs'] is None


def test_tampered_saved_result_is_omitted_and_not_downloadable(monkeypatch, tmp_path):
    path = install_result(monkeypatch, tmp_path)
    changed = json.loads(path.read_text())
    changed['candidate_instance_f1'] = 0.99
    path.write_text(json.dumps(changed))
    result = progress.snapshot()
    assert not result['experiments']
    assert any('Stenosis comparison hash mismatch' in warning for warning in result['warnings'])
    with TestClient(app) as client:
        _, headers = make_user(f'stenosis-tamper-{uuid4().hex}@example.org', 'researcher')
        assert client.get('/api/research-progress/evidence/stenosis-threshold-result', headers=headers).status_code == 404


def test_verified_evidence_requires_research_role(monkeypatch, tmp_path):
    install_result(monkeypatch, tmp_path)
    with TestClient(app) as client:
        url = '/api/research-progress/evidence/stenosis-threshold-result'
        assert client.get(url).status_code == 401
        _, headers = make_user(f'stenosis-proof-{uuid4().hex}@example.org', 'researcher')
        response = client.get(url, headers=headers)
        assert response.status_code == 200 and response.json()['run_id'] == 364196526
        assert response.headers['x-content-type-options'] == 'nosniff'
        _, viewer = make_user(f'stenosis-viewer-{uuid4().hex}@example.org', 'viewer')
        assert client.get(url, headers=viewer).status_code == 403
