"""Reconcile completed project output bundles against immutable handoff hashes."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',type=Path,required=True)
    parser.add_argument('--packages',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():
        raise ValueError('Do not overwrite existing reconciliation evidence')
    known={}
    for path in args.packages.glob('*/package.json'):
        package=json.loads(path.read_text())
        for model in package.get('models',[]):
            known.setdefault(model['sha256'],[]).append(dict(package=path.parent.name,
                task=package.get('task'),selected=model.get('selected_for_integration')))
        if 'sha256' in package:
            known.setdefault(package['sha256'],[]).append(dict(package=path.parent.name,
                task=package.get('task'),selected=None))
    archives=[]; checkpoints=[]
    allowed_roots={'syntax_pretrained','imagecas128','imagecasx128','corovision_stenosis',
                   'corovision_syntax','dca2d','aorta128','cadica_corrected','stenosis_boxes','hepatic128'}
    for path in sorted(args.downloads.glob('results*.zip')):
        if not zipfile.is_zipfile(path):
            archives.append(dict(archive=path.name,status='invalid_or_incomplete_zip'))
            continue
        with zipfile.ZipFile(path) as archive:
            names=archive.namelist()
            best=[name for name in names if name.endswith('/best.pt')]
            roots={name.split('/')[0] for name in names}
        if not best or not roots.issubset(allowed_roots):
            archives.append(dict(archive=path.name,status='not_a_baseline_bundle_left_unchanged',
                                 checkpoint_count=len(best)))
            continue
        subprocess.run([sys.executable,str(ROOT/'scripts/import_kaggle_model_bundle.py'),str(path)],check=True)
        archive_hash=digest(path)
        folder=ROOT/'external_artifacts/kaggle_downloads_20261026'/archive_hash[:16]
        receipt=json.loads((folder/'receipt.json').read_text())
        archives.append(dict(archive=path.name,sha256=archive_hash,status='staged_verified',
                             receipt=str(folder.relative_to(ROOT)/'receipt.json')))
        for row in receipt['copied']:
            if row['file'].endswith('/best.pt'):
                checkpoints.append(dict(archive=path.name,file=row['file'],sha256=row['sha256'],
                    registered_task=row['registered_task'],handoff_matches=known.get(row['sha256'],[]),
                    verification='exact_handoff_match' if row['sha256'] in known else 'unmatched_quarantined',
                    active_model_replaced=False))
    result=dict(archives=archives,checkpoints=checkpoints,training_performed=False,
                active_models_changed=False,downloaded_code_executed=False,
                incomplete_downloads=len(list(args.downloads.glob('*.crdownload'))),
                note='File verification is not inference integration or new accuracy validation.')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x') as handle:
        json.dump(result,handle,indent=2)
    print(json.dumps(dict(report=str(args.report),staged_archives=sum(r['status']=='staged_verified' for r in archives),
         checkpoints=len(checkpoints),matched=sum(bool(r['handoff_matches']) for r in checkpoints),
         incomplete_downloads=result['incomplete_downloads']),indent=2))


if __name__=='__main__':
    main()
