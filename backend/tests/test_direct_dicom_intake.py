"""Direct multipart transport contracts; reconstruction is tested separately."""
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4

from fastapi.testclient import TestClient
from app import main
from test_volume_inference import make_user


def test_direct_series_permissions_limits_and_reconstruction_handoff(monkeypatch):
    captured = {}

    def handoff(case_id, background, upload, hu, research, kind, model, user, db):
        captured['confirmations'] = (hu, research, kind)
        with ZipFile(BytesIO(upload.file.read())) as archive:
            captured['members'] = [archive.read(name) for name in archive.namelist()]
        return {'id': 'transport-test-only', 'status': 'queued'}

    monkeypatch.setattr(main, 'create_volume_analysis', handoff)
    with TestClient(main.app) as client:
        suffix = uuid4().hex
        _, owner = make_user(f'dicom-owner-{suffix}@example.org', 'researcher')
        _, outsider = make_user(f'dicom-other-{suffix}@example.org', 'researcher')
        _, viewer = make_user(f'dicom-viewer-{suffix}@example.org', 'viewer')
        case = client.post('/api/cases', headers=owner, json={
            'case_code': 'DIRECT-'+suffix, 'modality': 'CTA', 'anatomy': 'coronary',
            'intended_task': 'volume_preparation'}).json()
        url = f"/api/cases/{case['id']}/volumes/dicom-analyses"
        files = [('files', ('../one.dcm', b'first')), ('files', ('two.dcm', b'second'))]
        assert client.post(url, files=files).status_code == 401
        assert client.post(url, headers=viewer, files=files).status_code == 403
        assert client.post(url, headers=outsider, files=files).status_code == 404
        assert client.post(url, headers=owner, files=files[:1]).status_code == 422
        empty = [('files', ('one.dcm', b'')), files[1]]
        assert client.post(url, headers=owner, files=empty).status_code == 422
        result = client.post(url, headers=owner, files=files,
                             data={'hu_confirmed': 'true', 'research_confirmed': 'true'})
        assert result.status_code == 202, result.text
        assert captured['members'] == [b'first', b'second']
        assert captured['confirmations'] == (True, True, 'medical_study')
