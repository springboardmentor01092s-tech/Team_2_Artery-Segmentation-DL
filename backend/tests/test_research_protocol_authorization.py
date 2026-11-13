from uuid import uuid4
from fastapi.testclient import TestClient
from app import main
from test_rbac_system import make_user


def test_explicit_authorization_is_audited_and_role_scoped():
    with TestClient(main.app) as client:
        _,owner=make_user(f'protocol-owner-{uuid4().hex}@example.org','researcher')
        _,viewer=make_user(f'protocol-viewer-{uuid4().hex}@example.org','viewer')
        payload=dict(protocol_id='COROVISION_XCA_RESEARCH_5CLASS',protocol_version='1.0.0',
            research_mode_only=True,decision='authorize')
        assert client.post('/api/research/severity-protocol',json=payload).status_code==401
        assert client.post('/api/research/severity-protocol',headers=viewer,json=payload).status_code==403
        authorized=client.post('/api/research/severity-protocol',headers=owner,json=payload)
        assert authorized.status_code==200
        assert authorized.json()['status']=='researcher_authorized'
        assert authorized.json()['clinical_validated'] is False
        assert client.get('/api/research/severity-protocol',headers=owner).json()==authorized.json()
        assert client.post('/api/research/severity-protocol',headers=owner,json={**payload,'protocol_version':'unknown'}).status_code==422
        inactive=client.post('/api/research/severity-protocol',headers=owner,json={**payload,'decision':'deactivate'})
        assert inactive.json()['status']=='inactive'
        informed=client.post('/api/research/severity-protocol',headers=owner,json={**payload,'protocol_id':'COROVISION_CADRADS_INFORMED_XCA'})
        assert informed.status_code==200
        assert informed.json()['boundaries']['Minimal']=='(0,25)'
        assert informed.json()['clinical_validated'] is False
        assert informed.json()['reference'].startswith('https://www.jacc.org/')
        client.post('/api/research/severity-protocol',headers=owner,json={**payload,'decision':'deactivate'})
