from io import BytesIO
import hashlib
import numpy as np
import pytest
from PIL import Image, ImageFilter, ImageOps
from fastapi.testclient import TestClient
from app.main import app
from test_rbac_system import make_user


def sample():
    array = np.tile(np.linspace(110, 140, 128, dtype=np.uint8), (96, 1))
    # Sparse impulse noise stays below the autocontrast clipping percentile.
    array[::19, ::23] = 255
    array[::17, ::29] = 0
    image = Image.fromarray(array)
    stream = BytesIO(); image.save(stream, format="PNG")
    return image, stream.getvalue()


def test_standard_presets_execute_and_preserve_source():
    original, raw = sample()
    with TestClient(app) as client:
        _, headers = make_user("standard-pipelines@example.org", "technician")
        case_id = client.post("/api/cases", headers=headers, json={"case_code": "PRESET-COMPARISON"}).json()["id"]
        url = f"/api/cases/{case_id}/images"
        hashes = set()
        for preset, denoise, enhance in [("baseline", False, False), ("denoise", True, False), ("contrast", False, True), ("balanced", True, True)]:
            uploaded = client.post(url, headers=headers, files={"file": ("test.png", raw, "image/png")},
                                   data={"standard_pipeline": preset})
            assert uploaded.status_code == 201, uploaded.text
            item = next(item for item in client.get(f"/api/cases/{case_id}", headers=headers).json()["images"] if item["id"] == uploaded.json()["id"])
            config = item["processing_record"]
            assert config["standard_pipeline"] == preset
            assert config["options"] == {"denoise": denoise, "contrast_enhancement": enhance}
            assert config["source_sha256"] == hashlib.sha256(raw).hexdigest()
            assert ("optional_median_noise_reduction" in item["preprocessing"]) == denoise
            assert ("optional_clipped_autocontrast" in item["preprocessing"]) == enhance
            assert config["resize_geometry"]["content_size_xy"] == [128, 96]
            assert item["spacing_mm"] is None
            assert client.get(item["source_url"], headers=headers).content == raw
            preview_raw = client.get(item["preview_url"], headers=headers).content
            hashes.add(hashlib.sha256(preview_raw).hexdigest())
            expected = original.copy()
            if denoise: expected = expected.filter(ImageFilter.MedianFilter(3))
            if enhance: expected = ImageOps.autocontrast(expected, cutoff=1)
            canvas = Image.new("L", (512, 512)); canvas.paste(expected, (192, 208))
            assert np.array_equal(np.asarray(Image.open(BytesIO(preview_raw))), np.asarray(canvas))
            repeated = client.post(url, headers=headers, files={"file": ("renamed.png", raw, "image/png")}, data={"standard_pipeline": preset})
            assert repeated.status_code == 409
        assert len(hashes) == 4
        assert len(client.get(f"/api/cases/{case_id}", headers=headers).json()["images"]) == 4


@pytest.mark.parametrize("options", [{"standard_pipeline": "unknown"}, {"profile": "standard", "denoise": "true"}, {"profile": "research", "standard_pipeline": "balanced"}])
def test_invalid_or_mixed_presets_are_rejected(options):
    _, raw = sample()
    with TestClient(app) as client:
        _, headers = make_user("invalid-presets@example.org", "researcher")
        # A distinct reference per parameter; no duplicate-case bypass.
        reference = "PRESET-" + hashlib.sha256(str(options).encode()).hexdigest()[:12]
        case_id = client.post("/api/cases", headers=headers, json={"case_code": reference}).json()["id"]
        response = client.post(f"/api/cases/{case_id}/images", headers=headers,
                               files={"file": ("test.png", raw, "image/png")}, data=options)
        assert response.status_code == 422
        assert client.get(f"/api/cases/{case_id}", headers=headers).json()["images"] == []
