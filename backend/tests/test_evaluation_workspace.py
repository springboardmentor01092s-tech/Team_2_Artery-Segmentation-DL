"""Synthetic fixtures only; these experiments never enter the development database."""
import base64
import copy
import io
from uuid import uuid4

import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from test_rbac_system import make_user


def png(value=0):
    stream = io.BytesIO()
    Image.new("L", (8, 8), value).save(stream, format="PNG")
    return base64.b64encode(stream.getvalue()).decode()


def bundle():
    return {
        "name": "Synthetic test fixture", "architecture": "test-unet", "version": "fixture-v1",
        "checkpoint_sha256": "a" * 64, "task": "test_segmentation", "dimension": "2D",
        "dataset": {"name": "synthetic-fixture", "version": "1", "split": "validation",
                    "protocol": "test-only pixel protocol", "counts": {"images": 1},
                    "patient_independence_verified": True},
        "metrics": [{"name": "Dice", "value": .75, "unit": "ratio", "definition": "test overlap", "aggregation": "mean"}],
        "epochs": [{"epoch": 1, "values": {"train_loss": .5, "validation_loss": .6}},
                   {"epoch": 2, "values": {"train_loss": .4, "validation_loss": .5}}],
        "best_epoch": 2, "early_stopping_epoch": 2,
        "samples": [{"id": "test-1", "reference_available": True, "reviewed": True,
                     "artifacts": {"original": "image", "reference": "truth", "prediction": "mask"}}],
        "artifacts": [{"key": key, "format": "png", "data_base64": png(value)}
                      for key, value in [("image", 80), ("truth", 255), ("mask", 255)]],
        "deidentified_research_data": True,
    }


def accounts():
    suffix = uuid4().hex
    return {role: make_user(f"experiment-{role}-{suffix}@example.org", role)[1]
            for role in ("ml_engineer", "researcher", "admin", "viewer", "doctor")}


def test_import_read_export_and_rbac():
    with TestClient(app) as client:
        users = accounts()
        assert client.get("/api/evaluation/workspace").status_code == 401
        assert client.get("/api/evaluation/workspace", headers=users["viewer"]).status_code == 403
        assert client.post("/api/evaluation/workspace", headers=users["researcher"], json=bundle()).status_code == 403
        result = client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=bundle())
        assert result.status_code == 201, result.text
        row = result.json()
        assert row["status"] == "experimental"
        assert row["metrics"][0]["value"] == .75
        assert "data_base64" not in str(row)
        listing = client.get("/api/evaluation/workspace", headers=users["researcher"]).json()
        assert any(r["id"] == row["id"] for r in listing["runs"])
        path = f'/api/evaluation/workspace/{row["id"]}'
        assert client.get(path + "/report", headers=users["researcher"]).json() == row
        assert client.get(path + "/artifacts/image", headers=users["doctor"]).status_code == 403
        image = client.get(path + "/artifacts/image", headers=users["researcher"])
        assert image.status_code == 200 and image.content.startswith(b"\x89PNG")
        assert client.get(path + "/artifacts/not-present", headers=users["researcher"]).status_code == 404
        assert client.post(path + "/review", headers=users["ml_engineer"], json={"decision": "approved", "notes": "test review notes"}).status_code == 403


def test_validation_rejects_bad_metadata_and_preserves_history():
    with TestClient(app) as client:
        users = accounts()
        for mutate in [
            lambda b: b.update(checkpoint_sha256="not-a-hash"),
            lambda b: b["epochs"].append(b["epochs"][0]),
            lambda b: b["samples"][0]["artifacts"].update(prediction="../../secret"),
            lambda b: b.update(confusion_matrix=[[1, 2]], class_labels=["a"]),
            lambda b: b["dataset"].update(counts={"images": -1}),
            lambda b: b.update(deidentified_research_data=False),
        ]:
            bad = bundle(); mutate(bad)
            assert client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=bad).status_code == 422
        first = client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=bundle()).json()
        second = client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=bundle()).json()
        assert first["id"] != second["id"]
        assert client.get(f'/api/evaluation/workspace/{first["id"]}/report', headers=users["researcher"]).json()["metrics"] == first["metrics"]


