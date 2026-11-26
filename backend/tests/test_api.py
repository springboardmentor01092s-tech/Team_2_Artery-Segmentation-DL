"""API tests: status codes, validation and error responses."""
import pytest

PW = "Test-pass-123"


# ------------------------------------------------------------------ basics
def test_root_is_running(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "running" in r.json()["message"].lower()


# ------------------------------------------------------------------ register
def test_register_returns_user_without_password(client):
    r = client.post(
        "/auth/register",
        json={"name": "Reg One", "email": "reg1@test.example", "password": PW, "role": "researcher"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "reg1@test.example"
    assert body["role"] == "researcher"
    assert "password" not in body and "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    payload = {"name": "Dup", "email": "dup@test.example", "password": PW, "role": "clinician"}
    assert client.post("/auth/register", json=payload).status_code == 201
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 400
    assert "already" in r.json()["detail"].lower()


def test_register_invalid_role_rejected(client):
    r = client.post(
        "/auth/register",
        json={"name": "X", "email": "badrole@test.example", "password": PW, "role": "superuser"},
    )
    assert r.status_code == 400


def test_register_invalid_email_rejected(client):
    r = client.post(
        "/auth/register",
        json={"name": "X", "email": "not-an-email", "password": PW, "role": "clinician"},
    )
    assert r.status_code == 422


def test_register_missing_fields_rejected(client):
    r = client.post("/auth/register", json={"email": "missing@test.example"})
    assert r.status_code == 422


# ------------------------------------------------------------------ login
def test_login_returns_bearer_token(client, users):
    r = client.post(
        "/auth/login", data={"username": users["clinician"]["email"], "password": PW}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_wrong_password(client, users):
    r = client.post(
        "/auth/login", data={"username": users["clinician"]["email"], "password": "wrong"}
    )
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/login", data={"username": "nobody@test.example", "password": PW})
    assert r.status_code == 401


def test_me_returns_current_user(client, users):
    r = client.get("/auth/me", headers=users["clinician"]["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == users["clinician"]["email"]


# ------------------------------------------------------------------ cases
def test_create_case(client, users):
    r = client.post(
        "/cases",
        json={"patient_id": "api-1", "age": 55, "gender": "Male", "anatomical_region": "LAD"},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 201
    body = r.json()
    assert body["patient_id"] == "api-1"
    assert body["analysis_status"] == "Pending"
    assert body["image_path"] is None


def test_create_case_requires_patient_id(client, users):
    r = client.post("/cases", json={"age": 30}, headers=users["clinician"]["headers"])
    assert r.status_code == 422


def test_create_case_rejects_text_age(client, users):
    r = client.post(
        "/cases",
        json={"patient_id": "api-bad-age", "age": "abc"},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 422


def test_get_case_and_list(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-get")
    r = client.get(f"/cases/{case['id']}", headers=users["clinician"]["headers"])
    assert r.status_code == 200
    assert r.json()["patient_id"] == "api-get"

    lst = client.get("/cases", headers=users["clinician"]["headers"])
    assert lst.status_code == 200
    assert any(c["id"] == case["id"] for c in lst.json())


def test_get_unknown_case_is_404(client, users):
    r = client.get("/cases/987654", headers=users["clinician"]["headers"])
    assert r.status_code == 404


def test_update_case(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-upd")
    r = client.put(
        f"/cases/{case['id']}",
        json={"patient_id": "api-upd", "age": 61, "gender": "Female"},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 200
    assert r.json()["age"] == 61


def test_delete_case_then_404(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-del")
    r = client.delete(f"/cases/{case['id']}", headers=users["clinician"]["headers"])
    assert r.status_code == 204
    again = client.get(f"/cases/{case['id']}", headers=users["clinician"]["headers"])
    assert again.status_code == 404


# ------------------------------------------------------------------ uploads and analysis input checks
def test_upload_rejects_non_image(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-badfile")
    r = client.post(
        f"/cases/{case['id']}/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 400
    assert "png or jpg" in r.json()["detail"].lower()


def test_preprocess_needs_a_scan(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-noscan-1")
    r = client.post(f"/cases/{case['id']}/preprocess", headers=users["clinician"]["headers"])
    assert r.status_code == 400
    assert "upload a scan" in r.json()["detail"].lower()


def test_segment_rejects_unknown_task(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-task")
    r = client.post(
        f"/cases/{case['id']}/segment",
        params={"task": "banana"},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 400


def test_pipeline_needs_a_scan(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-noscan-2")
    r = client.post(
        f"/cases/{case['id']}/stenosis-pipeline", headers=users["clinician"]["headers"]
    )
    assert r.status_code == 400


def test_report_rejects_unknown_format(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-fmt")
    r = client.get(
        f"/cases/{case['id']}/report",
        params={"format": "docx"},
        headers=users["clinician"]["headers"],
    )
    assert r.status_code == 400


def test_report_needs_a_scan(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-report-noscan")
    r = client.get(f"/cases/{case['id']}/report", headers=users["clinician"]["headers"])
    assert r.status_code == 400


def test_results_summary_and_saved_results_empty_for_new_case(client, users, make_case):
    case = make_case(users["clinician"]["headers"], "api-results")
    assert client.get("/cases/results/summary", headers=users["clinician"]["headers"]).status_code == 200
    r = client.get(f"/cases/{case['id']}/results", headers=users["clinician"]["headers"])
    assert r.status_code == 200
    assert r.json() == {}


def test_model_comparison_endpoint(client, users):
    r = client.get("/cases/model-comparison", headers=users["clinician"]["headers"])
    assert r.status_code in (200, 404)  # 404 only if weights/model_comparison.json is missing
    if r.status_code == 200:
        assert len(r.json()["models"]) >= 2


def test_model_metrics_endpoint(client, users):
    r = client.get("/cases/model-metrics", headers=users["clinician"]["headers"])
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert "accuracy" in r.json()