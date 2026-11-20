import base64
import hmac

from fastapi.testclient import TestClient

from app import admin_mfa
from app.main import app
from test_rbac_system import make_user


def test_production_administrator_and_invitation(monkeypatch):
    with TestClient(app) as client:
        _, old_session = make_user("enrollment-test@example.org", "admin")
        _, viewer = make_user("invite-outsider@example.org", "viewer")
        monkeypatch.setenv("COROVISION_ENV", "production")
        monkeypatch.setattr(admin_mfa.time, "time", lambda: 1_700_000_000)
        login = {"email": "enrollment-test@example.org", "password": "secure-pass-1234"}
        assert client.get("/api/auth/me", headers=old_session).status_code == 401
        challenge = client.post("/api/auth/login", json=login).json()
        assert challenge["mfa_required"] and "access_token" not in challenge
        secret = base64.b32decode(challenge["enrollment_key"])
        digest = hmac.digest(secret, (1_700_000_000 // 30).to_bytes(8, "big"), "sha1")
        offset = digest[-1] & 15
        code = f"{(int.from_bytes(digest[offset:offset+4], 'big') & 0x7fffffff) % 1_000_000:06d}"
        login["mfa_code"] = code
        result = client.post("/api/auth/login", json=login)
        assert result.status_code == 200, result.text
        token = {"Authorization": f"Bearer {result.json()['access_token']}"}
        assert client.post("/api/auth/login", json=login).status_code == 401
        assert client.get("/api/auth/me", headers=token).status_code == 200
        payload = {"email": "invited-user@example.org", "password": "A-Unique-Password-42!"}
        url = "/api/admin/invitations"
        assert client.post(url, headers=viewer, json={"email": payload["email"]}).status_code == 403
        assert client.post("/api/auth/register", json=payload).status_code == 403
        invite = client.post(url, headers=token, json={"email": payload["email"]})
        assert invite.status_code == 201
        payload["invitation"] = invite.json()["invitation"]
        assert client.post("/api/auth/register", json={**payload, "email": "wrong@example.org"}).status_code == 403
        assert client.post("/api/auth/register", json=payload).json()["role"] == "viewer"
        # Existing-account validation takes precedence over invitation status.
        assert client.post("/api/auth/register", json=payload).status_code == 409
