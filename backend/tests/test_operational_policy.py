from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from app import main
from app.main import app
from test_rbac_system import make_user


def grant(client, admin, user_id, permission, enabled=True):
    return client.post(f"/api/admin/users/{user_id}/operational-grant", headers=admin,
                       json={"permission": permission, "enabled": enabled,
                             "reason": "Verified authorization for this scoped operational workflow."})


def test_technician_analysis_requires_separate_grant_and_case_edit(monkeypatch):
    monkeypatch.setattr(main, "models_ready", lambda: False)
    with TestClient(app) as client:
        tech, tech_headers = make_user("tech-actions@example.org", "technician")
        _, admin = make_user("grant-actions@example.org", "admin")
        _, doctor = make_user("doctor-actions@example.org", "doctor")
        case = client.post("/api/cases", headers=doctor, json={"case_code": "ACTIONS-CASE"}).json()
        image = BytesIO(); Image.new("L", (64, 64), 100).save(image, format="PNG")
        uploaded = client.post(f"/api/cases/{case['id']}/images", headers=doctor,
                               files={"file": ("study.png", image.getvalue(), "image/png")})
        assert uploaded.status_code == 201
        path = f"/api/images/{uploaded.json()['id']}/analyze"
        assert client.post(path, headers=tech_headers).status_code == 403
        assert grant(client, admin, tech["id"], "analysis:run").status_code == 200
        assert client.post(path, headers=tech_headers).status_code == 404
        assert client.post(f"/api/cases/{case['id']}/access", headers=doctor,
                           json={"user_email_or_id": tech["email"], "access_level": "read"}).status_code == 201
        assert client.post(path, headers=tech_headers).status_code == 403
        assert client.get(f"/api/cases/{case['id']}", headers=tech_headers).json()["permissions"]["can_run_analysis"] is False
        assert client.post(f"/api/cases/{case['id']}/access", headers=doctor,
                           json={"user_email_or_id": tech["email"], "access_level": "edit"}).status_code == 201
        assert client.get(f"/api/cases/{case['id']}", headers=tech_headers).json()["permissions"]["can_run_analysis"] is True
        assert client.post(path, headers=tech_headers).status_code == 503  # Authorized; no real inference.
        assert grant(client, admin, tech["id"], "analysis:run", False).status_code == 200
        assert client.post(path, headers=tech_headers).status_code == 403
        assert client.post(f"/api/cases/{case['id']}/review", headers=tech_headers,
                           json={"decision": "approved"}).status_code == 403


def test_admin_operational_grants_cannot_be_self_approved_or_bypass_resources():
    with TestClient(app) as client:
        target, target_headers = make_user("target-actions@example.org", "admin")
        _, approver = make_user("approver-actions@example.org", "admin")
        _, researcher = make_user("research-actions@example.org", "researcher")
        assert client.post("/api/cases", headers=target_headers, json={"case_code": "ADMIN-CASE"}).status_code == 403
        assert grant(client, target_headers, target["id"], "case:create").status_code == 403
        assert grant(client, approver, target["id"], "case:create").status_code == 200
        created = client.post("/api/cases", headers=target_headers, json={"case_code": "ADMIN-CASE"})
        assert created.status_code == 201
        assert client.post("/api/cases", headers=target_headers, json={"case_code": "ADMIN-CASE"}).status_code == 409
        case_id = created.json()["id"]
        assert created.json()["permissions"]["can_upload"] is False
        assert created.json()["permissions"]["can_run_analysis"] is False
        assert client.post(f"/api/cases/{case_id}/images", headers=target_headers,
                           files={"file": ("x.png", b"not-read-before-authorization", "image/png")}).status_code == 403
        assert grant(client, researcher, target["id"], "case:upload").status_code == 403
        assert grant(client, approver, target["id"], "case:upload").status_code == 200
        assert client.get(f"/api/cases/{case_id}", headers=target_headers).json()["permissions"]["can_upload"] is True
        assert grant(client, approver, target["id"], "case:create", False).status_code == 200
        assert client.post("/api/cases", headers=target_headers, json={"case_code": "ADMIN-CASE-2"}).status_code == 403


def test_role_changes_clear_old_operational_grants():
    with TestClient(app) as client:
        target, technician = make_user("role-change-actions@example.org", "technician")
        _, admin = make_user("role-change-approver@example.org", "admin")
        assert grant(client, admin, target["id"], "analysis:run").status_code == 200
        assert "analysis:run" in client.get("/api/auth/me", headers=technician).json()["permissions"]
        assert client.post(f"/api/admin/users/{target['id']}/role", headers=admin, json={"role": "ml_engineer"}).status_code == 200
        assert client.post(f"/api/admin/users/{target['id']}/role", headers=admin, json={"role": "technician"}).status_code == 200
        assert "analysis:run" not in client.get("/api/auth/me", headers=technician).json()["permissions"]
