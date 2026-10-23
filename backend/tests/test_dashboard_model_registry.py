import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app import main
from app.main import app
from test_rbac_system import make_user


def test_dashboard_aggregates_only_accessible_cases_and_model_registry_is_role_gated():
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        _, owner = make_user(f"dashboard-{suffix}@example.org", "researcher")
        _, other = make_user(f"other-{suffix}@example.org", "researcher")
        created = client.post("/api/cases", headers=owner, json={"case_code": f"DASH-{suffix}"})
        assert created.status_code == 201
        owner_summary = client.get("/api/dashboard/analytics", headers=owner)
        other_summary = client.get("/api/dashboard/analytics", headers=other)
        assert owner_summary.status_code == other_summary.status_code == 200
        assert owner_summary.json()["total_cases"] == 1
        assert other_summary.json()["total_cases"] == 0
        assert owner_summary.json()["model_flagged_cases"] == 0
        assert owner_summary.json()["clinician_severity_distribution"]["severe"] == 0
        assert "normal_cases" not in owner_summary.json()
        assert client.get("/api/analysis/models", headers=other).status_code == 200
        _, viewer = make_user(f"viewer-{suffix}@example.org", "viewer")
        assert client.get("/api/analysis/models", headers=viewer).status_code == 403


def test_model_activation_records_history_and_uses_only_available_checkpoint_pairs(tmp_path, monkeypatch):
    suffix = uuid4().hex[:10]
    model_root = tmp_path / "models" / "segmentation"
    for task in ("syntax", "stenosis"):
        (model_root / task).mkdir(parents=True)
        for architecture in ("tiny_unet", "attention_unet"):
            (model_root / task / f"{architecture}.pt").write_bytes(f"{task}:{architecture}".encode())
            (model_root / task / f"{architecture}_report.json").write_text(json.dumps({
                "training_run_id": "20261012T120000Z", "model_version": f"arcade-{architecture}-20261012T120000Z"}))
    (model_root / "promoted_model.json").write_text(json.dumps({
        "architecture": "tiny_unet", "version": "arcade-tiny_unet-20261012T120000Z"}))
    (model_root / "comparison_report.json").write_text(json.dumps({
        "architecture_mean_validation_dice": {"tiny_unet": 0.4, "attention_unet": 0.5},
        "experiments": [{"task": task, "architecture": architecture, "threshold": 0.45,
                         "train_images": 20, "validation_images": 8,
                         "best_validation": {"dice": 0.5 if architecture == "attention_unet" else 0.4},
                         "dataset": "ARCADE"}
                        for task in ("syntax", "stenosis")
                        for architecture in ("tiny_unet", "attention_unet")],
    }))
    monkeypatch.setattr(main, "BASE_DIR", tmp_path)
    with TestClient(app) as client:
        _, researcher = make_user(f"model-manager-{suffix}@example.org", "researcher")
        assert client.post("/api/analysis/models/activate", headers=researcher,
                           json={"architecture": "attention_unet"}).status_code == 403
        _, researcher = make_user(f"model-approver-{suffix}@example.org", "admin")
        response = client.post("/api/analysis/models/activate", headers=researcher,
                               json={"architecture": "attention_unet"})
        assert response.status_code == 200, response.text
        selected = json.loads((model_root / "promoted_model.json").read_text())
        history = json.loads((model_root / "model_registry.json").read_text())["history"]
        assert selected["architecture"] == "attention_unet"
        assert selected["version"] == "arcade-attention_unet-20261012T120000Z"
        assert selected["thresholds"] == {"syntax": 0.45, "stenosis": 0.45}
        assert history[0]["previous_architecture"] == "tiny_unet"
        assert history[0]["activated_by"]
