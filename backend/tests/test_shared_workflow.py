from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.main import app
from test_rbac_system import make_user


def test_technician_to_approved_report_and_recoverable_delete(monkeypatch):
    monkeypatch.setenv("CV_LOCAL_DEMO_SHARING", "1")
    source = BytesIO()
    Image.new("L", (64, 64), 100).save(source, format="PNG")
    monkeypatch.setattr(main, "models_ready", lambda: True)
    monkeypatch.setattr(main, "analyze", lambda path, spacing=None: (
        source.getvalue(), 18, 3,
        {"centerline_paths": [], "branch_points": [], "endpoint_points": [], "quality_flags": []},
        None, None, None, None, {"calibration": "unavailable"}, source.getvalue(),
    ))

    with TestClient(app) as client:
        _, technician = make_user("technician.demo@example.com", "technician")
        _, researcher = make_user("researcher.demo@example.com", "researcher")
        _, doctor = make_user("doctor.demo@example.com", "doctor")
        clinician_user, clinician = make_user("radiologist.demo@example.com", "clinician")
        _, viewer = make_user("viewer.demo@example.com", "viewer")
        _, admin = make_user("admin-workflow@example.com", "admin")

        created = client.post("/api/cases", headers=technician, json={"case_code": "WORKFLOW-DEMO-001"})
        assert created.status_code == 201
        case_id = created.json()["id"]
        assert created.json()["workflow_status"] == "draft"
        assert any(task["case_id"] == case_id for task in client.get("/api/tasks", headers=technician).json())

        upload = client.post(f"/api/cases/{case_id}/images", headers=technician,
                             files={"file": ("study.png", source.getvalue(), "image/png")})
        assert upload.status_code == 201
        image_id = upload.json()["id"]
        research_case = client.get(f"/api/cases/{case_id}", headers=researcher).json()
        assert research_case["workflow_status"] == "ready_for_analysis"
        assert research_case["processing_status"] == "completed"
        # Read sharing permits viewing, not a new analysis run; explicitly delegate edit.
        assert research_case["permissions"]["can_run_analysis"] is False
        assert client.post(f"/api/cases/{case_id}/access", headers=technician,
                           json={"user_email_or_id": "researcher.demo@example.com", "access_level": "edit"}).status_code == 201
        assert any(task["case_id"] == case_id and task["view"] == "analysis"
                   for task in client.get("/api/tasks", headers=researcher).json())

        analysis = client.post(f"/api/images/{image_id}/analyze", headers=researcher)
        assert analysis.status_code == 200
        assert client.get(f"/api/cases/{case_id}", headers=doctor).json()["workflow_status"] == "pending_review"
        assert any(task["case_id"] == case_id for task in client.get("/api/tasks", headers=doctor).json())

        review = client.post(f"/api/cases/{case_id}/review", headers=doctor,
                             json={"decision": "reviewed", "notes": "Research image reviewed"})
        assert review.status_code == 201
        assert review.json()["workflow_status"] == "reviewed"
        submitted = client.post(f"/api/cases/{case_id}/reports/submit", headers=doctor)
        assert submitted.status_code == 201, submitted.text
        assert submitted.json()["version"] == 1
        assert client.get(f"/api/cases/{case_id}/reports/1", headers=viewer).status_code == 404

        assert client.post(f"/api/cases/{case_id}/reports/1/decision", headers=clinician,
                           json={"decision": "approved"}).status_code == 403
        grant = client.post(f"/api/admin/users/{clinician_user['id']}/report-approval", headers=admin,
                            json={"enabled": True})
        assert grant.status_code == 200
        assert grant.json()["can_approve_reports"] is True
        assert any(task["case_id"] == case_id for task in client.get("/api/tasks", headers=clinician).json())
        approved = client.post(f"/api/cases/{case_id}/reports/1/decision", headers=clinician,
                               json={"decision": "approved", "notes": "Approved for this research workflow"})
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
        viewer_case = client.get(f"/api/cases/{case_id}", headers=viewer).json()
        assert (viewer_case["workflow_status"], viewer_case["report_status"]) == ("complete", "approved")
        assert client.get(f"/api/cases/{case_id}/reports/1", headers=viewer).status_code == 200
        assert client.get("/api/notifications", headers=viewer).status_code == 200

        assert client.delete(f"/api/cases/{case_id}", headers=viewer).status_code == 403
        assert client.delete(f"/api/cases/{case_id}", headers=technician).status_code == 200
        assert client.get(f"/api/cases/{case_id}", headers=doctor).status_code == 404
        assert any(item["id"] == case_id for item in client.get("/api/admin/trash", headers=admin).json())
        assert client.post(f"/api/admin/trash/{case_id}/restore", headers=admin).status_code == 200
        assert client.get(f"/api/cases/{case_id}", headers=viewer).status_code == 200
