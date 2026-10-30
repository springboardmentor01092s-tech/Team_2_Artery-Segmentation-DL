"""Create one clearly synthetic research case and verify real local 3D API outputs.

This is execution/geometry acceptance, not medical or segmentation accuracy testing.
Uses existing private local demo credentials without printing or exporting them.
"""
import gzip
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

import httpx
import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    credentials = json.loads((ROOT/'backend/demo-credentials.json').read_text())
    account = next(item for item in credentials['accounts'] if item['email'] == 'researcher.demo@example.com')
    with TemporaryDirectory(prefix='corovision-synthetic-3d-') as temporary:
        source = Path(temporary)/'synthetic_geometry_cta.nii.gz'
        x,y,z = np.indices((24,28,32))
        values = (x*17+y*9+z*4-300).astype(np.float32)
        affine = np.diag([-.7,.9,1.5,1.]); affine[:3,3] = [20,-10,30]
        image = nib.Nifti1Image(values,affine); image.header.set_xyzt_units('mm'); nib.save(image,source)
        raw = source.read_bytes()
        with httpx.Client(base_url='http://127.0.0.1:8000',timeout=120) as client:
            login = client.post('/api/auth/login',json={'email':account['email'],'password':account['password']})
            login.raise_for_status()
            client.headers['Authorization'] = 'Bearer '+login.json()['access_token']
            response = client.post('/api/cases',json={'case_code':'SYNTHETIC-3D-CHECK-'+uuid4().hex[:6],
                'modality':'CTA','anatomy':'coronary','intended_task':'volume_preparation',
                'source_dataset':'Synthetic geometry acceptance fixture — not patient data'})
            response.raise_for_status(); case = response.json()
            base = f'/api/cases/{case["id"]}/volumes/analyses'
            response = client.post(base,files={'file':(source.name,raw,'application/gzip')},
                                   data={'hu_confirmed':'true','research_confirmed':'true','input_kind':'synthetic_fixture'})
            response.raise_for_status(); submitted = response.json()
            deadline = time.monotonic()+120
            while time.monotonic()<deadline:
                response = client.get(base); response.raise_for_status()
                row = next(item for item in response.json() if item['id'] == submitted['id'])
                if row['status'] in {'completed','failed'}:
                    break
                time.sleep(.5)
            if row['status'] != 'completed':
                raise RuntimeError('3D acceptance did not complete: '+row['status'])
            artifacts = {}
            for name,url in row['artifacts'].items():
                response = client.get(url); response.raise_for_status()
                artifacts[name] = {'bytes':len(response.content),'sha256':hashlib.sha256(response.content).hexdigest()}
                if name == 'mask_source.nii.gz':
                    mask = nib.Nifti1Image.from_bytes(gzip.decompress(response.content))
                    assert mask.shape == image.shape
                    np.testing.assert_allclose(mask.affine,image.affine)
                    assert set(np.unique(mask.dataobj)) <= {0,1}
                if name == 'probability_coarse.nii.gz':
                    probability = nib.Nifti1Image.from_bytes(gzip.decompress(response.content))
                    values = np.asarray(probability.dataobj)
                    assert values.shape == (128,128,128) and np.isfinite(values).all()
                    assert values.min() >= 0 and values.max() <= 1
            assert row['result']['severity'] is None and row['result']['clinical_validated'] is False
            receipt = {'fixture':'Synthetic HU-like gradient, not a medical study or accuracy benchmark',
                       'case_code':case['case_code'],'case_id':case['id'],'run_id':row['id'],
                       'status':row['status'],'source_sha256':row['source_sha256'],
                       'result':row['result'],'artifacts_verified':artifacts,
                       'source_grid_shape_and_affine_verified':True}
            (ROOT/'reports/volume_inference_receipt.json').write_text(json.dumps(receipt,indent=2))
            print(json.dumps({'case_code':case['case_code'],'status':row['status'],
                              'duration_seconds':row['result']['duration_seconds'],
                              'artifacts_verified':list(artifacts),'geometry_verified':True}))


if __name__ == '__main__':
    main()
