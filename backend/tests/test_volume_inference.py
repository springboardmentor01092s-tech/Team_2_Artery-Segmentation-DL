"""3D geometry/contract/API checks. Synthetic inputs are not accuracy evidence."""
import json
import os
from uuid import uuid4

import nibabel as nib
import numpy as np
import pytest
from scipy.ndimage import zoom
from fastapi.testclient import TestClient
from app import main, volume_inference as volume
from test_rbac_system import make_user


def nifti(tmp_path):
    values = np.indices((16,18,20)).sum(0).astype(np.float32)*40-300
    affine = np.diag([-0.7,0.9,2.,1.]); affine[:3,3] = [50,-20,11]
    image = nib.Nifti1Image(values,affine)
    image.header.set_xyzt_units('mm')
    path = tmp_path/'synthetic.nii.gz'
    nib.save(image,path)
    return path


def test_source_preparation_parity_and_native_geometry(tmp_path):
    path = nifti(tmp_path)
    source, canonical, tensor, affine = volume.prepare_input(path)
    original = np.asarray(nib.as_closest_canonical(nib.load(path)).dataobj,dtype=np.float32)
    expected = ((zoom(np.clip(original,-200,800),np.array([128]*3)/original.shape,
                      order=1,prefilter=False)+200)/1000).astype(np.float16).astype(np.float32)
    np.testing.assert_array_equal(tensor,expected)
    assert tensor.shape == (128,128,128) and tensor.dtype == np.float32
    # First and last voxel centres agree after canonical-axis resize.
    np.testing.assert_allclose(affine@np.array([127,127,127,1]),
                               canonical.affine@np.array([*(np.array(canonical.shape)-1),1]))
    prediction = np.zeros((128,128,128),np.uint8); prediction[:64] = 1
    restored = volume.restore_mask(prediction,affine,source)
    assert restored.shape == source.shape
    np.testing.assert_allclose(restored.affine,source.affine)
    assert restored.header.get_xyzt_units()[0] == 'mm'
    assert set(np.unique(restored.dataobj)) <= {0,1}
    # X was flipped to RAS, then must be flipped back to source.
    assert np.asarray(restored.dataobj)[-1].all() and not np.asarray(restored.dataobj)[0].any()


def test_invalid_volume_and_checkpoint_rejected(tmp_path, monkeypatch):
    path = nifti(tmp_path)
    image = nib.load(path); image.header.set_xyzt_units('unknown'); nib.save(image,path)
    with pytest.raises(ValueError,match='millimetres'):
        volume.prepare_input(path)
    fake = tmp_path/'bad.pt'; fake.write_bytes(b'untrusted')
    monkeypatch.setenv('COROVISION_3D_CHECKPOINT',str(fake))
    with pytest.raises(ValueError,match='checksum'):
        volume.run_inference(path,tmp_path/'out')


def test_native_cta_header_above_old_limit_is_accepted_without_decoding(tmp_path, monkeypatch):
    path = tmp_path/'native-size.nii'
    header = nib.Nifti1Header()
    header.set_data_shape((512,512,321))
    header.set_data_dtype(np.int16)
    header.set_xyzt_units('mm')
    header.set_sform(np.diag([.5,.5,1.,1.]),code=1)
    header['vox_offset'] = 352
    with path.open('wb') as stream:
        header.write_to(stream)
        stream.write(bytes(4))
        stream.truncate(352+512*512*321*2)  # Sparse native-size fixture, not clinical data.
    def forbid_decode(*args, **kwargs):
        raise AssertionError('Header validation must not decode the volume')
    monkeypatch.setattr(nib.arrayproxy.ArrayProxy,'__array__',forbid_decode)
    assert volume.inspect_input(path).shape == (512,512,321)
    assert volume.MAX_VOXELS >= 512*512*321 > 32_000_000


def test_oversized_and_vector_headers_rejected_before_decode(tmp_path):
    path = tmp_path/'too-big.nii'
    header = nib.Nifti1Header()
    header.set_data_shape((600,600,300))
    header.set_xyzt_units('mm')
    header['vox_offset'] = 352
    path.write_bytes(header.binaryblock+bytes(4))
    with pytest.raises(ValueError,match='96 million'):
        volume.inspect_input(path)


