from io import BytesIO
import json
import os
from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import main,task_models,task_inference
from test_rbac_system import make_user


def test_registry_is_task_specific_and_keeps_exclusions():
    rows=task_models.catalog()
    assert len(rows)==12
    assert [r['id'] for r in rows if r['state']=='excluded_by_user']==['hepatic_vessels','hepatic_tumours']
    assert all(not row['clinical_validated'] for row in rows)
    assert task_models.SPECS['imagecasx']['sha256']!='858ab22c82e36258589f3c4d9056f380dfe9a5623a823bd3876deab96051b142'
    assert task_models.SPECS['cadica_localization']['sha256']==task_models.SPECS['cadica_grade_aware']['sha256']
    assert task_models.SPECS['aorta_aligned']['anatomy']=='aorta'


def test_checkpoint_checksum_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setenv('COROVISION_TASK_MODELS',str(tmp_path))
    (tmp_path/'cadica.pt').write_bytes(b'not registered weights')
    assert not task_models.installed('cadica_localization')
    assert not task_models.installed('archive_lesions')


def test_authenticated_persistence_case_identity_and_artifacts(monkeypatch):
    monkeypatch.setattr(main,'models_ready',lambda:True)
    monkeypatch.setattr(task_inference,'installed',lambda identity:True)
    def fixture(identity,source,output):
        output.mkdir();Image.open(source).save(output/'overlay.png')
        return dict(fixture_only=True,records=[],checkpoint_sha256=task_models.SPECS[identity]['sha256'])
    monkeypatch.setattr(task_inference,'run_image',fixture)
    with TestClient(app) as client:
        _,owner=make_user(f'tasks-{uuid4().hex}@example.org','researcher')
        _,other=make_user(f'other-{uuid4().hex}@example.org','researcher')
        _,viewer=make_user(f'view-{uuid4().hex}@example.org','viewer')
        case=client.post('/api/cases',headers=owner,json={'case_code':'TASK-'+uuid4().hex[:8]}).json()
        raw=BytesIO();Image.fromarray(np.tile(np.arange(512,dtype=np.uint8),(512,1))).save(raw,format='PNG')
        upload=client.post(f"/api/cases/{case['id']}/images",headers=owner,files={'file':('fixture.png',raw.getvalue(),'image/png')})
        assert upload.status_code==201,upload.text
        image=upload.json();url=f"/api/cases/{case['id']}/task-analyses"
        body=dict(image_id=image['id'],task_id='cadica_localization',research_confirmed=True)
        assert client.post(url,headers=other,json=body).status_code==404
        assert client.post(url,headers=viewer,json=body).status_code==403
        assert client.post(url,headers=owner,json=dict(body,task_id='hepatic_vessels')).status_code==422
        response=client.post(url,headers=owner,json=body)
        assert response.status_code==202,response.text
        rows=client.get(url,headers=owner).json();assert rows[0]['status']=='completed'
        assert rows[0]['image_id']==image['id'] and rows[0]['case_id']==case['id']
        overlay=rows[0]['artifacts']['overlay.png']
        assert client.get(overlay,headers=owner).status_code==200
        assert client.get(overlay,headers=other).status_code==404
        assert client.get(url,headers=owner).json()==rows
        result=client.get(rows[0]['artifacts']['result.json'],headers=owner).json()
        assert result['input_sha256']==rows[0]['input_sha256'] and result['fixture_only']
        assert client.get('/api/task-models').status_code==401
        assert client.get('/api/task-models',headers=viewer).status_code==403


def test_volume_selection_enforces_anatomy_and_persists_model(tmp_path,monkeypatch):
    import nibabel as nib
    from app import volume_inference
    monkeypatch.setattr(task_models,'installed',lambda identity:True)
    def fixture(source,output,model_key='imagecas'):
        output.mkdir();(output/'overlay_0.png').write_bytes(b'unit-fixture')
        return dict(model_id=model_key,clinical_validated=False)
    monkeypatch.setattr(volume_inference,'run_inference',fixture)
    image=nib.Nifti1Image(np.zeros((4,4,4),dtype=np.float32),np.eye(4));image.header.set_xyzt_units('mm')
    path=tmp_path/'fixture.nii.gz';nib.save(image,path)
    with TestClient(app) as client:
        _,owner=make_user(f'volume-select-{uuid4().hex}@example.org','researcher')
        coronary=client.post('/api/cases',headers=owner,json=dict(case_code='C-'+uuid4().hex[:8],modality='CTA',anatomy='coronary',intended_task='volume_preparation')).json()
        aorta=client.post('/api/cases',headers=owner,json=dict(case_code='A-'+uuid4().hex[:8],modality='CT',anatomy='aorta',intended_task='volume_preparation')).json()
        confirms=dict(hu_confirmed='true',research_confirmed='true',model_key='aorta_aligned')
        files={'file':('fixture.nii.gz',path.read_bytes(),'application/gzip')}
        assert client.post(f"/api/cases/{coronary['id']}/volumes/analyses",headers=owner,data=confirms,files=files).status_code==422
        url=f"/api/cases/{aorta['id']}/volumes/analyses"
        response=client.post(url,headers=owner,data=confirms,files=files)
        assert response.status_code==202,response.text
        rows=client.get(url,headers=owner).json()
        assert rows[0]['status']=='completed' and rows[0]['model_key']=='aorta_aligned'
        assert rows[0]['result']['model_id']=='aorta_aligned'
        assert client.post(url,headers=owner,data=dict(confirms,model_key='imagecasx'),files=files).status_code==422


@pytest.mark.skipif(os.getenv('CV_VERIFY_TASK_MODELS')!='1',reason='Opt-in real checkpoint integration smoke, no benchmark')
def test_all_additional_2d_checkpoints_execute(tmp_path):
    source=Path(os.environ['CV_TASK_IMAGE'])
    for identity in ['dca_vessels','arcade_anatomical_instances','cadica_localization','cadica_grade_aware','archive_lesions']:
        result=task_models.run_image(identity,source,tmp_path/identity)
        assert result['checkpoint_sha256']==task_models.SPECS[identity]['sha256']
        assert result['reference_metrics'] is None and result['clinical_validated'] is False
        assert (tmp_path/identity/'overlay.png').is_file()
        with Image.open(tmp_path/identity/'overlay.png') as image:assert image.size==(512,512)


@pytest.mark.skipif(os.getenv('CV_VERIFY_TASK_MODELS')!='1',reason='Opt-in genuine 3D checkpoint smoke on synthetic nonmedical volume')
def test_original_3d_checkpoints_execute_without_substitution(tmp_path):
    import nibabel as nib
    from app import volume_inference
    data=np.linspace(-200,800,16**3,dtype=np.float32).reshape(16,16,16)
    image=nib.Nifti1Image(data,np.eye(4));image.header.set_xyzt_units('mm')
    source=tmp_path/'synthetic.nii.gz';nib.save(image,source)
    for identity in ['imagecasx','aorta_aligned']:
        result=volume_inference.run_inference(source,tmp_path/identity,identity)
        assert result['checkpoint_sha256']==task_models.SPECS[identity]['sha256']
        assert result['anatomy']==task_models.SPECS[identity]['anatomy']
        restored=nib.load(tmp_path/identity/'mask_source.nii.gz')
        assert restored.shape==data.shape and np.array_equal(restored.affine,image.affine)
