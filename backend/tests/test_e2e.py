"""End-to-end test: the whole workflow on one case, using the real models.

Runs in order: upload, preprocess, segment (artery + stenosis), stenosis pipeline, reports.
"""
import json
import os

import pytest

from app.routers import case_routes

pytestmark = pytest.mark.slow


def test_01_scan_is_uploaded(client, e2e_case):
    r = client.get(f"/cases/{e2e_case['id']}", headers=e2e_case["headers"])
    assert r.status_code == 200
    assert r.json()["image_path"]


def test_02_preprocessing_creates_six_stage_images(client, e2e_case):
    r = client.post(f"/cases/{e2e_case['id']}/preprocess", headers=e2e_case["headers"])
    assert r.status_code == 200, r.text
    stages = r.json()["stages"]
    assert len(stages) == 6
    for s in stages:
        path = os.path.join(case_routes.PROCESSED_DIR, os.path.basename(s["url"]))
        assert os.path.exists(path), f"missing stage image {path}"


def test_03_artery_segmentation(client, e2e_case):
    r = client.post(
        f"/cases/{e2e_case['id']}/segment", params={"task": "syntax"}, headers=e2e_case["headers"]
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["task"] == "syntax"
    assert body["mask_url"] and body["overlay_url"]
    assert "vessel_segments" in body["vessel"]


def test_04_stenosis_segmentation(client, e2e_case):
    r = client.post(
        f"/cases/{e2e_case['id']}/segment", params={"task": "stenosis"}, headers=e2e_case["headers"]
    )
    assert r.status_code == 200, r.text
    assert r.json()["task"] == "stenosis"


def test_05_results_are_saved(client, e2e_case):
    saved = client.get(f"/cases/{e2e_case['id']}/results", headers=e2e_case["headers"]).json()
    assert "syntax" in saved and "stenosis" in saved

    summary = client.get("/cases/results/summary", headers=e2e_case["headers"]).json()
    assert str(e2e_case["id"]) in summary


def test_06_stenosis_pipeline(client, e2e_case):
    r = client.post(
        f"/cases/{e2e_case['id']}/stenosis-pipeline", headers=e2e_case["headers"]
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["stages_done"]) >= 8
    assert isinstance(body["candidates"], list)

    case = client.get(f"/cases/{e2e_case['id']}", headers=e2e_case["headers"]).json()
    assert case["analysis_status"] == "Stenosis pipeline complete"
    assert os.path.exists(case_routes.pipeline_json_path(e2e_case["id"]))


def test_07_pdf_report(client, e2e_case):
    r = client.get(
        f"/cases/{e2e_case['id']}/report", params={"format": "pdf"}, headers=e2e_case["headers"]
    )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content.startswith(b"%PDF")
    assert "attachment" in r.headers["content-disposition"]


def test_08_csv_report(client, e2e_case):
    r = client.get(
        f"/cases/{e2e_case['id']}/report", params={"format": "csv"}, headers=e2e_case["headers"]
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    first_line = r.text.splitlines()[0]
    assert "patient_id" in first_line and "narrowing_pct" in first_line
    assert "e2e-test" in r.text


def test_09_json_report_covers_the_whole_workflow(client, e2e_case):
    r = client.get(
        f"/cases/{e2e_case['id']}/report", params={"format": "json"}, headers=e2e_case["headers"]
    )
    assert r.status_code == 200
    data = json.loads(r.text)
    assert data["patient"]["patient_id"] == "e2e-test"
    assert "stenosis_regions" in data and "summary" in data
    assert len(data["preprocessing"]) == 6
    assert data["disclaimer"]

    actions = [h["action"] for h in data["history"]]
    for expected in ["upload_scan", "preprocess", "segment_syntax", "segment_stenosis", "stenosis_pipeline"]:
        assert expected in actions, f"{expected} missing from processing history: {actions}"


def test_10_researcher_can_download_but_not_run(client, users, e2e_case):
    h = users["researcher"]["headers"]
    assert client.get(f"/cases/{e2e_case['id']}/report", params={"format": "csv"}, headers=h).status_code == 200
    assert client.post(f"/cases/{e2e_case['id']}/stenosis-pipeline", headers=h).status_code == 403