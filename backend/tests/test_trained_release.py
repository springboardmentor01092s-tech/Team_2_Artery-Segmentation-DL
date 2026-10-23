import hashlib
import json
import numpy as np
import pytest
import os
from PIL import Image
from app import analysis_service, trained_release


def test_configured_invalid_release_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv('COROVISION_MODEL_PROVIDER', 'preserved')
    monkeypatch.setenv('COROVISION_TRAINED_RELEASE', str(tmp_path))
    assert trained_release.configured()
    assert not analysis_service.models_ready()
    with pytest.raises(ValueError):
        trained_release.predict_masks(tmp_path/'missing.png')


def test_hash_verification_and_legacy_rollback(tmp_path, monkeypatch):
    monkeypatch.setenv('COROVISION_MODEL_PROVIDER', 'preserved')
    monkeypatch.setenv('COROVISION_TRAINED_RELEASE', str(tmp_path))
    specs=[]
    for name in ['artery.pt','stenosis.pt']:
        content=name.encode();(tmp_path/name).write_bytes(content)
        specs.append(dict(filename=name,sha256=hashlib.sha256(content).hexdigest(),task=name))
    monkeypatch.setitem(trained_release.RELEASE,'models',specs)
    monkeypatch.setattr(trained_release.importlib.util,'find_spec',lambda _:object())
    trained_release._verify.cache_clear()
    assert trained_release.ready()
    (tmp_path/'artery.pt').write_bytes(b'wrong-artifact')
    assert not trained_release.ready()
    monkeypatch.setenv('COROVISION_MODEL_PROVIDER','legacy')
    assert not trained_release.configured()


def test_adapter_keeps_masks_and_instance_semantics(tmp_path, monkeypatch):
    path=tmp_path/'prepared.png';Image.new('RGB',(512,512),(128,128,128)).save(path)
    artery=np.zeros((512,512),bool);artery[100:150,200:204]=True
    stenosis=np.zeros_like(artery);stenosis[110:115,200:204]=True
    monkeypatch.setattr(trained_release,'predict_masks',lambda _: (artery,stenosis,artery.astype('float32'),stenosis.astype('float32'),[dict(category_id=26,model_score=.4)]))
    result=trained_release.analyze(path)
    assert len(result)==10 and result[1:3]==(200,20)
    assert result[8]['instance_detections'][0]['category_id']==26
    assert result[4] is None and result[7] is None  # No invented attention/Grad-CAM layer.
    assert 'absence of disease' in result[8]['absence_interpretation']


@pytest.mark.skipif(os.environ.get('CV_TEST_REAL_TRAINED_RELEASE') != '1', reason='Opt-in installed-checkpoint integration test')
def test_real_case_upload_analysis_and_access_control(monkeypatch):
    from io import BytesIO
    from uuid import uuid4
    from fastapi.testclient import TestClient
    from app.main import app
    from test_rbac_system import make_user
    monkeypatch.setenv('COROVISION_MODEL_PROVIDER', 'preserved')
    assert trained_release.ready()
    with TestClient(app) as client:
        suffix=uuid4().hex[:10]
        _,owner=make_user(f'integration-{suffix}@example.org','researcher')
        _,outsider=make_user(f'outsider-{suffix}@example.org','researcher')
        status=client.get('/api/analysis/status',headers=owner)
        assert status.status_code==200 and status.json()['trained_release']['ready']
        evidence=status.json()['trained_release']['research_evidence']
        assert len(evidence['tasks'])==12 and sum(x['inference_connected'] for x in evidence['tasks'])==2
        assert len(evidence['calibration_studies'])==2
        case=client.post('/api/cases',headers=owner,json={'case_code':'SYNTHETIC-'+suffix})
        assert case.status_code==201
        image=BytesIO();Image.new('RGB',(512,512),(120,120,120)).save(image,format='PNG')
        upload=client.post('/api/cases/'+case.json()['id']+'/images',headers=owner,files={'file':('synthetic.png',image.getvalue(),'image/png')})
        assert upload.status_code==201
        identity=upload.json()['id'];url='/api/images/'+identity+'/analyze'
        assert client.post(url,headers=outsider).status_code==404
        result=client.post(url,headers=owner)
        assert result.status_code==200
        record=result.json()
        assert record['model_version']==trained_release.RELEASE['version']
        assert record['model_scores']['checkpoint_sha256']=={x['task']:x['sha256'] for x in trained_release.RELEASE['models']}
        assert client.get(record['overlay_url'],headers=owner).status_code==200
        assert client.get(record['centerline_url'],headers=owner).status_code==200
        assert client.get(record['overlay_url'],headers=outsider).status_code==404
        assert client.get('/api/images/'+identity+'/analyses',headers=owner).status_code==200
        # Real installed checkpoints through the actual background dispatcher.
        import time
        from app.inference_jobs import InferenceWorker
        from app.main import execute_analysis_job
        worker = InferenceWorker(execute_analysis_job)
        worker.start()
        try:
            job = client.post(f'/api/images/{identity}/analysis/jobs', headers=owner,
                              json={'idempotency_key': uuid4().hex})
            assert job.status_code == 202
            state = job.json()
            deadline = time.monotonic() + 40
            while state['status'] in {'pending', 'processing'} and time.monotonic() < deadline:
                time.sleep(.1)
                state = client.get(state['status_url'], headers=owner).json()
            assert state['status'] == 'completed'
            result = client.get(state['result_url'], headers=owner).json()['structured_result']
            assert result['models']['checkpoint_sha256'] == record['model_scores']['checkpoint_sha256']
            assert result['severity']['narrowing_percent'] is None
            assert result['input']['prepared_sha256']
            for name in ['artery_mask', 'stenosis_mask']:
                response = client.get(result['artifacts'][name], headers=owner)
                assert response.status_code == 200
                mask = np.array(Image.open(BytesIO(response.content)))
                assert mask.shape == (512, 512) and set(np.unique(mask)) <= {0, 255}
                assert client.get(result['artifacts'][name], headers=outsider).status_code == 404
            scores = client.get(result['artifacts']['raw_scores'], headers=owner)
            with np.load(BytesIO(scores.content), allow_pickle=False) as arrays:
                assert set(arrays.files) == {'artery', 'stenosis'}
                assert arrays['artery'].shape == (512, 512) and np.isfinite(arrays['artery']).all()
            for candidate in result['candidates']:
                assert len(candidate['bbox_prepared_xyxy']) == 4 and candidate['category_id'] == 26
            assert client.get(f'/api/images/{identity}/analyses', headers=owner).status_code == 200
        finally:
            worker.close()


@pytest.mark.parametrize('invalid', ['shape', 'nonfinite', 'range'])
def test_invalid_prediction_arrays_fail_closed(tmp_path, monkeypatch, invalid):
    shape = (10, 10) if invalid == 'shape' else (512, 512)
    mask = np.zeros(shape, dtype=bool)
    raw = np.zeros(shape, dtype=np.float32)
    if invalid == 'nonfinite':
        raw[0, 0] = np.nan
    if invalid == 'range':
        raw[0, 0] = 1.1
    monkeypatch.setattr(trained_release, 'predict_masks', lambda _: (mask, mask, raw, raw, []))
    with pytest.raises(ValueError):
        trained_release.analyze(tmp_path / 'not-read-by-mock.png')
