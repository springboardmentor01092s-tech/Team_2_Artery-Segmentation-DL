from copy import deepcopy
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from app.evaluation_catalog import catalog, evaluation_runs
from app.trained_release import RELEASE
from test_rbac_system import make_user


def test_catalog_preserves_manifest_and_missing_values():
    original = deepcopy(RELEASE)
    data = catalog()
    assert len(data["runs"]) == len(RELEASE["models"]) == 2
    assert data["summary"]["approved_models"] is None
    assert data["summary"]["running_experiments"] is None
    for run, model in zip(data["runs"], RELEASE["models"]):
        assert run["metrics"][0]["value"] == model["validation_dice"]
        assert run["metrics"][1]["value"] == model["validation_iou"]
        assert run["model"]["checkpoint_sha256"] == model["sha256"]
        assert run["dataset"]["split"] == "validation"
        assert run["dataset"]["patient_independence_verified"] is None
        assert run["approval_status"] is None
        assert run["evaluated_at"] is None
        assert not run["prediction_artifacts"]
    assert RELEASE == original
    assert evaluation_runs()[0]["metrics"][0]["aggregation"] != evaluation_runs()[1]["metrics"][0]["aggregation"]


def test_evaluation_endpoints_are_role_gated_and_preserve_detail():
    suffix = uuid4().hex
    with TestClient(app) as client:
        assert client.get("/api/evaluation/runs").status_code == 401
        for role in ("admin", "researcher", "ml_engineer"):
            _, headers = make_user(f"eval-{role}-{suffix}@example.org", role)
            response = client.get("/api/evaluation/runs", headers=headers)
            assert response.status_code == 200
            row = response.json()["runs"][0]
            assert client.get(f'/api/evaluation/runs/{row["id"]}', headers=headers).json() == row
            assert client.get("/api/evaluation/runs/unknown", headers=headers).status_code == 404
        for role in ("viewer", "technician", "doctor", "clinician"):
            _, headers = make_user(f"eval-{role}-{suffix}@example.org", role)
            assert client.get("/api/evaluation/runs", headers=headers).status_code == 403
            assert client.get("/api/evaluation/runs/unknown", headers=headers).status_code == 403
