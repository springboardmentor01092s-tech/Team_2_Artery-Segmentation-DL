"""Install the complete pinned application model set from a downloaded handoff.

No training files, datasets, unapproved candidates or secrets are imported.
Existing checkpoints are verified and never replaced.
"""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def specifications(root=ROOT):
    release = json.loads((root/'ml/releases/corovision_20261023.json').read_text())
    volume = json.loads((root/'ml/releases/imagecas_3d_128.json').read_text())
    specs = [dict(task=m['task'], source=m['source_relative'],
                  target='models/trained_release/'+m['filename'], sha256=m['sha256'])
             for m in release['models']]
    specs.append(dict(task='3d_coronary_segmentation',
                      source='trained_models/imagecas128/models/candidate_01_models/best.pt',
                      target='models/volume_release/imagecas128.pt',
                      sha256=volume['checkpoint_sha256']))
    return specs


def install(source, *, check_only=False, root=ROOT, specs=None):
    source = source.resolve() if source is not None else None
    specs = specifications(root) if specs is None else specs
    # Preflight every member before installing any member.
    rows = []
    for spec in specs:
        target = root/spec['target']
        if not target.resolve().is_relative_to((root/'models').resolve()):
            raise ValueError('Destination is outside model storage')
        installed = target.is_file()
        if target.exists() and not installed:
            raise ValueError('Checkpoint destination is not a regular file')
        if installed and digest(target) != spec['sha256']:
            raise ValueError('Existing checkpoint differs; refusing replacement: '+spec['task'])
        origin = source/spec['source'] if source else None
        if not installed and not check_only:
            if origin is None or not origin.is_file():
                raise ValueError('Missing source checkpoint: '+spec['task'])
            if not origin.resolve().is_relative_to(source):
                raise ValueError('Source checkpoint escapes selected handoff')
            if digest(origin) != spec['sha256']:
                raise ValueError('Source checkpoint checksum mismatch: '+spec['task'])
        rows.append(dict(task=spec['task'], sha256=spec['sha256'],
                         installed=installed, status='verified_existing' if installed else 'missing'))
    if not check_only:
        for spec, row in zip(specs, rows):
            if row['installed']:
                continue
            target = root/spec['target']; target.parent.mkdir(parents=True, exist_ok=True)
            # Copy, never link to the original immutable handoff.
            fd, name = tempfile.mkstemp(prefix='.checkpoint-', dir=target.parent)
            temporary = Path(name)
            try:
                with os.fdopen(fd, 'wb') as dest, (source/spec['source']).open('rb') as src:
                    shutil.copyfileobj(src, dest)
                    dest.flush(); os.fsync(dest.fileno())
                if digest(temporary) != spec['sha256']:
                    raise ValueError('Copied checkpoint checksum mismatch')
                # Atomic no-clobber publication: a concurrent installation is
                # never overwritten, even if it appeared after preflight.
                os.link(temporary, target)
                row.update(installed=True, status='installed_verified')
            finally:
                temporary.unlink(missing_ok=True)
    return dict(models=rows, all_required_installed=all(r['installed'] for r in rows),
                optimizer_updates=0, training_performed=False,
                baseline_replacement=False, unsupported_candidates_activated=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Root of already downloaded, verified model handoff')
    parser.add_argument('--check', action='store_true', help='Read-only check of installed model hashes')
    parser.add_argument('--report', type=Path, help='New receipt file; never overwrites existing evidence')
    args = parser.parse_args()
    result = install(args.source, check_only=args.check)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open('x') as handle:
            json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))
    if not result['all_required_installed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
