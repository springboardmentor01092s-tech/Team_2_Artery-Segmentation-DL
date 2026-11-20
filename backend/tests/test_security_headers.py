import importlib
import os

from fastapi.testclient import TestClient


def test_security_headers_present_on_api_and_frontend(client=None):
    from app.main import app
    with TestClient(app) as c:
        for path in ("/api/health", "/"):
            r = c.get(path)
            csp = r.headers.get("content-security-policy", "")
            assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp and "object-src 'none'" in csp
            assert r.headers.get("x-frame-options") == "DENY"
            assert r.headers.get("x-content-type-options") == "nosniff"
            assert "strict-transport-security" not in r.headers  # plain HTTP locally


def test_hsts_only_behind_https_proxy():
    from app.main import app
    with TestClient(app) as c:
        r = c.get("/api/health", headers={"X-Forwarded-Proto": "https"})
        assert r.headers.get("strict-transport-security", "").startswith("max-age=")


def test_api_docs_hidden_in_production(monkeypatch):
    from app import operations
    monkeypatch.setenv("COROVISION_ENV", "production")
    monkeypatch.delenv("CV_PUBLIC_API_DOCS", raising=False)
    assert operations.api_docs_enabled() is False
    monkeypatch.setenv("CV_PUBLIC_API_DOCS", "1")
    assert operations.api_docs_enabled() is True
    monkeypatch.setenv("COROVISION_ENV", "development")
    assert operations.api_docs_enabled() is True
