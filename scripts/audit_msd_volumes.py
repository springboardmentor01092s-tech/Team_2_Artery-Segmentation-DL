"""Full-volume MSD integrity/EDA gate; no resampling or label modification."""
import json
from pathlib import Path
import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT/'Task08_HepaticVessel'
    metadata = json.loads((source/'dataset.json').read_text())
    rows, errors, warnings = [], [], []
    for i, entry in enumerate(metadata['training']):
        try:
            image = nib.load(source/entry['image'])
            label = nib.load(source/entry['label'])
            if image.shape != label.shape:
                raise ValueError('Image and label shapes differ')
            if not np.allclose(image.affine,label.affine,rtol=0,atol=1e-3):
                raise ValueError('Image/label affine differs by more than 0.001 mm per matrix element')
            if not np.array_equal(image.affine,label.affine):
                warnings.append({'case':Path(entry['image']).name,'affine_max_abs_difference':
                    float(np.max(np.abs(image.affine-label.affine))),
                    'action':'Retain both original headers; submillimetre rounding only, no registration applied'})
            values = np.asarray(image.dataobj,dtype=np.float32)
            if not np.isfinite(values).all():
                raise ValueError('Nonfinite image intensities')
            masks = np.asarray(label.dataobj)
            labels, counts = np.unique(masks,return_counts=True)
            if not set(labels.tolist()).issubset({0,1,2}):
                raise ValueError('Unexpected categorical labels')
            rows.append({'case':Path(entry['image']).name,'shape':image.shape,
                'spacing_mm':image.header.get_zooms()[:3], 'affine':image.affine.tolist(),
                'orientation':nib.aff2axcodes(image.affine),
                'range':[float(values.min()),float(values.max())],
                'labels':{str(int(k)):int(v) for k,v in zip(labels,counts)}})
        except Exception as exc:
            errors.append({'case':entry['image'],'error':str(exc)})
        if (i+1)%20==0:
            print(f'Validated {i+1}/{len(metadata["training"])}',flush=True)
    missing_test = [p for p in metadata['test'] if not (source/p).is_file()]
    listed_test={Path(p).name for p in metadata['test']}
    actual_test={p.name for p in (source/'imagesTs').glob('*.nii.gz')}
    report={'dataset':'MSD Task08 HepaticVessel','modality':'CT','licence':metadata['licence'],
        'declared_test_count':metadata['numTest'],'listed_test_count':len(listed_test),
        'actual_test_count':len(actual_test),'unlisted_test_files':sorted(actual_test-listed_test),
        'labels':metadata['labels'],'cases_checked':len(rows),'errors':errors,'warnings':warnings,
        'missing_test':missing_test,'voxel_audit_passed':not errors and len(rows)==303,
        'training_complete':False,'test_voxels_used_for_tuning':False,'cases':rows}
    out=ROOT/'reports/msd_volume_audit.json'
    out.write_text(json.dumps(report,indent=2,default=lambda v:v.item()))
    print(out, 'errors:',len(errors),'warnings:',len(warnings),flush=True)


if __name__=='__main__':
    main()
