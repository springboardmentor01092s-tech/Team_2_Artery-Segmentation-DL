"""Stage required model/config files from an existing Kaggle output ZIP safely.

Never executes downloaded code, extracts pickle internals, imports test images,
or replaces active models. Checkpoint hashes are matched to release contracts.
"""
import argparse
import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    args=parser.parse_args()
    digest=sha(args.archive)
    out=ROOT/'external_artifacts/kaggle_downloads_20261026'/digest[:16]
    if out.exists():
        receipt=json.loads((out/'receipt.json').read_text())
        if receipt['archive_sha256']!=digest:
            raise ValueError('Existing archive receipt mismatch')
        for row in receipt['copied']:
            relative=PurePosixPath(row['file'])
            if relative.is_absolute() or '..' in relative.parts or '\\' in row['file']:
                raise ValueError('Unsafe receipt path')
            if sha(out.joinpath(*relative.parts))!=row['sha256']:
                raise ValueError('Previously staged file changed')
        print(json.dumps(dict(receipt=str(out/'receipt.json'),status='verified_existing')))
        return
    out.mkdir(parents=True,exist_ok=False)
    release=json.loads((ROOT/'ml/releases/corovision_20261023.json').read_text())
    known={m['sha256']:m['task'] for m in release['models']}
    volume=json.loads((ROOT/'ml/releases/imagecas_3d_128.json').read_text())
    known[volume['checkpoint_sha256']]='3d_coronary_segmentation'
    copied=[]; skipped=[]
    with zipfile.ZipFile(args.archive) as archive:
        entries=archive.infolist()
        if len(entries)>10000 or sum(e.file_size for e in entries)>10*1024**3:
            raise ValueError('Archive exceeds intake limits')
        seen=set()
        for entry in entries:
            path=PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename:
                raise ValueError('Unsafe archive member')
            if stat.S_ISLNK(entry.external_attr>>16) or entry.filename in seen:
                raise ValueError('Symlink or duplicate archive member')
            seen.add(entry.filename)
        for entry in entries:
            path=PurePosixPath(entry.filename)
            if entry.is_dir():
                continue
            allowed=(path.name=='best.pt' or path.suffix in {'.json','.jsonl','.yaml','.yml','.md'})
            if not allowed or '__pycache__' in path.parts or 'test' in path.name.lower():
                skipped.append(entry.filename)
                continue
            dest=out.joinpath(*path.parts)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with archive.open(entry) as source, dest.open('xb') as target:
                shutil.copyfileobj(source,target)
            member_sha=sha(dest)
            copied.append(dict(file=entry.filename,bytes=entry.file_size,sha256=member_sha,
                               registered_task=known.get(member_sha) if path.suffix=='.pt' else None))
    receipt=dict(source_archive=args.archive.name,archive_sha256=digest,
                 copied=copied,skipped=skipped,active_models_changed=False,
                 downloaded_code_executed=False,training_performed=False)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(dict(receipt=str(out/'receipt.json'),files_staged=len(copied),
                          registered_models=[r['registered_task'] for r in copied if r['registered_task']]),indent=2))


if __name__=='__main__':
    main()
