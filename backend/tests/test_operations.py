import json
import logging
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from app import main
from app.operations import validate_deployment_environment
from test_rbac_system import make_user


def test_operations_permissions_privacy_headers_and_readiness(monkeypatch, caplog):
    monkeypatch.setattr(main, 'models_ready', lambda: True)
    with TestClient(main.app) as client:
        with caplog.at_level(logging.INFO, logger='corovision.operations'):
            response = client.get('/api/health/live?token=PRIVATE_SENTINEL', headers={'X-Request-ID': 'PRIVATE_SENTINEL'})
        assert response.status_code == 200
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['Cache-Control'] == 'no-store'
        assert response.headers['X-Request-ID'] != 'PRIVATE_SENTINEL'
        entries = [json.loads(r.message) for r in caplog.records if r.name == 'corovision.operations']
        assert entries and all('PRIVATE_SENTINEL' not in json.dumps(row) for row in entries)
        assert client.get('/api/health/ready').status_code == 200
        monkeypatch.setattr(main, 'models_ready', lambda: False)
        assert client.get('/api/health/ready').status_code == 503
        assert client.get('/api/admin/operations').status_code == 401
        suffix = uuid4().hex
        _, viewer = make_user(f'ops-viewer-{suffix}@example.org', 'viewer')
        _, admin = make_user(f'ops-admin-{suffix}@example.org', 'admin')
        for path in ['/api/admin/operations', '/api/admin/metrics']:
            assert client.get(path, headers=viewer).status_code == 403
            assert client.get(path, headers=admin).status_code == 200
        snapshot = client.get('/api/admin/operations', headers=admin).json()
        assert snapshot['workers_supported'] == 1
        assert snapshot['training_dispatch'] == 'not_connected'
        assert snapshot['clinical_validation'] is False
        assert 'corovision_http_requests_total' in client.get('/api/admin/metrics', headers=admin).text


def test_production_rejects_unsafe_defaults(monkeypatch):
    monkeypatch.setenv('COROVISION_ENV', 'production')
    monkeypatch.setenv('JWT_SECRET', 'short')
    with pytest.raises(RuntimeError):
        validate_deployment_environment()
    monkeypatch.setenv('JWT_SECRET', 'a' * 64)
    monkeypatch.setenv('CV_LOCAL_DEMO_SESSIONS', '1')
    with pytest.raises(RuntimeError):
        validate_deployment_environment()
    monkeypatch.setenv('CV_LOCAL_DEMO_SESSIONS', '0')
    monkeypatch.setenv('CV_LOCAL_DEMO_SHARING', '0')
    validate_deployment_environment()
