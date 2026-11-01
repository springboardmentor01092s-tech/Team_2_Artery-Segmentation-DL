import importlib.util
from pathlib import Path
import sqlite3
import pytest

spec=importlib.util.spec_from_file_location('backup_local',Path(__file__).resolve().parents[2]/'scripts/backup_local.py')
backup=importlib.util.module_from_spec(spec);spec.loader.exec_module(backup)


def source(tmp_path):
    database=tmp_path/'source.db'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE records(value TEXT)');db.execute("INSERT INTO records VALUES ('synthetic')")
    storage=tmp_path/'uploads';storage.mkdir();(storage/'synthetic.txt').write_text('deidentified synthetic fixture')
    return database,storage


def test_offline_roundtrip_preserves_database_and_artifact(tmp_path):
    db,storage=source(tmp_path);snapshot=tmp_path/'snapshot';out=tmp_path/'restored'
    backup.create(db,storage,snapshot,offline_confirmed=True)
    assert backup.restore(snapshot,out)['restored_files']==2
    with sqlite3.connect(out/'metadata.sqlite') as restored:
        assert restored.execute('SELECT value FROM records').fetchone()[0]=='synthetic'
    assert (out/'storage/synthetic.txt').read_bytes()==(storage/'synthetic.txt').read_bytes()
    with pytest.raises(FileExistsError):backup.restore(snapshot,out)
    with pytest.raises(ValueError):backup.restore(snapshot,snapshot/'nested-restore')
    with pytest.raises(FileExistsError):backup.create(db,storage,snapshot,offline_confirmed=True)


def test_requires_offline_and_rejects_nested_destination(tmp_path):
    db,storage=source(tmp_path)
    with pytest.raises(ValueError):backup.create(db,storage,tmp_path/'snapshot')
    with pytest.raises(ValueError):backup.create(db,storage,storage/'snapshot',offline_confirmed=True)


def test_tampered_snapshot_rejected_before_restore(tmp_path):
    db,storage=source(tmp_path);snapshot=tmp_path/'snapshot'
    backup.create(db,storage,snapshot,offline_confirmed=True)
    (snapshot/'storage/synthetic.txt').write_text('tampered')
    with pytest.raises(ValueError):backup.restore(snapshot,tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_symlinks_not_followed(tmp_path):
    db,storage=source(tmp_path);(storage/'link').symlink_to(db)
    with pytest.raises(ValueError):backup.create(db,storage,tmp_path/'snapshot',offline_confirmed=True)
