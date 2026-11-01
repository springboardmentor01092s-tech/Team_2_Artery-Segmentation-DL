"""Copy useful, hash-verified drive evidence without changing application models."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

TEXT = {'.json', '.jsonl', '.csv', '.tsv', '.md', '.txt', '.yaml', '.yml', '.toml', '.py', '.ipynb', '.log', '.lock'}
WEIGHTS = {'.pt', '.pth', '.ckpt', '.onnx', '.safetensors'}
SECRET = re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|(?:AKIA[0-9A-Z]{16})|(?:gh[pousr]_[A-Za-z0-9]{30,})|(?:hf_[A-Za-z0-9]{25,})|["\'](?:api_key|api_token|access_token|refresh_token|password|secret_access_key)["\']\s*:\s*["\'][^"\'\s]{12,}["\']', re.I)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--drive', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    drive, dest = args.drive.resolve(), args.destination.resolve()
    selected, excluded = [], collections.Counter()
    for package, label in [('CoroVision_Full_20261024', 'full_handoff'), ('CoroVision_Kaggle_Offline_20261024', 'kaggle_offline')]:
        for line in (drive / package / 'manifest.jsonl').open():
            row = json.loads(line)
            logical = row.get('source_path', row.get('path')).replace('\\', '/')
            path = Path(logical)
            top = path.parts[0]
            size = row['bytes']
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Unsafe logical path')
            if any(p.lower() in {'.env', 'kaggle.json', 'credentials.json', 'token.json', '__pycache__', '.git', 'node_modules'} for p in path.parts):
                excluded['credentials_or_cache'] += 1
                continue
            if top in {'Dataset', 'application'} or (label == 'kaggle_offline' and top == 'datasets'):
                excluded['raw_data_or_old_app_or_input_archives'] += 1
                continue
            suffix = path.suffix.lower()
            useful = suffix in TEXT and size <= 30_000_000
            useful |= suffix in WEIGHTS and top not in {'processed'}
            useful |= suffix in {'.png', '.svg', '.pdf'} and top in {'reports', 'docs', 'trained_models'} and size <= 20_000_000
            if not useful:
                excluded['bulk_arrays_archives_or_unneeded_binary'] += 1
                continue
            source = (drive / row['disk_path'].replace('\\', '/')).resolve()
            if not source.is_relative_to(drive):
                raise ValueError('Source escaped drive')
            selected.append((label, logical, source, row))
    unique = {r['sha256']: r['bytes'] for _, _, _, r in selected}
    print(json.dumps({'selected_files': len(selected), 'logical_bytes': sum(r['bytes'] for *_, r in selected), 'unique_bytes': sum(unique.values()), 'excluded': dict(excluded)}), flush=True)
    if not args.apply:
        return
    dest.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(dest).free < sum(unique.values()) + 2_000_000_000:
        raise RuntimeError('Insufficient free space')
    hashes, records, failures = {}, [], []
    for number, (label, logical, source, row) in enumerate(selected, 1):
        target = dest / label / logical
        try:
            if not source.is_file():
                raise ValueError('Source missing')
            if source.stat().st_size != row['bytes']:
                raise ValueError('Source size mismatch')
            if source.suffix.lower() in TEXT and SECRET.search(source.read_text(errors='replace')):
                excluded['possible_embedded_credential'] += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = row['sha256']
            if target.exists():
                with target.open('rb') as stream:
                    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
                if actual != digest:
                    target = target.with_name(target.stem + '.version-' + digest[:12] + target.suffix)
                    if target.exists():
                        with target.open('rb') as stream:
                            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                                raise ValueError('Versioned destination differs; preserved')
                    else:
                        shutil.copyfile(source, target)
                        with target.open('rb') as stream:
                            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                                raise ValueError('Versioned copy hash mismatch')
            elif digest in hashes:
                os.link(hashes[digest], target)
            else:
                temporary = target.with_name(target.name + '.intake-part')
                if temporary.exists():
                    raise ValueError('Partial destination exists; preserved')
                shutil.copyfile(source, temporary)
                with temporary.open('rb') as stream:
                    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
                if actual != digest:
                    raise ValueError('Copied hash mismatch; partial retained')
                temporary.rename(target)
            hashes[digest] = target
            records.append({'package': label, 'logical_path': logical, 'destination_path': str(target.relative_to(dest)), 'source_disk_path': row['disk_path'], 'bytes': row['bytes'], 'sha256': digest, 'verified': True})
        except (OSError, ValueError) as error:
            failures.append({'path': logical, 'error': str(error)})
        if number % 100 == 0:
            print(json.dumps({'processed': number, 'total': len(selected), 'copied_verified': len(records), 'failures': len(failures)}), flush=True)
    report = {'files': records, 'failures': failures, 'excluded': dict(excluded), 'verified_files': len(records), 'unique_content_bytes': sum({r['sha256']: r['bytes'] for r in records}.values()), 'application_models_changed': False, 'training_executed': False, 'note': 'Reference intake only. Hash identity is not model approval. Duplicate contents use hardlinks; treat intake as immutable.'}
    (dest / 'INTAKE_MANIFEST.json').write_text(json.dumps(report, indent=2))
    (dest / 'README.md').write_text('# Drive reference intake\n\nContains preserved model checkpoints, evaluation records, configurations, dataset metadata and source references from the connected CoroVision backup. See INTAKE_MANIFEST.json for every source path and SHA-256.\n\nThis is ignored local reference material, not an application deployment or model approval. Training was not started. Raw datasets, prepared arrays, input ZIP archives, old application files and suspected credentials were excluded. Identical content uses hardlinks: do not edit these reference copies in place.\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}), flush=True)


if __name__ == '__main__':
    main()
