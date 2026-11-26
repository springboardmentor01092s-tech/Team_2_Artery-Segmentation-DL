"""Shared test setup: temporary database, test users and a sample scan.

The real uploads folder is used (the pipeline looks for its files there), and every file
the tests create in it is deleted again at the end.
"""
import glob
import os
import shutil

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import auth, models
from app.database import Base, get_db
from app.main import app

PASSWORD = "Test-pass-123"
TEST_CASE_ID = 9001  # high id so test files never clash with real cases


def _snapshot():
    """All files currently under uploads (normalized paths)."""
    return {
        os.path.normpath(p)
        for p in glob.glob("uploads/**/*", recursive=True)
        if os.path.isfile(p)
    }


def _cleanup_test_files(before):
    """Delete every file the tests created, plus any leftovers of the test case."""
    for path in _snapshot() - before:
        try:
            os.remove(path)
        except OSError:
            pass
    for pattern in (f"uploads/**/case_{TEST_CASE_ID}*", "uploads/test_probe_*.txt"):
        for path in glob.glob(pattern, recursive=True):
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass


def _login(client, email):
    r = client.post("/auth/login", data={"username": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def workdir(tmp_path_factory):
    return tmp_path_factory.mktemp("artery_tests")


@pytest.fixture(scope="session")
def client(workdir):
    """TestClient wired to a temporary SQLite database."""
    os.makedirs("uploads", exist_ok=True)
    before = _snapshot()

    engine = create_engine(
        f"sqlite:///{workdir / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        c.session_factory = session_factory
        c.files_before = before
        yield c

    app.dependency_overrides.clear()
    _cleanup_test_files(before)


@pytest.fixture(scope="session")
def users(client):
    """Test users for every role: {name: {"email", "headers", "id"}}."""
    out = {}
    for name, role in [
        ("clinician", "clinician"),
        ("clinician2", "clinician"),
        ("researcher", "researcher"),
        ("data_scientist", "data_scientist"),
    ]:
        email = f"{name}@test.example"
        r = client.post(
            "/auth/register",
            json={"name": f"Test {name}", "email": email, "password": PASSWORD, "role": role},
        )
        assert r.status_code == 201, r.text
        out[name] = {"email": email, "headers": _login(client, email)}

    # admin cannot register through the API, so create it directly in the test database
    db = client.session_factory()
    db.add(
        models.User(
            name="Test admin",
            email="admin@test.example",
            hashed_password=auth.hash_password(PASSWORD),
            role="admin",
        )
    )
    db.commit()
    db.close()
    out["admin"] = {"email": "admin@test.example", "headers": _login(client, "admin@test.example")}

    for u in out.values():
        u["id"] = client.get("/auth/me", headers=u["headers"]).json()["id"]
    return out


@pytest.fixture(scope="session")
def make_case(client):
    def _make(headers, patient_id="p-test", **extra):
        r = client.post("/cases", json={"patient_id": patient_id, **extra}, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture(scope="session")
def sample_scan(workdir, client):
    """A real scan that existed in your uploads folder before the tests, else a synthetic image."""
    for pattern in ("uploads/case_*.png", "uploads/case_*.jpg", "uploads/case_*.jpeg"):
        for path in sorted(glob.glob(pattern)):
            norm = os.path.normpath(path)
            if f"case_{TEST_CASE_ID}" in norm or norm not in client.files_before:
                continue
            try:
                with Image.open(norm) as im:
                    im.verify()
            except Exception:
                continue
            dest = str(workdir / ("sample_scan" + os.path.splitext(norm)[1]))
            shutil.copy(norm, dest)
            return dest

    rng = np.random.default_rng(0)
    arr = rng.normal(150, 12, (512, 512)).clip(0, 255)
    for x in range(60, 460):
        y = 256 + int(80 * np.sin(x / 60))
        arr[y - 6 : y + 6, x] = 40
    dest = str(workdir / "sample_scan.png")
    Image.fromarray(arr.astype(np.uint8)).save(dest)
    return dest


@pytest.fixture(scope="session")
def e2e_case(client, users, sample_scan):
    """One case with a scan uploaded, owned by the test clinician (id 9001)."""
    db = client.session_factory()
    db.add(
        models.Case(
            id=TEST_CASE_ID,
            owner_id=users["clinician"]["id"],
            patient_id="e2e-test",
            age=40,
            gender="Female",
            imaging_modality="Coronary angiography",
            scan_date="2026-11-19",
            anatomical_region="LAD",
        )
    )
    db.commit()
    db.close()

    mime = "image/jpeg" if sample_scan.lower().endswith((".jpg", ".jpeg")) else "image/png"
    with open(sample_scan, "rb") as f:
        r = client.post(
            f"/cases/{TEST_CASE_ID}/upload",
            files={"file": (os.path.basename(sample_scan), f, mime)},
            headers=users["clinician"]["headers"],
        )
    assert r.status_code == 200, r.text
    assert r.json()["image_path"]
    return {"id": TEST_CASE_ID, "headers": users["clinician"]["headers"]}