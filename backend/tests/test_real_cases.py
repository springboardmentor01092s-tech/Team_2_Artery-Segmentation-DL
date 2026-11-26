"""Smoke tests on the REAL database and REAL cases (p001, p002, p003, ...).

Nothing is created, edited or deleted. Report downloads add audit-log rows, and may create
missing preprocessing images or a saved pipeline result for a case.

Run it separately from the other tests:
    $env:TEST_EMAIL="your-login-email"; $env:TEST_PASSWORD="your-password"
    python -m pytest tests/test_real_cases.py -v -s
Optional (re-runs the real pipeline on every case, slower):
    $env:RUN_PIPELINE="1"
"""
import csv
import io
import json
import os

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

EMAIL = os.getenv("TEST_EMAIL")
PASSWORD = os.getenv("TEST_PASSWORD")

pytestmark = pytest.mark.skipif(
    not (EMAIL and PASSWORD),
    reason="set TEST_EMAIL and TEST_PASSWORD to test the real cases",
)


@pytest.fixture(scope="module")
def real():
    saved = app.dependency_overrides.pop(get_db, None)  # make sure the real database is used
    with TestClient(app) as c:
        r = c.post("/auth/login", data={"username": EMAIL, "password": PASSWORD})
        assert r.status_code == 200, "login failed: check TEST_EMAIL and TEST_PASSWORD"
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        cases = c.get("/cases", headers=headers).json()
        yield c, headers, cases
    if saved is not None:
        app.dependency_overrides[get_db] = saved


def test_real_cases_exist(real):
    c, h, cases = real
    print("\nreal cases:", [x["patient_id"] for x in cases])
    assert len(cases) >= 1, "no cases found for this login"


def test_each_case_loads(real):
    c, h, cases = real
    for case in cases:
        r = c.get(f"/cases/{case['id']}", headers=h)
        assert r.status_code == 200, f"case {case['patient_id']}: {r.status_code}"
        assert r.json()["patient_id"] == case["patient_id"]


def test_each_scan_image_can_be_opened(real):
    c, h, cases = real
    for case in cases:
        if not case["image_path"]:
            continue
        r = c.get(f"/uploads/{case['image_path']}")
        assert r.status_code == 200, f"scan of {case['patient_id']} not found"
        assert r.headers["content-type"].startswith("image/")


def test_each_case_has_saved_results(real):
    c, h, cases = real
    summary = c.get("/cases/results/summary", headers=h).json()
    for case in cases:
        if not case["image_path"]:
            continue
        r = c.get(f"/cases/{case['id']}/results", headers=h)
        assert r.status_code == 200
        print(
            f"\n{case['patient_id']}: saved results = {sorted(r.json().keys())}, "
            f"summary = {summary.get(str(case['id']))}"
        )


def test_reports_for_every_real_case(real):
    c, h, cases = real
    checked = 0
    for case in cases:
        if not case["image_path"]:
            continue
        pid, cid = case["patient_id"], case["id"]

        pdf = c.get(f"/cases/{cid}/report", params={"format": "pdf"}, headers=h)
        assert pdf.status_code == 200, f"{pid}: pdf returned {pdf.status_code} {pdf.text[:200]}"
        assert pdf.content.startswith(b"%PDF"), f"{pid}: not a valid PDF"

        js = c.get(f"/cases/{cid}/report", params={"format": "json"}, headers=h)
        assert js.status_code == 200, f"{pid}: json returned {js.status_code}"
        data = json.loads(js.text)
        assert data["patient"]["patient_id"] == pid
        assert data["summary"]["regions_flagged"] == len(data["stenosis_regions"])
        assert len(data["history"]) >= 1, f"{pid}: processing history is empty"

        cs = c.get(f"/cases/{cid}/report", params={"format": "csv"}, headers=h)
        assert cs.status_code == 200, f"{pid}: csv returned {cs.status_code}"
        rows = list(csv.DictReader(io.StringIO(cs.text)))
        expected_rows = max(len(data["stenosis_regions"]), 1)
        assert len(rows) == expected_rows, f"{pid}: csv has {len(rows)} rows, json has {expected_rows}"

        print(
            f"\n{pid}: pdf {len(pdf.content) // 1024} KB, "
            f"{data['summary']['regions_flagged']} region(s), "
            f"highest narrowing {data['summary']['highest_narrowing_pct']}% "
            f"({data['summary']['highest_severity']})"
        )
        checked += 1
    assert checked >= 1, "no case with a scan to test"


@pytest.mark.skipif(
    os.getenv("RUN_PIPELINE") != "1", reason="set RUN_PIPELINE=1 to re-run the real pipeline"
)
def test_pipeline_rerun_on_real_cases(real):
    c, h, cases = real
    for case in cases:
        if not case["image_path"]:
            continue
        r = c.post(f"/cases/{case['id']}/stenosis-pipeline", headers=h)
        if r.status_code == 403:
            pytest.skip("this login is not allowed to run the pipeline")
        assert r.status_code == 200, f"{case['patient_id']}: {r.status_code} {r.text[:200]}"
        body = r.json()
        assert len(body["stages_done"]) >= 8
        print(f"\n{case['patient_id']}: {len(body['candidates'])} candidate(s)")