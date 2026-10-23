from fastapi.testclient import TestClient
from app.main import app
from test_rbac_system import make_user


def test_admin_clinical_access_preserves_case_scope():
    with TestClient(app) as client:
        admin, headers = make_user("admin-clinical@test.org", "admin")
        _, clinician_headers = make_user("owner-clinical@test.org", "clinician")
        permissions = client.get("/api/auth/me", headers=headers).json()["permissions"]
        assert {"case:create", "case:upload", "analysis:run", "analysis:export", "clinical_review:create"} <= set(permissions)
        own = client.post("/api/cases", headers=headers, json={"case_code": "ADMIN-CLINICAL"})
        assert own.status_code == 201
        case = own.json()
        assert case["permissions"]["can_review"]
        review = client.post(f"/api/cases/{case['id']}/review", headers=headers,
                             json={"decision": "reviewed", "stenosis_severity": "mild"})
        assert review.status_code == 201
        assert review.json()["reviews"][0]["reviewer_id"] == admin["id"]
        other = client.post("/api/cases", headers=clinician_headers, json={"case_code": "OTHER-CLINICAL"}).json()
        assert client.post(f"/api/cases/{other['id']}/review", headers=headers,
                           json={"decision": "reviewed"}).status_code == 404


def test_multiple_intended_tasks_saved_and_reloaded():
    with TestClient(app) as client:
        _, headers = make_user("multi-task-clinician@test.org", "clinician")
        tasks = ["artery_segmentation", "stenosis_localization"]
        response = client.post("/api/cases", headers=headers, json={
            "case_code": "MULTI-TASK", "modality": "XCA", "intended_tasks": tasks,
        })
        assert response.status_code == 201
        case = response.json()
        assert case["intended_tasks"] == tasks
        assert client.get(f"/api/cases/{case['id']}", headers=headers).json()["intended_tasks"] == tasks
        assert client.post("/api/cases", headers=headers, json={
            "case_code": "EMPTY-TASK", "intended_tasks": [],
        }).status_code == 422
