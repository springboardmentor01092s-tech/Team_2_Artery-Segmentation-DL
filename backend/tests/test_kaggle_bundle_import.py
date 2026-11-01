import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

PATH=Path(__file__).resolve().parents[2]/'scripts/import_kaggle_model_bundle.py'
spec=importlib.util.spec_from_file_location('kaggle_bundle_import',PATH)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def setup(tmp_path,monkeypatch,members):
    root=tmp_path/'app'; release=root/'ml/releases'; release.mkdir(parents=True)
    (release/'corovision_20261023.json').write_text(json.dumps(dict(models=[dict(task='fixture',sha256=hashlib.sha256(b'weights').hexdigest())])))
    (release/'imagecas_3d_128.json').write_text(json.dumps(dict(checkpoint_sha256='0'*64)))
    archive=tmp_path/'results.zip'
    with zipfile.ZipFile(archive,'w') as z:
        for name,data in members:
            z.writestr(name,data)
    monkeypatch.setattr(module,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['import_kaggle_model_bundle.py',str(archive)])
    return root


def receipt(root):
    return next((root/'external_artifacts').glob('**/receipt.json'))


def test_stage_required_files_only(tmp_path,monkeypatch):
    root=setup(tmp_path,monkeypatch,[('model/best.pt',b'weights'),('model/config.json',b'{}'),
        ('train.py',b'raise RuntimeError()'),('model/last.pt',b'optimizer'),('test.json',b'{}')])
    module.main()
    r=json.loads(receipt(root).read_text())
    assert len(r['copied'])==2 and len(r['skipped'])==3
    assert r['copied'][0]['registered_task']=='fixture'
    assert not r['active_models_changed'] and not r['downloaded_code_executed']


def test_idempotent_import_verifies_existing_files(tmp_path,monkeypatch):
    root=setup(tmp_path,monkeypatch,[('model/best.pt',b'weights')])
    module.main(); module.main()
    (receipt(root).parent/'model/best.pt').write_bytes(b'changed')
    with pytest.raises(ValueError,match='staged file changed'):
        module.main()


@pytest.mark.parametrize('name',['../escape.json','/absolute.json','model\\escape.json'])
def test_archive_path_escape_rejected(tmp_path,monkeypatch,name):
    root=setup(tmp_path,monkeypatch,[(name,b'{}')])
    with pytest.raises(ValueError,match='Unsafe archive'):
        module.main()
    assert not list(root.glob('**/receipt.json'))
