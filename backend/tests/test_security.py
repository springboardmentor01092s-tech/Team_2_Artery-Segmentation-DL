"""Security tests: authentication, tokens, roles, input safety, and known weaknesses."""
import base64
import json
import os
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app import auth

PW = "Test-pass-123"


def _b64(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


# ------------------------------------------------------------------ no or bad token
PROTECTED = [
    ("GET", "/auth/me"),
    ("GET", "/cases"),
    ("POST", "/cases"),
    ("GET", "/cases/1"),
    ("PUT", "/cases/1"),
    ("DELETE", "/cases/1"),
    ("POST", "/cases/1/upload"),
    ("POST", "/cases/1/preprocess"),
    ("POST", "/cases/1/segment"),
    ("POST", "/cases/1/stenosis-pipeline"),
    ("GET", "/cases/1/results"),
    ("GET", "/cases/1/report"),
    ("GET", "/cases/results/summary"),
    ("GET", "/cases/model-metrics"),
    ("GET", "/cases/model-comparison"),
]


@pytest.mark.parametrize("method,url", PROTECTED)
def test_endpoints_reject_requests_without_token(client, method, url):
    r = client.request(method, url)
    assert r.status_code == 401, f"{method} {url} returned {r.status_code}"


def test_garbage_token_rejected(client):
    r = client.get("/cases", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401


def test_token_signed_with_wrong_key_rejected(client, users):
    forged = jwt.encode(
        {"sub": users["admin"]["email"], "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "some-other-secret",
        algorithm="HS256",
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_unsigned_alg_none_token_rejected(client, users):
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    token = f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64({'sub': users['admin']['email'], 'exp': exp})}."
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_expired_token_rejected(client, users):
    expired = jwt.encode(
        {"sub": users["clinician"]["email"], "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
        auth.SECRET_KEY,
        algorithm=auth.ALGORITHM,
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_token_for_unknown_user_rejected(client):
    token = auth.create_access_token({"sub": "ghost@test.example", "role": "admin"})
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# ------------------------------------------------------------------ privilege escalation
def test_cannot_register_as_admin(client):
    r = client.post(
        "/auth/register",
        json={"name": "Evil", "email": "evil@test.example", "password": PW, "role": "admin"},
    )
    assert r.status_code == 400


def test_responses_never_expose_password_hash(client, users):
    body = client.get("/auth/me", headers=users["clinician"]["headers"]).text.lower()
    assert "password" not in body


# ------------------------------------------------------------------ role permissions
def test_other_clinician_cannot_see_or_change_a_case(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "sec-private")
    other = users["clinician2"]["headers"]

    assert client.get(f"/cases/{case['id']}", headers=other).status_code == 404
    assert case["id"] not in [c["id"] for c in client.get("/cases", headers=other).json()]
    assert (
        client.put(f"/cases/{case['id']}", json={"patient_id": "hacked"}, headers=other).status_code
        == 403
    )
    assert client.delete(f"/cases/{case['id']}", headers=other).status_code == 403


def test_researcher_is_read_only(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "sec-readonly")
    h = users["researcher"]["headers"]

    assert client.get(f"/cases/{case['id']}", headers=h).status_code == 200
    assert client.post("/cases", json={"patient_id": "nope"}, headers=h).status_code == 403
    assert (
        client.put(f"/cases/{case['id']}", json={"patient_id": "x"}, headers=h).status_code == 403
    )
    assert client.delete(f"/cases/{case['id']}", headers=h).status_code == 403
    assert (
        client.post(
            f"/cases/{case['id']}/upload",
            files={"file": ("a.png", b"x", "image/png")},
            headers=h,
        ).status_code
        == 403
    )
    assert client.post(f"/cases/{case['id']}/preprocess", headers=h).status_code == 403
    assert client.post(f"/cases/{case['id']}/stenosis-pipeline", headers=h).status_code == 403


def test_data_scientist_can_view_but_not_edit(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "sec-ds")
    h = users["data_scientist"]["headers"]

    assert client.get(f"/cases/{case['id']}", headers=h).status_code == 200
    assert client.post("/cases", json={"patient_id": "nope"}, headers=h).status_code == 403
    assert (
        client.put(f"/cases/{case['id']}", json={"patient_id": "x"}, headers=h).status_code == 403
    )
    assert client.delete(f"/cases/{case['id']}", headers=h).status_code == 403


def test_admin_can_edit_and_delete_any_case(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "sec-admin")
    h = users["admin"]["headers"]

    r = client.put(f"/cases/{case['id']}", json={"patient_id": "sec-admin-2", "age": 70}, headers=h)
    assert r.status_code == 200
    assert client.delete(f"/cases/{case['id']}", headers=h).status_code == 204


# ------------------------------------------------------------------ input safety
def test_sql_injection_in_login_does_not_log_in(client):
    r = client.post("/auth/login", data={"username": "' OR '1'='1", "password": "x"})
    assert r.status_code == 401


def test_sql_injection_text_is_stored_as_plain_text(client, users):
    h = users["clinician"]["headers"]
    evil = "x'); DROP TABLE cases;--"
    r = client.post("/cases", json={"patient_id": evil}, headers=h)
    assert r.status_code == 201
    assert r.json()["patient_id"] == evil
    assert client.get("/cases", headers=h).status_code == 200  # table still exists


@pytest.mark.parametrize("filename", ["scan.exe", "scan.png.exe", "script.js", "scan.svg", "scan"])
def test_upload_rejects_dangerous_file_types(client, users, make_case, filename):
    case = make_case(users["clinician"]["headers"], "sec-upload")
    r = client.post(
        f"/cases/{case['id']}/upload",
        files={"file": (filename, b"data", "application/octet-stream")},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 400


def test_upload_path_traversal_name_is_not_used_for_storage(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "sec-traversal")
    # a valid image extension with a traversal-style name must be stored under a safe generated name
    r = client.post(
        f"/cases/{case['id']}/upload",
        files={"file": ("../../evil.png", b"\x89PNG\r\n", "image/png")},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 200
    stored = r.json()["image_path"]
    assert ".." not in stored and "/" not in stored and "\\" not in stored


# ------------------------------------------------------------------ known weaknesses
# These tests are marked xfail on purpose. They document real weaknesses in the current app.
# They show as "xfailed" now and will show "XPASS" once you fix the issue.
@pytest.mark.xfail(reason="SECRET_KEY is hard-coded in auth.py. Move it to an environment variable.")
def test_secret_key_is_not_the_default():
    assert auth.SECRET_KEY != "change-this-secret-key-later"


@pytest.mark.xfail(reason="Files in /uploads can be opened without logging in.")
def test_uploaded_files_require_authentication(client):
    os.makedirs("uploads", exist_ok=True)
    probe = os.path.join("uploads", "test_probe_security.txt")
    with open(probe, "w") as f:
        f.write("probe")
    try:
        r = client.get("/uploads/test_probe_security.txt")
        assert r.status_code in (401, 403)
    finally:
        if os.path.exists(probe):
            os.remove(probe)


@pytest.mark.xfail(reason="No rate limiting on login, so passwords can be guessed repeatedly.")
def test_login_is_rate_limited(client):
    last = None
    for _ in range(12):
        last = client.post("/auth/login", data={"username": "nobody@test.example", "password": "x"})
    assert last.status_code == 429


@pytest.mark.xfail(reason="Very weak passwords (one character) are accepted at registration.")
def test_weak_password_rejected(client):
    r = client.post(
        "/auth/register",
        json={"name": "Weak", "email": "weak@test.example", "password": "a", "role": "clinician"},
    )
    assert r.status_code in (400, 422)