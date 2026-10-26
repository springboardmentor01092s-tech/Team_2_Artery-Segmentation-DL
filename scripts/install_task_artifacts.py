"""Install hash-pinned task inference artifacts without replacing active models."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.task_models import SPECS,checkpoint_path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'external_artifacts/drive_intake_20261025/full_handoff/trained_models')
    args=parser.parse_args();receipts=[]
    for identity,spec in SPECS.items():
        if 'package' not in spec:continue
        source=args.source/spec['package']/spec['source'];destination=checkpoint_path(identity)
        with source.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=spec['sha256']:raise ValueError(f'Source checksum mismatch: {identity}')
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():
            with destination.open('rb') as stream:existing=hashlib.file_digest(stream,'sha256').hexdigest()
            if existing!=digest:raise ValueError('Refusing to overwrite different task weights')
        else:shutil.copyfile(source,destination)
        with destination.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('Installed checksum mismatch')
        receipts.append(dict(task_id=identity,sha256=digest,verified=True,weights_updated=False))
    print(json.dumps(receipts,indent=2))


if __name__=='__main__':main()
