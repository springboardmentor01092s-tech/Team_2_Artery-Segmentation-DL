from io import BytesIO

from PIL import Image as PILImage

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from conftest import authorize_test_researcher


def test_registration_case_and_image_upload():
    with TestClient(app) as client:
        email = "researcher@example.org"
        password = "a-long-test-password"
        response = client.post("/api/auth/register", json={"email": email, "password": password})
        assert response.status_code == 201
        assert response.json()["role"] == "viewer"
        assert client.post("/api/auth/register", json={"email": email, "password": password}).status_code == 409
        assert client.get("/api/cases").status_code in (401, 403)

        token = client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = client.get("/api/auth/me", headers=headers).json()["id"]
        assert client.post(
            f"/api/admin/users/{user_id}/role", json={"role": "admin"}, headers=headers
        ).status_code == 403
        assert client.post("/api/cases", json={"case_code": "NO-DEFAULT-ACCESS"}, headers=headers).status_code == 403
        authorize_test_researcher(email)
        case = client.post("/api/cases", json={"case_code": "CASE-001"}, headers=headers)
        assert case.status_code == 201
        case_id = case.json()["id"]

        image = PILImage.new("RGB", (640, 480), color=(90, 120, 150))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        upload = client.post(
            f"/api/cases/{case_id}/images",
            files={"file": ("sample.png", buffer.getvalue(), "image/png")},
            headers=headers,
        )
        assert upload.status_code == 201, upload.text
        assert upload.json()["width"] == 640
        preview = client.get(upload.json()["preview_url"], headers=headers)
        assert preview.status_code == 200
        assert PILImage.open(BytesIO(preview.content)).size == (512, 512)
        source = client.get(f"/api/images/{upload.json()['id']}/source", headers=headers)
        assert source.status_code == 200
        assert source.content == buffer.getvalue()

        invalid = client.post(
            f"/api/cases/{case_id}/images",
            files={"file": ("bad.png", b"not an image", "image/png")},
            headers=headers,
        )
        assert invalid.status_code == 422


def test_case_isolation():
    with TestClient(app) as client:
        headers = []
        for index in (1, 2):
            email = f"user{index}@example.org"
            password = "a-long-test-password"
            client.post("/api/auth/register", json={"email": email, "password": password})
            authorize_test_researcher(email)
            token = client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
            headers.append({"Authorization": f"Bearer {token}"})
        case_id = client.post("/api/cases", json={"case_code": "PRIVATE"}, headers=headers[0]).json()["id"]
        assert client.get(f"/api/cases/{case_id}", headers=headers[1]).status_code == 404
        assert client.get("/api/cases", headers=headers[1]).json() == []
        buffer = BytesIO()
        PILImage.new("L", (64, 64), 100).save(buffer, format="PNG")
        uploaded = client.post(f"/api/cases/{case_id}/images", headers=headers[0],
                               files={"file": ("source.png", buffer.getvalue(), "image/png")})
        assert uploaded.status_code == 201
        assert client.get(f"/api/images/{uploaded.json()['id']}/source", headers=headers[1]).status_code == 404
