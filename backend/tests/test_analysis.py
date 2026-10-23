from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.main import app


def _login(client, email):
    from conftest import authorize_test_researcher
    password = "research-password-123"
    assert client.post("/api/auth/register", json={"email": email, "password": password}).status_code == 201
    authorize_test_researcher(email)
    token = client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_analysis_is_real_model_gated_and_case_scoped(monkeypatch):
    with TestClient(app) as client:
        owner = _login(client, "analysis-owner@example.org")
        other = _login(client, "analysis-other@example.org")
        case = client.post("/api/cases", headers=owner, json={"case_code": "ANALYSIS-1"}).json()
        image = Image.new("L", (64, 64), 100)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        uploaded = client.post(f"/api/cases/{case['id']}/images", headers=owner,
                               files={"file": ("image.png", buffer.getvalue(), "image/png")}).json()
        image_id = uploaded["id"]
        monkeypatch.setattr(main, "models_ready", lambda: False)
        assert client.post(f"/api/images/{image_id}/analyze", headers=owner).status_code == 503
        assert client.post(f"/api/images/{image_id}/analyze", headers=other).status_code == 404
        monkeypatch.setattr(main, "models_ready", lambda: True)
        monkeypatch.setattr(main, "analyze", lambda path, spacing=None: (
            buffer.getvalue(), 123, 4,
            {"centerline_paths": [], "branch_points": [], "endpoint_points": [],
             "quality_flags": [], "quality_status": "information_only"},
            None, None, None, None,
            {"artery_foreground_mean_probability": None,
             "stenosis_foreground_mean_probability": None,
             "calibration": "unavailable"},
            buffer.getvalue(),
        ))
        result = client.post(f"/api/images/{image_id}/analyze", headers=owner)
        assert result.status_code == 200, result.text
        assert result.json()["research_only"] is True
        assert result.json()["stenosis_pixels"] == 4
        assert result.json()["model_scores"]["calibration"] == "unavailable"
        assert client.get(f"/api/images/{image_id}/analysis", headers=owner).status_code == 200
        assert client.get(f"/api/images/{image_id}/analysis/overlay", headers=owner).status_code == 200
        assert client.get(f"/api/images/{image_id}/analysis/map/centerline", headers=owner).status_code == 200
        assert client.get(f"/api/images/{image_id}/analysis", headers=other).status_code == 404
        assert client.get(f"/api/images/{image_id}/analysis/overlay", headers=other).status_code == 404
