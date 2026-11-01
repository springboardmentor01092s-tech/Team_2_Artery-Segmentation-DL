"""Opt-in genuine public validation image through the existing job pipeline."""
import hashlib
import os
import time
from pathlib import Path
from uuid import uuid4
import pytest


@pytest.mark.skipif(not os.getenv("CV_PUBLIC_HANDOFF_IMAGE"), reason="Opt-in public ARCADE fixture on connected drive")
def test_known_arcade_image_with_installed_weights(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app, execute_analysis_job
    from app.inference_jobs import InferenceWorker
    from app import trained_release
    from test_rbac_system import make_user
    path = Path(os.environ["CV_PUBLIC_HANDOFF_IMAGE"])
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "748a2d4fcd2df8a11e5c1b836abbdf5201d21f75be808e0e71865ef8cda7bf55"
    monkeypatch.setenv("COROVISION_MODEL_PROVIDER", "preserved")
    assert trained_release.ready()
    with TestClient(app) as client:
        _, owner = make_user(f"public-fixture-{uuid4().hex}@example.org", "researcher")
        case = client.post("/api/cases", headers=owner, json={"case_code": "PUBLIC-ARCADE-" + uuid4().hex[:8]}).json()
        uploaded = client.post(f'/api/cases/{case["id"]}/images', headers=owner,
                               files={"file": ("public-arcade-validation.png", raw, "image/png")})
        assert uploaded.status_code == 201, uploaded.text
        asset = uploaded.json()
        worker = InferenceWorker(execute_analysis_job); worker.start()
        try:
            response = client.post(f'/api/images/{asset["id"]}/analysis/jobs', headers=owner, json={"idempotency_key": uuid4().hex})
            assert response.status_code == 202
            job = response.json(); deadline = time.monotonic() + 60
            while job["status"] in {"pending", "processing"} and time.monotonic() < deadline:
                time.sleep(.1)
                job = client.get(job["status_url"], headers=owner).json()
            assert job["status"] == "completed", job
            record = client.get(job["result_url"], headers=owner).json()["structured_result"]
            assert record["model_version"] == trained_release.RELEASE["version"]
            assert record["measurements"]["artery_pixels"] > 0
            assert record["severity"]["narrowing_percent"] is None
            assert record["models"]["checkpoint_sha256"] == {m["task"]: m["sha256"] for m in trained_release.RELEASE["models"]}
            for kind in ("artery_mask", "stenosis_mask", "raw_scores", "overlay"):
                assert client.get(record["artifacts"][kind], headers=owner).status_code == 200
            assert record["explanation"]["method"] == "deterministic_saved_result_template"
        finally:
            worker.close()
