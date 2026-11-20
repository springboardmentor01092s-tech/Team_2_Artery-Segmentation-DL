import io
import secrets
import time

import httpx
from PIL import Image

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as client:
    for attempt in range(90):
        try:
            if client.get("/api/health/ready").is_success:
                break
        except httpx.TransportError:
            pass
        time.sleep(2)
    else:
        raise RuntimeError("Readiness timeout")

    def account(name):
        email = f"{name}@example.org"
        password = secrets.token_urlsafe(24)
        with SessionLocal() as db:
            db.add(User(email=email, password_hash=hash_password(password), role="researcher", status="active"))
            db.commit()
        token = client.post("/api/auth/login", json={"email": email, "password": password}).raise_for_status().json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    owner, outsider = account("owner"), account("outsider")
    def submit(label):
        case = client.post("/api/cases", headers=owner, json={"case_code": f"CAPPED-SYNTHETIC-{label}"}).raise_for_status().json()
        case_url = f"/api/cases/{case['id']}"
        source = io.BytesIO()
        Image.new("RGB", (512, 512), (120 + label, 120, 120)).save(source, "PNG")
        image = client.post(f"{case_url}/images", headers=owner, files={"file": ("synthetic.png", source.getvalue(), "image/png")}).raise_for_status().json()
        job = client.post(f"/api/images/{image['id']}/analysis/jobs", headers=owner, json={"idempotency_key": f"capped-synthetic-{label}"}).raise_for_status().json()
        return case_url, job
    from concurrent.futures import ThreadPoolExecutor

    def verify(case_url, job):
        started = time.monotonic()
        last_status = None
        while time.monotonic() - started < 600:
            status = client.get(job["status_url"], headers=owner)
            state = status.raise_for_status().json()
            if state["status"] != last_status:
                last_status = state["status"]
                print(f"Job {job['id']} status {last_status} after {time.monotonic() - started:.1f}s")
            if last_status not in {"processing", "pending"}:
                break
            time.sleep(2)
        assert last_status == "completed", state
        reports_url = f"{case_url}/research-reports"
        for attempt in range(15):
            reports = client.get(reports_url, headers=owner).raise_for_status().json()
            if reports:
                break
            time.sleep(1)
        assert len(reports) == 1 and reports[0]["analysis_event_id"] == state["result_event_id"], reports
        report_id = reports[0]["id"]
        for fmt, expected in [("pdf", "application/pdf"), ("csv", "text/csv"), ("json", "application/json")]:
            url = f"{reports_url}/{report_id}/export/{fmt}"
            result = client.get(url, headers=owner).raise_for_status()
            assert expected in result.headers["content-type"]
            assert client.get(url, headers=outsider).status_code == 404
            if fmt == "pdf":
                assert result.content.startswith(b"%PDF-")
            print(f"{fmt}: {len(result.content)} bytes, outsider denied")
        print(f"Report {report_id} bound to run {state['result_event_id']}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = list(pool.map(submit, (1, 2)))
        assert len({job["id"] for _, job in jobs}) == 2
        checks = [pool.submit(verify, case_url, job) for case_url, job in jobs]
        for check in checks:
            check.result()
