import json
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from app import research_progress as progress
from test_rbac_system import make_user


def isolate(monkeypatch,tmp_path):
    monkeypatch.setattr(progress,'APP_ROOT',tmp_path)
    monkeypatch.setenv('COROVISION_RESEARCH_ROOT',str(tmp_path))


def test_missing_evidence_never_invents_progress(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    result=progress.snapshot()
    assert result['summary']['measured_gains']==0
    assert result['summary']['framework_tests'] is None
    assert result['telemetry']['confirmed_running_jobs'] is None
    assert not result['tasks'] and not result['activity']
    assert all(not row['available'] for row in result['evidence'])
    assert result['task_proof']==[]


def test_kaggle_result_tampering_is_not_imported(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    path=progress.evidence_paths()['artery-kaggle-result'][1]
    path.parent.mkdir(parents=True)
    path.write_text('{"decision":"candidate_requires_independent_review"}')
    result=progress.snapshot()
    assert not result['experiments'] and result['summary']['measured_gains']==0
    assert any('hash mismatch' in warning for warning in result['warnings'])


def test_task_proof_requires_allowlisted_available_evidence(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    paths=progress.evidence_paths()
    path=paths['task-proof'][1];path.parent.mkdir(parents=True)
    rows=[dict(id='one',title='Masks',status='software_verified',evidence_id='task-verification'),
          dict(id='two',title='Severity',status='blocked'),
          dict(id='three',title='Fake completion',status='complete'),
          dict(id='one',title='Duplicate',status='blocked')]
    path.write_text(json.dumps(dict(schema_version=1,tasks=rows)))
    result=progress.snapshot()['task_proof']
    assert len(result)==2 and result[0]['status']=='verification_required'
    paths['task-verification'][1].write_text('Dated software verification only')
    assert progress.snapshot()['task_proof'][0]['status']=='software_verified'
    rows[0]['evidence_id']=['invalid']
    path.write_text(json.dumps(dict(schema_version=1,tasks=rows)))
    assert progress.snapshot()['task_proof'][0]['status']=='verification_required'
    path.write_text(json.dumps(dict(schema_version=1,tasks=None)))
    assert progress.snapshot()['task_proof']==[]


def test_regression_and_corrupt_inventory(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    paths=progress.evidence_paths()
    path=paths['pilot-result'][1];path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'baseline':{'mean_dice':.83,'fn':10,'fp':12},'candidate':{'mean_dice':.82,'fn':15,'fp':8},'decision':'rejected_baseline_retained'}))
    inventory=paths['framework-inventory'][1];inventory.parent.mkdir(parents=True)
    inventory.write_text('[null, 2]')
    result=progress.snapshot()
    assert result['summary']['recorded_experiments']==1
    assert result['summary']['measured_gains']==0
    assert result['experiments'][0]['delta']<0
    assert result['experiments'][0]['status']=='rejected_baseline_retained'
    inventory.write_text('{broken')
    assert progress.snapshot()['warnings']


def test_symlink_outside_root_is_not_evidence(monkeypatch,tmp_path):
    root=tmp_path/'workspace';root.mkdir();isolate(monkeypatch,root)
    secret=tmp_path/'outside.md';secret.write_text('not permitted')
    path=progress.evidence_paths()['framework-status'][1];path.parent.mkdir(parents=True)
    path.symlink_to(secret)
    assert not progress.safe_file(path,root)
    assert not next(e for e in progress.snapshot()['evidence'] if e['id']=='framework-status')['available']


def test_activity_rejects_running_and_invalid_entries(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    journal=tmp_path/'reports/research_progress/activity.jsonl';journal.parent.mkdir(parents=True)
    event={'id':'one','title':'Recorded action','detail':'Evidence review','status':'completed','recorded_at':'2026-10-26T10:00:00+00:00','evidence_id':'framework-status'}
    journal.write_text('\n'.join([json.dumps(event),json.dumps(dict(event,status='running')),'null','broken']))
    assert len(progress.snapshot()['activity'])==1


def test_authenticated_roles_and_evidence_redaction(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    path=progress.evidence_paths()['framework-status'][1];path.parent.mkdir(parents=True)
    path.write_text(f'**40 tests passed**\n{tmp_path}/private')
    with TestClient(app) as client:
        assert client.get('/api/research-progress').status_code==401
        for role in ('admin','researcher','ml_engineer'):
            _,headers=make_user(f'progress-{role}-{uuid4().hex}@example.org',role)
            assert client.get('/api/research-progress',headers=headers).json()['summary']['framework_tests']==40
            response=client.get('/api/research-progress/evidence/framework-status',headers=headers)
            assert response.status_code==200 and str(tmp_path) not in response.text
            assert response.headers['x-content-type-options']=='nosniff'
            assert client.get('/api/research-progress/evidence/unknown',headers=headers).status_code==404
        for role in ('viewer','doctor','clinician','technician'):
            _,headers=make_user(f'progress-{role}-{uuid4().hex}@example.org',role)
            assert client.get('/api/research-progress',headers=headers).status_code==403
            assert client.get('/api/research-progress/evidence/framework-status',headers=headers).status_code==403


def test_telemetry_requires_fresh_heartbeat_and_alive_process(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    path=tmp_path/'reports/research_live/state.json';path.parent.mkdir(parents=True)
    row=dict(job_id='a'*32,state='running',pid=os.getpid(),heartbeat_at=datetime.now(timezone.utc).isoformat(),
        title='Fixture job',completed_units=10,total_units=20)
    path.write_text(json.dumps(row))
    live=progress.snapshot()['telemetry']
    assert live['state']=='running' and live['confirmed_running_jobs']==1 and live['completed_units']==10
    row['heartbeat_at']=(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat()
    path.write_text(json.dumps(row))
    assert progress.snapshot()['telemetry']['state']=='stale'
    row['state']='completed';path.write_text(json.dumps(row))
    assert progress.snapshot()['telemetry']['confirmed_running_jobs']==0


def test_job_result_download_stays_inside_allowlisted_root(monkeypatch,tmp_path):
    isolate(monkeypatch,tmp_path)
    identity='b'*32;path=tmp_path/'reports/research_live/jobs'/identity/'result.json'
    path.parent.mkdir(parents=True);path.write_text('{"test_fixture":true}')
    with TestClient(app) as client:
        _,headers=make_user(f'job-{uuid4().hex}@example.org','researcher')
        assert client.get('/api/research-progress/evidence/job-'+identity,headers=headers).json()['test_fixture']
        assert client.get('/api/research-progress/evidence/job-not-a-uuid',headers=headers).status_code==404
