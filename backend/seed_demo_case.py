"""Seed one isolated, synthetic 2D demonstration case through the public API.

This script is for the loopback-only ``compose.demo.yaml`` environment.  It
does not import patient data or historic user databases.  The resulting case is
explicitly marked as synthetic and is suitable only for a software walkthrough.
"""

import json
import os
import time
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image, ImageDraw


CASE_CODE = "DEMO-INTEGRATED-SYNTHETIC"
DEMO_URL = os.getenv("DEMO_BASE_URL", "http://127.0.0.1:8000")
CREDS_PATH = Path(os.getenv("DEMO_CREDENTIALS_PATH", "demo-credentials.json"))


def synthetic_png() -> bytes:
    """Create known non-clinical geometry; it is never presented as angiography."""
    image = Image.new("L", (512, 512), color=230)
    draw = ImageDraw.Draw(image)
    draw.text((18, 18), "SYNTHETIC SOFTWARE FIXTURE - NOT PATIENT DATA", fill=30)
    draw.line([(68, 350), (150, 270), (235, 230), (322, 190), (440, 132)], fill=45, width=18)
    draw.line([(235, 230), (276, 310), (360, 380)], fill=65, width=10)
    draw.ellipse((305, 173, 341, 209), fill=175)
    payload = BytesIO()
    image.save(payload, format="PNG")
    return payload.getvalue()


def main() -> None:
    if not CREDS_PATH.is_file():
        raise SystemExit("Run seed_demo_accounts.py before seed_demo_case.py")
    credentials = json.loads(CREDS_PATH.read_text())
    account = next((item for item in credentials.get("accounts", [])
                    if item.get("email") == "researcher.demo@example.com"), None)
    if account is None:
        raise SystemExit("The isolated demo researcher is unavailable")
    with httpx.Client(base_url=DEMO_URL, timeout=180) as client:
        ready_by = time.monotonic() + 60
        while True:
            try:
                readiness = client.get("/api/health/ready")
                if readiness.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if time.monotonic() >= ready_by:
                raise RuntimeError("Local demonstration application did not become ready within 60 seconds")
            time.sleep(0.5)
        login = client.post("/api/auth/login", json={
            "identifier": account["email"], "password": account["password"], "remember": True,
        })
        login.raise_for_status()
        client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
        cases = client.get("/api/cases")
        cases.raise_for_status()
        case = next((row for row in cases.json() if row.get("case_code") == CASE_CODE), None)
        if case is None:
            created = client.post("/api/cases", json={
                "case_code": CASE_CODE,
                "modality": "XCA",
                "anatomy": "coronary",
                "intended_task": "artery_and_stenosis",
                "source_dataset": "Synthetic software fixture — not patient data",
                "notes": "Generated geometry for local workflow demonstration only. Not clinical evidence, a patient study, or model-performance validation.",
            })
            created.raise_for_status()
            case = created.json()
        case_detail = client.get(f"/api/cases/{case['id']}")
        case_detail.raise_for_status()
        image = next((row for row in case_detail.json().get("images", [])
                      if row.get("original_name") == "synthetic_demo_fixture.png"), None)
        if image is None:
            uploaded = client.post(
                f"/api/cases/{case['id']}/images",
                files={"file": ("synthetic_demo_fixture.png", synthetic_png(), "image/png")},
                data={"modality": "XCA", "profile": "standard", "standard_pipeline": "baseline"},
            )
            uploaded.raise_for_status()
            image = uploaded.json()
        history = client.get(f"/api/images/{image['id']}/analysis/jobs")
        history.raise_for_status()
        job = next((row for row in history.json() if row.get("status") == "completed"), None)
        if job is None:
            queued = client.post(f"/api/images/{image['id']}/analysis/jobs", json={"idempotency_key": str(uuid4())})
            queued.raise_for_status()
            job = queued.json()
            deadline = time.monotonic() + 180
            while job["status"] in {"pending", "processing"} and time.monotonic() < deadline:
                time.sleep(0.5)
                poll = client.get(job["status_url"])
                poll.raise_for_status()
                job = poll.json()
            if job["status"] != "completed":
                raise RuntimeError(f"Synthetic demonstration analysis did not complete: {job['status']}")
        print(json.dumps({
            "case_code": CASE_CODE,
            "case_id": case["id"],
            "image_id": image["id"],
            "job_id": job["id"],
            "status": job["status"],
            "scope": "synthetic software demonstration only",
        }, sort_keys=True))


if __name__ == "__main__":
    main()
