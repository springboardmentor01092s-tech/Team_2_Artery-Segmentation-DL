"""Read-only local metadata audit; never reads test pixels, trains or changes splits."""
import hashlib
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT/'external_artifacts/drive_intake_20261025/full_handoff'


def audit_ica(workspace):
    """Separate local intake, not one of the nine trained task packages."""
    import numpy as np
    from PIL import Image
    source = workspace/'data/external/ICA_NJ_BinarySeg'
    manifest_path = workspace/'data/processed/ica/manifest.csv'
    if not manifest_path.is_file() or not source.is_dir():
        return {'available':False}
    with manifest_path.open() as stream:
        rows = list(csv.DictReader(stream))
    images = {p.stem:p for p in (source/'V1.0/ICA_PNG').glob('*.png')}
    masks = {p.stem:p for p in (source/'V1.0/label').glob('*.png')}
    dimensions, values = set(), np.zeros(256,dtype=np.int64)
    verified, intermediate, errors = 0, 0, []
    hashes = []
    for row in rows:
        stem = Path(row['image_path']).stem
        if stem not in images or stem not in masks:
            errors.append({'sample_id':row['sample_id'],'reason':'missing image/mask pair'})
            continue
        image_path,mask_path = images[stem],masks[stem]
        image_hash = hashlib.file_digest(image_path.open('rb'),'sha256').hexdigest()
        mask_hash = hashlib.file_digest(mask_path.open('rb'),'sha256').hexdigest()
        hashes.append(image_hash)
        verified += image_hash == row['image_sha256'] and mask_hash == row['mask_sha256']
        with Image.open(image_path) as image, Image.open(mask_path) as mask:
            dimensions.add(image.size)
            if image.size != mask.size:
                errors.append({'sample_id':row['sample_id'],'reason':'geometry mismatch'})
            array = np.asarray(mask.convert('L'))
            counts = np.bincount(array.ravel(),minlength=256)
            values += counts
            intermediate += bool(counts[1:255].sum())
    return {'available':True,'source':'Local ICA_NJ_BinarySeg V1.0; separate from trained handoff inventory',
            'manifest_sha256':hashlib.file_digest(manifest_path.open('rb'),'sha256').hexdigest(),
            'manifest_samples':len(rows),'raw_image_count':len(images),'raw_mask_count':len(masks),
            'hash_verified_pairs':int(verified),'unique_image_byte_hashes':len(set(hashes)),
            'image_dimensions':sorted(map(list,dimensions)),
            'masks_with_intermediate_values':int(intermediate),
            'raw_mask_intensity_pixel_counts':{str(i):int(n) for i,n in enumerate(values) if n},
            'class_support_warning':'Raw intensities are not semantic class prevalence; no binarization threshold selected',
            'split_values':sorted({row['split'] for row in rows}),
            'license_file_present':any(p.name.lower().startswith(('license','licence','copying')) for p in source.iterdir()),
            'patient_mapping':'Unverified; numeric filename prefixes are not accepted patient IDs',
            'errors':errors,'pooling_authorized':False,'training_changed':False}


def audit(root=INTAKE):
    expected = json.loads((root/'reports/dataset_compatibility/EVIDENCE_HASHES.json').read_text())
    hashes = []
    for relative,digest in expected.items():
        path = root/relative.replace('\\','/')
        actual = hashlib.file_digest(path.open('rb'),'sha256').hexdigest() if path.is_file() else None
        hashes.append({'source':relative.replace('\\','/'),'expected_sha256':digest,
                       'actual_sha256':actual,'matches':actual == digest})
    registry = json.loads((root/'reports/dataset_compatibility/DATASET_REGISTRY.json').read_text())
    manifests = {}
    for task in ['dca2d','cadica_corrected','stenosis_boxes','aorta128','hepatic128','imagecas128','imagecasx128']:
        manifest = json.loads((root/'processed'/task/'manifest.json').read_text())
        splits = manifest.get('splits',{})
        sets = {key:set(map(str,values)) for key,values in splits.items()}
        manifests[task] = {'split_counts':{key:len(values) for key,values in splits.items()},
                           'within_manifest_split_id_intersections':{
                               f'{a}__{b}':len(sets[a]&sets[b]) for a,b in
                               [('train','val'),('train','test'),('val','test')] if a in sets and b in sets},
                           'identifier_warning':'Sample IDs alone do not establish independent patient identity'}
    cas = json.loads((root/'processed/imagecas128/manifest.json').read_text())['splits']
    casx = json.loads((root/'processed/imagecasx128/manifest.json').read_text())['splits']
    overlaps = {f'imagecas_{a}__imagecasx_{b}':len(set(map(str,x))&set(map(str,y)))
                for a,x in cas.items() for b,y in casx.items()}
    return {'date':'2026-10-25','scope':'Copied local manifests/evidence, not a raw pixel or patient-identity rescan',
            'raw_drive_mounted':Path('/Volumes/240gb').is_dir(),
            'dataset_task_packages':len(registry['datasets']), 'evidence':hashes,
            'all_evidence_hashes_match':all(row['matches'] for row in hashes),
            'manifest_checks':manifests,'imagecas_cross_variant_case_id_intersections':overlaps,
            'additional_local_ica_intake':audit_ica(ROOT.parent),
            'training_configuration_changed':False,'pooling_authorized':False,
            'test_pixels_read':False,'new_model_metrics_calculated':False}


if __name__ == '__main__':
    result = audit()
    (ROOT/'reports/local_dataset_evidence_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({key:result[key] for key in ['dataset_task_packages','all_evidence_hashes_match','raw_drive_mounted',
                                                'imagecas_cross_variant_case_id_intersections']}))