def test_known_legacy_fixture_is_not_presented_as_medical_study():
    from app.models import VolumeAnalysis, now
    row = VolumeAnalysis(id='test',case_id='case',source_sha256=next(iter(volume.SYNTHETIC_FIXTURE_HASHES)),
                         input_kind='unspecified',created_at=now(),status='completed',result_json='{}')
    assert main.volume_run_out(row)['input_kind']=='synthetic_fixture'


def test_volume_job_case_permissions_history_and_artifact_isolation(tmp_path, monkeypatch):
    source = nifti(tmp_path)
    monkeypatch.setattr(volume,'checkpoint_path',lambda:source)
    def fake_inference(path, output):
        output.mkdir(parents=True)
        (output/'overlay_0.png').write_bytes(b'fake-test-preview')
        return {'model_id':'synthetic-test-stub', 'clinical_validated':False, 'severity':None}
    monkeypatch.setattr(volume,'run_inference',fake_inference)
    with TestClient(main.app) as client:
        suffix = uuid4().hex
        _, owner = make_user(f'volume-owner-{suffix}@example.org','researcher')
        _, outsider = make_user(f'volume-outsider-{suffix}@example.org','researcher')
        _, viewer = make_user(f'volume-viewer-{suffix}@example.org','viewer')
        case = client.post('/api/cases',headers=owner,json={'case_code':'VOL-'+suffix,'modality':'CTA','anatomy':'coronary','intended_task':'volume_preparation'}).json()
        base = f"/api/cases/{case['id']}/volumes/analyses"
        files = {'file':('synthetic.nii.gz',source.read_bytes(),'application/gzip')}
        confirms = {'hu_confirmed':'true','research_confirmed':'true'}
        assert client.post(base,headers=owner,files=files).status_code == 422
        assert client.post(base,headers=viewer,files=files,data=confirms).status_code == 403
        assert client.get(base,headers=outsider).status_code == 404
        response = client.post(base,headers=owner,files=files,data=confirms)
        assert response.status_code == 202, response.text
        assert response.json()['status'] == 'queued'
        rows = client.get(base,headers=owner).json()
        assert rows[0]['status'] == 'completed'
        assert rows[0]['created_at'].endswith('+00:00')
        assert rows[0]['result']['source_sha256'] == rows[0]['source_sha256']
        assert rows[0]['input_kind'] == 'medical_study'
        assert rows[0]['result']['model_id'] == 'synthetic-test-stub'
        url = rows[0]['artifacts']['overlay_0.png']
        assert client.get(url,headers=owner).content == b'fake-test-preview'
        assert client.get(url,headers=outsider).status_code == 404
        assert client.get(url.replace('overlay_0.png','source.nii.gz'),headers=owner).status_code == 404
        wrong = client.post('/api/cases',headers=owner,json={'case_code':'WRONG-'+suffix,'modality':'MRA','anatomy':'coronary','intended_task':'volume_preparation'}).json()
        assert client.post(f"/api/cases/{wrong['id']}/volumes/analyses",headers=owner,files=files,data=confirms).status_code == 422
        monkeypatch.setattr(volume,'MAX_UPLOAD_BYTES',1)
        assert client.post(base,headers=owner,files=files,data=confirms).status_code == 413


@pytest.mark.skipif(os.getenv('CV_TEST_REAL_3D') != '1',reason='Opt-in installed real 3D checkpoint execution')
def test_real_checkpoint_executes_and_persists_geometry(tmp_path):
    source = nifti(tmp_path)
    result = volume.run_inference(source,tmp_path/'outputs')
    assert result['checkpoint_sha256'] == volume.CHECKPOINT_SHA
    assert result['model_id'] == volume.MODEL_ID
    assert result['severity'] is None and result['clinical_validated'] is False
    restored = nib.load(tmp_path/'outputs/mask_source.nii.gz')
    np.testing.assert_allclose(restored.affine,nib.load(source).affine)
    assert restored.shape == (16,18,20)
    assert nib.load(tmp_path/'outputs/probability_coarse.nii.gz').shape == (128,128,128)
    assert all((tmp_path/'outputs'/f'overlay_{axis}.png').is_file() for axis in range(3))
    json.dumps(result,allow_nan=False)
