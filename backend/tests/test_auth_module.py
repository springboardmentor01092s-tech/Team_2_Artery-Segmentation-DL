from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.database import SessionLocal
from app.main import app
from app.models import User
from app.security import hash_password


def register_and_login(client: TestClient, email: str, password: str = "long-password-123"):
    registered = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "display_name": "Test Researcher"},
    )
    assert registered.status_code == 201, registered.text
    token = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]
    return registered.json(), {"Authorization": f"Bearer {token}"}


def test_profile_sessions_password_and_audit():
    with TestClient(app) as client:
        user, headers = register_and_login(client, "profile@example.org")
        profile = client.get("/api/auth/me", headers=headers)
        assert profile.json()["display_name"] == "Test Researcher"
        changed = client.patch(
            "/api/auth/me", headers=headers,
            json={"display_name": "Updated Researcher", "email": "newprofile@example.org",
                  "current_password": "long-password-123"},
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["display_name"] == "Updated Researcher"
        assert changed.json()["email"] == "newprofile@example.org"

        second_token = client.post(
            "/api/auth/login",
            json={"email": "newprofile@example.org", "password": "long-password-123"},
        ).json()["access_token"]
        second_headers = {"Authorization": f"Bearer {second_token}"}
        sessions = client.get("/api/auth/sessions", headers=headers)
        assert sessions.status_code == 200
        assert sum(item["active"] for item in sessions.json()) == 2
        audit = client.get("/api/auth/audit", headers=headers).json()
        assert {"registered", "login", "profile_updated"}.issubset({item["action"] for item in audit})

        changed_password = client.post(
            "/api/auth/change-password", headers=headers,
            json={"current_password": "long-password-123", "new_password": "new-long-password-456"},
        )
        assert changed_password.status_code == 200
        assert client.get("/api/auth/me", headers=headers).status_code == 401
        assert client.get("/api/auth/me", headers=second_headers).status_code == 401
        new_token = client.post(
            "/api/auth/login",
            json={"email": "newprofile@example.org", "password": "new-long-password-456"},
        ).json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        assert client.post("/api/auth/logout", headers=new_headers).status_code == 200
        assert client.get("/api/auth/me", headers=new_headers).status_code == 401


def test_remembered_session_lasts_longer_on_local_demo():
    with TestClient(app) as client:
        register_and_login(client, "remembered@example.org")
        response = client.post(
            "/api/auth/login",
            json={"identifier": "remembered@example.org", "password": "long-password-123", "remember": True},
        )
        assert response.status_code == 200
        expires_at = datetime.fromisoformat(response.json()["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        from app.security import LOCAL_DEMO_SESSIONS
        remaining_days = (expires_at - datetime.now(timezone.utc)).total_seconds() / 86400
        if LOCAL_DEMO_SESSIONS:
            assert 29 < remaining_days < 31
        else:
            assert 0 < remaining_days < 1


def test_admin_role_assignment_and_case_restriction():
    from conftest import authorize_test_researcher
    with TestClient(app) as client:
        researcher, research_headers = register_and_login(client, "roles@example.org")
        authorize_test_researcher("roles@example.org")
        own_case = client.post("/api/cases", headers=research_headers, json={"case_code": "ROLE-CASE"})
        assert own_case.status_code == 201
        with SessionLocal() as db:
            db.add(User(
                email="admin@example.org",
                password_hash=hash_password("admin-long-password"),
                role="admin",
            ))
            db.commit()
        admin_token = client.post(
            "/api/auth/login",
            json={"email": "admin@example.org", "password": "admin-long-password"},
        ).json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        assert client.get("/api/admin/users", headers=research_headers).status_code == 403
        assert client.get("/api/admin/users", headers=admin_headers).status_code == 200
        assert not any(item["id"] == own_case.json()["id"] for item in client.get("/api/cases", headers=admin_headers).json())
        changed = client.post(
            f"/api/admin/users/{researcher['id']}/role",
            headers=admin_headers, json={"role": "ml_engineer"},
        )
        assert changed.status_code == 200
        assert changed.json()["role"] == "ml_engineer"
        assert client.get("/api/cases", headers=research_headers).status_code == 403
        model_status = client.get("/api/analysis/status", headers=research_headers)
        assert model_status.status_code == 200
        assert "model_version" in model_status.json()
        assert client.get("/api/admin/audit", headers=admin_headers).status_code == 200
        assert client.post(
            f"/api/admin/users/{researcher['id']}/role",
            headers=admin_headers, json={"role": "clinician"},
        ).status_code == 200
        clinician_cases = client.get("/api/cases", headers=research_headers)
        assert clinician_cases.status_code == 200
        assert [item["id"] for item in clinician_cases.json()] == [own_case.json()["id"]]
        assert client.get("/api/admin/users", headers=research_headers).status_code == 403


def test_repeated_failed_logins_are_temporarily_blocked():
    with TestClient(app) as client:
        register_and_login(client, "throttle@example.org")
        for _ in range(5):
            response = client.post(
                "/api/auth/login",
                json={"email": "throttle@example.org", "password": "wrong-password"},
            )
            assert response.status_code == 401
        blocked = client.post(
            "/api/auth/login",
            json={"email": "throttle@example.org", "password": "long-password-123"},
        )
        assert blocked.status_code == 429
