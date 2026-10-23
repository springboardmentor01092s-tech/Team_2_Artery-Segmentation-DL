from fastapi.testclient import TestClient

from app import auth_ext
from app.main import app


def test_username_and_email_password_login():
    with TestClient(app) as client:
        registered = client.post("/api/auth/register", json={
            "email": "aliases@example.org", "password": "long-password-123",
            "username": "researcher.one",
        })
        assert registered.status_code == 201, registered.text
        for identifier in ("aliases@example.org", "researcher.one"):
            response = client.post("/api/auth/login", json={"identifier": identifier, "password": "long-password-123"})
            assert response.status_code == 200, response.text
        assert client.post("/api/auth/login", json={"identifier": "+919876543210", "password": "long-password-123"}).status_code == 401
        assert client.post("/api/auth/phone/request-code").status_code == 404
        assert client.post("/api/auth/register", json={
            "email": "other@example.org", "password": "long-password-123", "username": "researcher.one",
        }).status_code == 409


def test_email_reset_code_revokes_sessions(monkeypatch):
    sent = []
    monkeypatch.setenv("SMTP_HOST", "smtp.example.org")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.org")
    monkeypatch.setattr(auth_ext, "send_code", lambda destination, code, purpose: sent.append((destination, code)))
    with TestClient(app) as client:
        client.post("/api/auth/register", json={"email": "reset@example.org", "password": "long-password-123"})
        old_token = client.post("/api/auth/login", json={"email": "reset@example.org", "password": "long-password-123"}).json()["access_token"]
        requested = client.post("/api/auth/password-reset/request", json={"contact": "reset@example.org"})
        assert requested.status_code == 200
        assert len(sent) == 1
        bad = client.post("/api/auth/password-reset/confirm", json={
            "contact": "reset@example.org", "code": "000000", "new_password": "new-long-password-456",
        })
        assert bad.status_code == 400
        good = client.post("/api/auth/password-reset/confirm", json={
            "contact": "reset@example.org", "code": sent[0][1], "new_password": "new-long-password-456",
        })
        assert good.status_code == 200, good.text
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"}).status_code == 401
        assert client.post("/api/auth/login", json={"identifier": "reset@example.org", "password": "new-long-password-456"}).status_code == 200
        assert client.post("/api/auth/password-reset/confirm", json={
            "contact": "reset@example.org", "code": sent[0][1], "new_password": "third-long-password-789",
        }).status_code == 400


def test_oauth_state_verified_identity_and_single_use_ticket(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth_ext, "provider_identity", lambda provider, code: ("google-sub-1", "social@example.org", "Social User"))
    with TestClient(app, follow_redirects=False) as client:
        start = client.get("/api/auth/oauth/google/start")
        assert start.status_code == 302
        assert "state=" in start.headers["location"]
        from urllib.parse import parse_qs, urlparse
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        assert client.get("/api/auth/oauth/google/callback", params={"code": "test", "state": "wrong"}).status_code == 400
        callback = client.get("/api/auth/oauth/google/callback", params={"code": "test", "state": state})
        assert callback.status_code == 302
        ticket = parse_qs(urlparse(callback.headers["location"]).query)["auth_ticket"][0]
        exchanged = client.post("/api/auth/oauth/exchange", json={"ticket": ticket})
        assert exchanged.status_code == 200, exchanged.text
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {exchanged.json()['access_token']}"}).json()["email"] == "social@example.org"
        assert client.post("/api/auth/oauth/exchange", json={"ticket": ticket}).status_code == 400


def test_existing_user_can_link_google_then_sign_in(monkeypatch):
    from urllib.parse import parse_qs, urlparse
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth_ext, "provider_identity", lambda provider, code: ("linked-google-sub", "link@example.org", "Linked User"))
    with TestClient(app, follow_redirects=False) as client:
        client.post("/api/auth/register", json={"email": "link@example.org", "password": "long-password-123"})
        token = client.post("/api/auth/login", json={"email": "link@example.org", "password": "long-password-123"}).json()["access_token"]
        link = client.post("/api/auth/oauth/google/link/start", headers={"Authorization": f"Bearer {token}"}, json={})
        assert link.status_code == 200, link.text
        state = parse_qs(urlparse(link.json()["authorization_url"]).query)["state"][0]
        callback = client.get("/api/auth/oauth/google/callback", params={"code": "test", "state": state})
        assert callback.status_code == 302
        assert "oauth_linked=google" in callback.headers["location"]
        assert client.get("/api/auth/social-accounts", headers={"Authorization": f"Bearer {token}"}).json()["providers"] == ["google"]
        start = client.get("/api/auth/oauth/google/start")
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        signed_in = client.get("/api/auth/oauth/google/callback", params={"code": "test", "state": state})
        ticket = parse_qs(urlparse(signed_in.headers["location"]).query)["auth_ticket"][0]
        assert client.post("/api/auth/oauth/exchange", json={"ticket": ticket}).status_code == 200


def test_provider_identity_requires_verified_email(monkeypatch):
    from fastapi import HTTPException

    class Reply:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data

    class FakeClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, **kwargs): return Reply({"access_token": "provider-token"})
        def get(self, url, **kwargs):
            if "googleapis" in url:
                return Reply({"sub": "stable-sub", "email": "google@example.org", "email_verified": False})
            if url.endswith("/emails"):
                return Reply([{"email": "github@example.org", "primary": True, "verified": True}])
            return Reply({"id": 12345, "login": "researcher"})

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth_ext.httpx, "Client", FakeClient)
    try:
        auth_ext.provider_identity("google", "code")
        assert False, "Unverified email must be rejected"
    except HTTPException as exc:
        assert exc.status_code == 400
    try:
        auth_ext.provider_identity("github", "code")
        assert False, "Removed GitHub sign-in must be rejected"
    except HTTPException as exc:
        assert exc.status_code == 400
    assert auth_ext.provider_ready("github") is False
    assert "github" not in auth_ext.capabilities()
