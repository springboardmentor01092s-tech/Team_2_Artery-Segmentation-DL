from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from test_volume_inference import make_user


def test_rejected_upload_preserves_previous_valid_case():
    with TestClient(app) as client:
        suffix = uuid4().hex
        _, headers = make_user(f"intake-{suffix}@example.org", "researcher")
        created = client.post("/api/cases", headers=headers, json={"case_code": f"INTAKE-{suffix}"})
        assert created.status_code == 201, created.text
        path = f"/api/cases/{created.json()['id']}"

        def reject():
            response = client.post(path + "/images", headers=headers, files={"file": ("invalid.txt", b"invalid")})
            assert response.status_code == 415

        reject()
        assert client.get(path, headers=headers).json()["workflow_status"] == "validation_failed"
        image = BytesIO()
        Image.new("L", (128, 128), 100).save(image, "PNG")
        uploaded = client.post(path + "/images", headers=headers,
                               files={"file": ("valid.png", image.getvalue(), "image/png")})
        assert uploaded.status_code == 201, uploaded.text
        before = client.get(path, headers=headers).json()
        assert before["workflow_status"] != "validation_failed"
        reject()
        after = client.get(path, headers=headers).json()
        for key in ("workflow_status", "processing_status", "images"):
            assert before[key] == after[key]
