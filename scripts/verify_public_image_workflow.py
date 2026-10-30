"""Explicit public-image acceptance run against the local app; creates one research case."""
import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[1]
IMAGE = Path("/Volumes/240gb/CoroVision_Full_20261024/workspace/Dataset/2D/ARCADE/syntax/val/images/1.png")


def main():
    raw = IMAGE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != "748a2d4fcd2df8a11e5c1b836abbdf5201d21f75be808e0e71865ef8cda7bf55":
        raise ValueError("Public acceptance fixture integrity mismatch")
    credentials = json.loads((ROOT / "backend/demo-credentials.json").read_text())
    account = next(item for item in credentials["accounts"] if item["email"] == "radiologist.demo@example.com")
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=60) as client:
        login = client.post("/api/auth/login", json={"email": account["email"], "password": account["password"]})
        login.raise_for_status()
        client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
        case_response = client.post("/api/cases", json={"case_code": "PUBLIC-ARCADE-CHECK-" + uuid4().hex[:6]})
        case_response.raise_for_status(); case = case_response.json()
        upload = client.post(f'/api/cases/{case["id"]}/images', files={"file": ("public-arcade-validation.png", raw, "image/png")})
        upload.raise_for_status(); asset = upload.json()
        submitted = client.post(f'/api/images/{asset["id"]}/analysis/jobs', json={"idempotency_key": uuid4().hex})
        submitted.raise_for_status(); job = submitted.json()
        deadline = time.monotonic() + 60
        while job["status"] in {"pending", "processing"} and time.monotonic() < deadline:
            time.sleep(.2)
            response = client.get(job["status_url"]); response.raise_for_status(); job = response.json()
        if job["status"] != "completed":
            raise RuntimeError("Acceptance analysis did not complete: " + job["status"])
        response = client.get(job["result_url"]); response.raise_for_status()
        result = response.json()["structured_result"]
        checks = {}
        for kind in ("artery_mask", "stenosis_mask", "raw_scores", "overlay"):
            response = client.get(result["artifacts"][kind])
            response.raise_for_status(); checks[kind] = bool(response.content)
        receipt = {"case_code": case["case_code"], "case_id": case["id"], "asset_id": asset["id"],
                   "job_id": job["id"], "status": job["status"], "model_version": result["model_version"],
                   "checkpoints": result["models"]["checkpoint_sha256"], "artifacts_verified": checks,
                   "stages": result["stages"], "artery_pixels": result["measurements"]["artery_pixels"],
                   "severity": result["severity"], "explanation_method": result["explanation"]["method"],
                   "source": "Public ARCADE validation image 1; development-exposed; acceptance smoke test, not performance validation"}
        output = ROOT / "reports/public_image_integration_receipt.json"
        output.write_text(json.dumps(receipt, indent=2))
        print(json.dumps({"case_code": case["case_code"], "status": job["status"], "artifacts_verified": checks}))


if __name__ == "__main__":
    main()
