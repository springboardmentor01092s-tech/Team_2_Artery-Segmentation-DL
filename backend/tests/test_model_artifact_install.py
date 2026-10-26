"""Small fixture tests: no model downloads, pickle loading or network access."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2]/'scripts/install_model_artifacts.py'
spec = importlib.util.spec_from_file_location('model_artifact_install', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def setup(tmp_path):
    source=tmp_path/'source'; source.mkdir()
    (source/'best.pt').write_bytes(b'verified fixture')
    root=tmp_path/'app'; root.mkdir()
    specs=[dict(task='fixture',source='best.pt',target='models/release/model.pt',
                sha256=hashlib.sha256(b'verified fixture').hexdigest())]
    return source,root,specs


def test_install_and_reuse(tmp_path):
    source,root,specs=setup(tmp_path)
    result=module.install(source,root=root,specs=specs)
    assert result['all_required_installed']
    assert result['optimizer_updates']==0
    assert (source/'best.pt').read_bytes()==b'verified fixture'
    assert module.install(None,root=root,specs=specs)['models'][0]['status']=='verified_existing'


def test_different_existing_model_is_preserved(tmp_path):
    source,root,specs=setup(tmp_path)
    target=root/specs[0]['target']; target.parent.mkdir(parents=True)
    target.write_bytes(b'user checkpoint')
    with pytest.raises(ValueError,match='refusing replacement'):
        module.install(source,root=root,specs=specs)
    assert target.read_bytes()==b'user checkpoint'


def test_bad_source_is_rejected(tmp_path):
    source,root,specs=setup(tmp_path)
    (source/'best.pt').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum mismatch'):
        module.install(source,root=root,specs=specs)
    assert not (root/specs[0]['target']).exists()


def test_check_never_installs(tmp_path):
    source,root,specs=setup(tmp_path)
    assert not module.install(source,check_only=True,root=root,specs=specs)['all_required_installed']
    assert not (root/'models').exists()


def test_preflight_prevents_partial_install(tmp_path):
    source,root,specs=setup(tmp_path)
    specs.append(dict(task='missing',source='absent.pt',target='models/release/second.pt',sha256='0'*64))
    with pytest.raises(ValueError,match='Missing source'):
        module.install(source,root=root,specs=specs)
    assert not (root/'models').exists()
