"""Lossless nnU-Net layout adapter; original CT/masks/splits remain untouched."""
import argparse
import json
import shutil
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    audit=json.loads(args.audit.read_text())
    assert audit['voxel_audit_passed'] and not audit['errors'], 'CT integrity audit must pass first'
    meta=json.loads((args.source/'dataset.json').read_text())
    assert meta['numTraining']==303 and meta['labels']=={'0':'background','1':'Vessel','2':'Tumour'}
    destination=args.destination/'Dataset008_HepaticVessel'
    assert not destination.exists(), 'Refuse to overwrite an existing converted dataset'
    for name in ('imagesTr','labelsTr'):
        (destination/name).mkdir(parents=True)
    for row in meta['training']:
        name=Path(row['image']).name
        case=name.removesuffix('.nii.gz')
        # Byte-for-byte copies preserve affine, spacing, intensities and categories.
        shutil.copyfile(args.source/row['image'],destination/'imagesTr'/f'{case}_0000.nii.gz')
        shutil.copyfile(args.source/row['label'],destination/'labelsTr'/f'{case}.nii.gz')
    (destination/'dataset.json').write_text(json.dumps({'channel_names':{'0':'CT'},
        'labels':{'background':0,'vessel':1,'tumour':2},'numTraining':303,
        'file_ending':'.nii.gz','licence':meta['licence']},indent=2))
    (destination/'source_provenance.json').write_text(json.dumps({
        'source_dataset_json':meta,'audit':audit,'test_policy':'Official imagesTs excluded from fitting and configuration selection',
        'conversion':'Byte-identical copy; channel suffix only; no intensity/label transforms',
        'cross_validation':'nnU-Net generated 5-fold case-level cross-validation; retain splits_final.json'},indent=2))
    print(destination)


if __name__=='__main__':
    main()