def test_policy_review_gates_and_immutable_audit():
    with TestClient(app) as client:
        users = accounts()
        data = bundle()
        policy = {"name": "Synthetic test policy", "task": data["task"], "dataset": data["dataset"],
                  "thresholds": [{"metric": "Dice", "minimum": .7}], "review_requirements": "Test-only qualitative and dataset review"}
        assert client.post("/api/evaluation/workspace/policies", headers=users["ml_engineer"], json=policy).status_code == 403
        policy_id = client.post("/api/evaluation/workspace/policies", headers=users["admin"], json=policy).json()["id"]
        data["policy_id"] = policy_id
        row = client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=data).json()
        path = f'/api/evaluation/workspace/{row["id"]}/review'
        decision = {"decision": "approved", "notes": "Synthetic independent reviewer decision",
                    "visual_review_completed": True, "dataset_audit_completed": True}
        assert client.post(path, headers=users["admin"], json=decision).status_code == 409
        assert client.post(path, headers=users["ml_engineer"], json={"decision": "validation_pending", "notes": "Submitted test candidate"}).status_code == 200
        missing = {**decision, "visual_review_completed": False}
        assert client.post(path, headers=users["admin"], json=missing).status_code == 409
        assert client.post(path, headers=users["admin"], json=decision).status_code == 409
        sample_path = f'/api/evaluation/workspace/{row["id"]}/samples/test-1/review'
        assert client.post(sample_path, headers=users["admin"], json={"notes": "Reviewed synthetic reference and prediction"}).status_code == 200
        approved = client.post(path, headers=users["admin"], json=decision)
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "approved"
        assert len(approved.json()["decisions"]) == 2
        retired = client.post(path, headers=users["admin"], json={"decision": "retired", "notes": "Retired test-only candidate"})
        assert retired.status_code == 200 and len(retired.json()["decisions"]) == 3
        # Checkpoints are metadata only; approval never writes the live inference registry.
        assert retired.json()["checkpoint_sha256"] == row["checkpoint_sha256"]


def test_volume_slice_and_geometry_validation():
    with TestClient(app) as client:
        users = accounts()
        data = bundle(); data["dimension"] = "3D"
        stream = io.BytesIO(); np.save(stream, np.arange(4 * 8 * 8).reshape(4, 8, 8).astype("float32"))
        data["artifacts"] = [{"key": key, "format": "npy", "data_base64": base64.b64encode(stream.getvalue()).decode()}
                             for key in ("image", "truth", "mask")]
        assert client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=data).status_code == 422
        data["samples"][0]["spatial_metadata"] = {"spacing": [1, 1, 1], "affine": np.eye(4).tolist(), "coordinate_frame": "test voxel grid"}
        result = client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=data)
        assert result.status_code == 201, result.text
        path = f'/api/evaluation/workspace/{result.json()["id"]}/artifacts/image'
        assert client.get(path + "?slice_index=3", headers=users["researcher"]).status_code == 200
        assert client.get(path + "?slice_index=4", headers=users["researcher"]).status_code == 422
        assert client.get(path, headers=users["viewer"]).status_code == 403


def test_failed_threshold_and_self_approval_are_denied():
    with TestClient(app) as client:
        users = accounts(); data = bundle()
        policy = {"name": "High test threshold", "task": data["task"], "dataset": data["dataset"],
                  "thresholds": [{"metric": "Dice", "minimum": .99}], "review_requirements": "Independent reference review"}
        data["policy_id"] = client.post("/api/evaluation/workspace/policies", headers=users["admin"], json=policy).json()["id"]
        row = client.post("/api/evaluation/workspace", headers=users["ml_engineer"], json=data).json()
        path = f'/api/evaluation/workspace/{row["id"]}/review'
        client.post(path, headers=users["ml_engineer"], json={"decision": "validation_pending", "notes": "Submit test candidate"})
        assert client.post(path, headers=users["admin"], json={"decision": "approved", "notes": "Test decision blocked", "visual_review_completed": True, "dataset_audit_completed": True}).status_code == 409
        own = client.post("/api/evaluation/workspace", headers=users["admin"], json=bundle()).json()
        own_path = f'/api/evaluation/workspace/{own["id"]}/review'
        client.post(own_path, headers=users["admin"], json={"decision": "validation_pending", "notes": "Own test submission"})
        assert client.post(own_path, headers=users["admin"], json={"decision": "rejected", "notes": "Own decision blocked"}).status_code == 403
