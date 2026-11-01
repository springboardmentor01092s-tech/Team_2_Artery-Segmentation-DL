"""Real public CTACardio acceptance, not model-accuracy or training evaluation.

Original is Slicer's hash-pinned testing data. NRRD is converted losslessly to
NIfTI with physical geometry preserved, no ROI/normalization/resampling. No
private user medical files are transmitted; all application work is localhost.
"""
import gzip
import hashlib
import json
from pathlib import Path
import time
from uuid import uuid4

import httpx
import nibabel as nib
import numpy as np
import SimpleITK as sitk

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'external_artifacts/public_cta_acceptance'
SHA = '3b0d4eb1a7d8ebb0c5a89cc0504640f76a030b4e869e33ff34c564c3d3b88ad2'
URL = 'https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/'+SHA


def main():
    original = FOLDER/'CTA-cardio.nrrd'
    if hashlib.file_digest(original.open('rb'),'sha256').hexdigest()!=SHA:
        raise ValueError('Public sample checksum mismatch')
    image = sitk.ReadImage(str(original))
    if image.GetDimension()!=3 or image.GetNumberOfComponentsPerPixel()!=1:
        raise ValueError('Sample must be scalar 3D CT')
    # New image retains voxel values and geometry but not arbitrary text metadata.
    sanitized = sitk.GetImageFromArray(sitk.GetArrayViewFromImage(image))
    sanitized.CopyInformation(image)
    source = FOLDER/'CTACardio_original_hu.nii.gz'
    sitk.WriteImage(sanitized,str(source))
    nii = nib.load(source)
    assert nii.header.get_xyzt_units()[0]=='mm'
    assert tuple(nii.shape)==image.GetSize()
    assert np.array_equal(np.asarray(nii.dataobj).transpose(2,1,0),sitk.GetArrayViewFromImage(image))
    for index in [(0,0,0),tuple(n-1 for n in image.GetSize())]:
        expected = np.array(image.TransformIndexToPhysicalPoint(index))*[-1,-1,1]
        np.testing.assert_allclose((nii.affine@np.array([*index,1]))[:3],expected,atol=1e-3)
    source_hash = hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
    provenance = {'dataset':'3D Slicer CTACardio public testing sample', 'source_url':URL,
        'source_documentation':'https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/SampleData/SampleData.py',
        'nrrd_sha256':SHA,'nifti_sha256':source_hash,'native_shape':list(nii.shape),
        'native_voxels':int(np.prod(nii.shape)),'conversion':'Lossless NRRD to NIfTI, metadata-minimized, physical LPS→RAS header conversion only',
        'voxel_values_and_physical_endpoints_verified':True,
        'usage':'Local workflow acceptance only; no redistribution, training or new benchmark claims',
        'limitations':'No reference coronary mask. Acquisition/domain differs from ImageCAS; not validated anatomical accuracy.'}
    (FOLDER/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2))
    del image,sanitized
    credentials=json.loads((ROOT/'backend/demo-credentials.json').read_text())
    account=next(item for item in credentials['accounts'] if item['email']=='researcher.demo@example.com')
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=180) as client:
        response=client.post('/api/auth/login',json={'email':account['email'],'password':account['password']})
        response.raise_for_status(); client.headers['Authorization']='Bearer '+response.json()['access_token']
        response=client.post('/api/cases',json={'case_code':'PUBLIC-CTA-CHECK-'+uuid4().hex[:6],
            'modality':'CTA','anatomy':'coronary','intended_task':'volume_preparation',
            'source_dataset':'3D Slicer CTACardio public research test sample',
            'source_reference':'SlicerTestingData SHA256 3b0d4eb1a7d8ebb0c5a89cc0504640f76a030b4e869e33ff34c564c3d3b88ad2'})
        response.raise_for_status(); case=response.json(); base=f'/api/cases/{case["id"]}/volumes/analyses'
        with source.open('rb') as stream:
            response=client.post(base,files={'file':(source.name,stream,'application/gzip')},
                data={'hu_confirmed':'true','research_confirmed':'true','input_kind':'medical_study'})
        response.raise_for_status(); submitted=response.json()
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            response=client.get(base); response.raise_for_status()
            row=next(item for item in response.json() if item['id']==submitted['id'])
            if row['status'] in {'completed','failed'}: break
            time.sleep(.5)
        if row['status']!='completed': raise RuntimeError('Public CTA job '+row['status']+': '+str(row.get('error')))
        checks={}
        for name,url in row['artifacts'].items():
            response=client.get(url); response.raise_for_status()
            checks[name]={'bytes':len(response.content),'sha256':hashlib.sha256(response.content).hexdigest()}
            if name=='mask_source.nii.gz':
                mask=nib.Nifti1Image.from_bytes(gzip.decompress(response.content))
                assert mask.shape==nii.shape
                np.testing.assert_allclose(mask.affine,nii.affine,atol=1e-4)
                assert set(np.unique(mask.dataobj))<={0,1}
            elif name=='probability_coarse.nii.gz':
                p=nib.Nifti1Image.from_bytes(gzip.decompress(response.content))
                values=np.asarray(p.dataobj)
                assert values.shape==(128,128,128) and np.isfinite(values).all()
                assert values.min()>=0 and values.max()<=1
        assert row['source_sha256']==source_hash and row['input_kind']=='medical_study'
        assert row['result']['severity'] is None and row['result']['clinical_validated'] is False
        receipt={'provenance':provenance,'case_code':case['case_code'],'case_id':case['id'],
            'run_id':row['id'],'status':row['status'],'result':row['result'],
            'artifacts_verified':checks,'source_grid_shape_and_affine_verified':True,
            'performance_metrics_calculated':False}
        (ROOT/'reports/public_cta_integration_receipt.json').write_text(json.dumps(receipt,indent=2))
        print(json.dumps({'case_code':case['case_code'],'status':row['status'],
            'native_shape':list(nii.shape),'foreground_voxels':row['result']['coarse_foreground_voxels'],
            'duration_seconds':row['result']['duration_seconds'],'artifacts_verified':list(checks),
            'source_grid_shape_and_affine_verified':True}))


if __name__=='__main__':
    main()
