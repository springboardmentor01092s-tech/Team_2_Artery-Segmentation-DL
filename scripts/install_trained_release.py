"""Export/import only the two hash-pinned mask checkpoints; never publish weights in Git."""
import argparse,hashlib,json,shutil,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RELEASE=json.loads((ROOT/'ml/releases/corovision_20261023.json').read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser();mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument('--export',type=Path);mode.add_argument('--install',type=Path);ap.add_argument('--training-root',type=Path);args=ap.parse_args()
    if args.export:
        assert args.training_root,'--training-root is required for export';assert not args.export.exists(),'Do not overwrite an existing transfer archive'
        for item in RELEASE['models']:assert sha(args.training_root/item['source_relative'])==item['sha256'],item['task']
        args.export.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(args.export,'w',zipfile.ZIP_STORED) as z:
            for item in RELEASE['models']:z.write(args.training_root/item['source_relative'],item['filename'])
            z.writestr('release.json',json.dumps(RELEASE,indent=2))
        print(json.dumps(dict(archive=str(args.export.resolve()),sha256=sha(args.export),raw_datasets=False)));return
    models=(ROOT/'models').resolve();models.mkdir(exist_ok=True);target=(models/'trained_release').resolve();assert target.parent==models
    if target.exists():
        assert all(sha(target/x['filename'])==x['sha256'] for x in RELEASE['models']),'Existing release differs; preserve it and select a new installation explicitly'
        print('Existing release verified; no files changed.');return
    with zipfile.ZipFile(args.install) as z:
        expected={x['filename'] for x in RELEASE['models']}|{'release.json'}
        assert len(z.infolist())==len(expected) and set(z.namelist())==expected,'Unexpected archive members'
        assert sum(x.file_size for x in z.infolist())<1024**3,'Archive exceeds bounded artifact size'
        assert json.loads(z.read('release.json'))==RELEASE,'Release contract mismatch'
        with tempfile.TemporaryDirectory(dir=models,prefix='install-') as temp:
            staging=Path(temp)/'release';staging.mkdir()
            for item in RELEASE['models']:
                p=staging/item['filename']
                with z.open(item['filename']) as source,p.open('wb') as dest:shutil.copyfileobj(source,dest)
                assert sha(p)==item['sha256'],'Checkpoint hash mismatch'
            (staging/'release.json').write_text(json.dumps(RELEASE,indent=2))
            assert staging.resolve().is_relative_to(models) and target.is_relative_to(models)
            staging.rename(target)
    print(json.dumps(dict(installed=str(target),models=2,weights_committed=False,version=RELEASE['version'])))
if __name__=='__main__':main()
