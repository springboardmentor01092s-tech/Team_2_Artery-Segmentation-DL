from fastapi.testclient import TestClient
from app.main import app
from test_rbac_system import make_user


def test_standard_registration_and_scoped_access_requests():
    with TestClient(app) as client:
        registered = client.post("/api/auth/register", json={"email": "standard-policy@example.org", "password": "secure-password-123", "role": "admin"})
        assert registered.status_code == 201
        assert registered.json()["role"] == "viewer"
        token = client.post("/api/auth/login", json={"email": "standard-policy@example.org", "password": "secure-password-123"}).json()["access_token"]
        standard = {"Authorization": f"Bearer {token}"}
        assert "comparison" not in client.get("/api/analysis/status", headers=standard).json()
        assert client.get("/api/dashboard/analytics", headers=standard).json()["validation_performance"] == {}
        assert client.post("/api/cases", headers=standard, json={"case_code": "NOT-AUTHORIZED"}).status_code == 403
        body = {"requested_role": "researcher", "reason": "Approved institutional research project; eligibility verification required."}
        pending = client.post("/api/auth/access-requests", headers=standard, json=body)
        assert pending.status_code == 201
        request_id = pending.json()["id"]
        assert client.get("/api/auth/me", headers=standard).json()["role"] == "viewer"
        assert client.post("/api/auth/access-requests", headers=standard, json=body).status_code == 409
        _, other = make_user("other-policy@example.org", "viewer")
        assert client.get("/api/auth/access-requests", headers=other).json() == []
        assert client.get("/api/admin/access-requests", headers=other).status_code == 403
        assert client.post(f"/api/admin/access-requests/{request_id}/decision", headers=standard,
                           json={"decision": "approved", "notes": "Self approval must not work."}).status_code == 403
        _, admin = make_user("policy-approver@example.org", "admin")
        decision = client.post(f"/api/admin/access-requests/{request_id}/decision", headers=admin,
                               json={"decision": "approved", "notes": "Verified research authorization and institutional affiliation manually."})
        assert decision.status_code == 200, decision.text
        assert client.get("/api/auth/me", headers=standard).json()["role"] == "researcher"
        assert client.get("/api/auth/me", headers=standard).json()["can_approve_reports"] is False
        assert client.post("/api/analysis/models/activate", headers=standard, json={"architecture": "tiny_unet"}).status_code == 403
        assert client.post(f"/api/admin/access-requests/{request_id}/decision", headers=admin,
                           json={"decision": "rejected", "notes": "Duplicate decisions must not be allowed."}).status_code == 409
        events = client.get("/api/admin/audit", headers=admin).json()
        assert any(event["action"].startswith("role_request_approved:") for event in events)


def test_admin_cannot_approve_own_request_and_ml_cannot_activate():
    with TestClient(app) as client:
        _, admin = make_user("self-policy@example.org", "admin")
        pending = client.post("/api/auth/access-requests", headers=admin, json={"requested_role": "ml_engineer", "reason": "Verify separate technical access for this administrator account."})
        assert pending.status_code == 201
        assert client.post(f"/api/admin/access-requests/{pending.json()['id']}/decision", headers=admin,
                           json={"decision": "approved", "notes": "This self approval must be rejected."}).status_code == 403
        _, ml = make_user("ml-policy@example.org", "ml_engineer")
        assert client.get("/api/cases", headers=ml).status_code == 403
        assert client.get("/api/analysis/models", headers=ml).json()["can_activate"] is False
        assert client.post("/api/analysis/models/activate", headers=ml, json={"architecture": "tiny_unet"}).status_code == 403
