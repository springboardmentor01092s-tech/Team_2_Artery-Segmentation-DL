"""Upload public fixtures for local Docker engineering acceptance."""
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import httpx
from PIL import Image

root = Path(__file__).resolve().parents[1]
account = next(a for a in json.load(sys.stdin)["accounts"] if a["email"] == "researcher.demo@example.com")
source = root / "external_artifacts/public_cta_acceptance/CTACardio_original_hu.nii.gz"
provenance = json.loads(source.with_name("PROVENANCE.json").read_text())
with source.open("rb") as stream:
    assert hashlib.file_digest(stream, "sha256").hexdigest() == provenance["nifti_sha256"]
archive = next((root.parent / "external_artifacts").glob("dca1*/X-ray Coronary Angiograms.zip"))
with ZipFile(archive) as z:
    with Image.open(io.BytesIO(z.read("X-ray Coronary Angiograms/Test/107.pgm"))) as image:
        png = io.BytesIO()
        image.save(png, format="PNG")

with httpx.Client(base_url="http://127.0.0.1:8001", timeout=120) as client:
    def call(method, path, **kwargs):
        response = client.request(method, path, **kwargs)
        response.raise_for_status()
        return response

    client.headers["Authorization"] = "Bearer " + call("POST", "/api/auth/login", json={
        "identifier": account["email"], "password": account["password"],
    }).json()["access_token"]

    def case(modality, task, dataset):
        record = call("POST", "/api/cases", json={
            "case_code": f"DOCKER-PUBLIC-{modality}-{uuid4().hex[:6]}",
            "modality": modality, "anatomy": "coronary", "intended_task": task,
            "source_dataset": dataset,
        }).json()
        print(record["case_code"], record["id"], flush=True)
        return f"/api/cases/{record['id']}"

    def wait(path, job_id=None):
        for _ in range(240):
            data = call("GET", path).json()
            row = next(item for item in data if item["id"] == job_id) if job_id else data
            if row["status"] not in {"pending", "queued", "processing", "running"}:
                return row
            time.sleep(1)
        raise TimeoutError(path)

    path = case("XCA", "artery_and_stenosis", "DCA1 v1, 107.pgm converted to PNG, CC BY 4.0")
    image_id = call("POST", path + "/images", files={
        "file": ("dca1-107.png", png.getvalue(), "image/png"),
    }, data={"modality": "XCA", "profile": "standard", "standard_pipeline": "baseline"}).json()["id"]
    job = call("POST", f"/api/images/{image_id}/analysis/jobs",
               json={"idempotency_key": uuid4().hex}).json()
    path3d = case("CTA", "volume_preparation", provenance["dataset"])
    with source.open("rb") as stream:
        run = call("POST", path3d + "/volumes/analyses",
                   files={"file": (source.name, stream, "application/gzip")},
                   data={"hu_confirmed": "true", "research_confirmed": "true", "input_kind": "medical_study"}).json()
    for kind, row in [("2D", wait(job["status_url"])), ("3D", wait(path3d + "/volumes/analyses", run["id"]))]:
        print(kind, row["id"], row["status"], row.get("error"), flush=True)
        if row["status"] != "completed":
            continue
        if kind == "2D":
            result = call("GET", row["result_url"]).json()["structured_result"]
            print("2D artifacts", {name: len(call("GET", result["artifacts"][name]).content)
                                  for name in ("artery_mask", "stenosis_mask", "overlay")}, flush=True)
        else:
            assert row["source_sha256"] == provenance["nifti_sha256"]
            print("3D artifacts", {name: len(call("GET", url).content)
                                  for name, url in row["artifacts"].items()}, flush=True)
