"""Offline SQLite/storage snapshot. Never uploads, deletes or overwrites data.

Stop all application writers first. PostgreSQL requires its own backup procedure.
Keep backups private; configuration secrets are deliberately not included.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def files(root):
    rows=[]
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise ValueError('Symlinked backup content is not supported')
        if path.is_file():rows.append(path)
    return rows


def create(database, storage, output, *, offline_confirmed=False):
    database,storage,output=map(Path,(database,storage,output))
    if not offline_confirmed:raise ValueError('Stop all writers and explicitly confirm offline state')
    if database.is_symlink() or storage.is_symlink() or not database.is_file() or not storage.is_dir():
        raise ValueError('Existing regular SQLite database and storage directory required')
    if output.resolve().is_relative_to(storage.resolve()):raise ValueError('Backup cannot be inside source storage')
    files(storage)  # Reject symlinks before creating any snapshot.
    output.mkdir(parents=True,exist_ok=False,mode=0o700)
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as source:
        with sqlite3.connect(output/'metadata.sqlite') as target:
            source.backup(target)
            if target.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity check failed')
    shutil.copytree(storage,output/'storage')
    rows=[dict(path=str(p.relative_to(output)),sha256=digest(p),bytes=p.stat().st_size) for p in files(output)]
    manifest=dict(schema_version=1,scope='offline SQLite and storage only; secrets and models excluded',files=rows)
    with (output/'manifest.json').open('x') as stream:json.dump(manifest,stream,indent=2)
    return manifest


def restore(snapshot, output):
    snapshot,output=map(Path,(snapshot,output))
    if snapshot.is_symlink():raise ValueError('Symlink snapshot unsupported')
    if output.resolve().is_relative_to(snapshot.resolve()):raise ValueError('Restore cannot modify snapshot contents')
    manifest=json.loads((snapshot/'manifest.json').read_text())
    if manifest.get('schema_version')!=1:raise ValueError('Unknown backup schema')
    listed=set()
    for row in manifest['files']:
        path=snapshot/row['path']
        if path.is_symlink() or not path.resolve().is_relative_to(snapshot.resolve()):raise ValueError('Unsafe backup path')
        if row['path'] in listed:raise ValueError('Duplicate manifest entry')
        listed.add(row['path'])
        if path.stat().st_size!=row['bytes'] or digest(path)!=row['sha256']:raise ValueError('Backup integrity mismatch')
    actual={str(p.relative_to(snapshot)) for p in files(snapshot) if p!=snapshot/'manifest.json'}
    if listed!=actual or 'metadata.sqlite' not in listed:raise ValueError('Backup file manifest mismatch')
    with sqlite3.connect((snapshot/'metadata.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as source:
        if source.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Invalid SQLite snapshot')
    output.mkdir(parents=True,exist_ok=False,mode=0o700)
    shutil.copy2(snapshot/'metadata.sqlite',output/'metadata.sqlite')
    shutil.copytree(snapshot/'storage',output/'storage')
    return dict(restored_files=len(listed),status='restored_to_new_directory')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    backup=sub.add_parser('create');backup.add_argument('--database',type=Path,required=True)
    backup.add_argument('--storage',type=Path,required=True);backup.add_argument('--output',type=Path,required=True)
    backup.add_argument('--offline-confirmed',action='store_true')
    recovery=sub.add_parser('restore');recovery.add_argument('--snapshot',type=Path,required=True)
    recovery.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='create':
        result=create(args.database,args.storage,args.output,offline_confirmed=args.offline_confirmed)
        print(json.dumps(dict(status='snapshot_created',files=len(result['files']))))
    else:print(json.dumps(restore(args.snapshot,args.output)))
