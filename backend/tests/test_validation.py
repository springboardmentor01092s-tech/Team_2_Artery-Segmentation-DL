"""Medical image validation tests: corrupt, fake, tiny, odd-format, blank and large images.

Uses high case ids (9100+) so no real case file is ever overwritten. Everything the tests
create in the uploads folder is deleted again by conftest.py at the end.
"""
import io
import itertools

import numpy as np
import pytest
from PIL import Image

from app import models

_ids = itertools.count(9100)
RNG = np.random.default_rng(1)


def _image_bytes(width, height, mode="L", fmt="PNG"):
    arr = RNG.normal(150, 20, (height, width)).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr).convert(mode)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _new_case_with_scan(client, users, filename, content, mime="image/png"):
    """Create a case with a high id and upload the given bytes as its scan."""
    case_id = next(_ids)
    db = client.session_factory()
    db.add(
        models.Case(
            id=case_id,
            owner_id=users["clinician"]["id"],
            patient_id=f"val-{case_id}",
        )
    )
    db.commit()
    db.close()
    r = client.post(
        f"/cases/{case_id}/upload",
        files={"file": (filename, content, mime)},
        headers=users["clinician"]["headers"],
    )
    return case_id, r


BAD_FILES = [
    pytest.param(b"this is not an image", id="plain-text"),
    pytest.param(b"<html><script>alert(1)</script></html>", id="html-disguised"),
    pytest.param(b"", id="empty-file"),
    pytest.param(_image_bytes(200, 200)[:60], id="truncated-png"),
]


# ------------------------------------------------------------------ corrupt and fake images
@pytest.mark.parametrize("content", BAD_FILES)
def test_corrupt_files_are_rejected_by_preprocessing(client, users, content):
    h = users["clinician"]["headers"]
    case_id, _ = _new_case_with_scan(client, users, "scan.png", content)

    r = client.post(f"/cases/{case_id}/preprocess", headers=h)
    assert r.status_code == 400, r.text

    # a failed run must not mark the case as processed
    status = client.get(f"/cases/{case_id}", headers=h).json()["analysis_status"]
    assert status == "Pending"


@pytest.mark.parametrize("endpoint", ["segment", "stenosis-pipeline"])
def test_corrupt_file_gives_a_clean_error_in_analysis(client, users, endpoint):
    h = users["clinician"]["headers"]
    case_id, _ = _new_case_with_scan(client, users, "scan.png", b"this is not an image")

    r = client.post(f"/cases/{case_id}/{endpoint}", headers=h)
    assert r.status_code == 400, r.text

    status = client.get(f"/cases/{case_id}", headers=h).json()["analysis_status"]
    assert status == "Pending"


@pytest.mark.xfail(reason="Upload checks only the file extension, not the image content.")
def test_upload_rejects_files_that_are_not_images(client, users):
    _, r = _new_case_with_scan(client, users, "fake.png", b"this is not an image")
    assert r.status_code == 400


# ------------------------------------------------------------------ size limits
@pytest.mark.parametrize(
    "size",
    [pytest.param((32, 32), id="32x32"), pytest.param((63, 200), id="63x200"), pytest.param((500, 40), id="500x40")],
)
def test_images_below_minimum_size_are_rejected(client, users, size):
    h = users["clinician"]["headers"]
    case_id, _ = _new_case_with_scan(client, users, "small.png", _image_bytes(*size))

    r = client.post(f"/cases/{case_id}/preprocess", headers=h)
    assert r.status_code == 400
    assert "too small" in r.json()["detail"].lower()


def test_image_at_the_minimum_size_is_accepted(client, users):
    h = users["clinician"]["headers"]
    case_id, _ = _new_case_with_scan(client, users, "min.png", _image_bytes(64, 64))

    r = client.post(f"/cases/{case_id}/preprocess", headers=h)
    assert r.status_code == 200, r.text
    assert len(r.json()["stages"]) == 6


def test_large_image_is_handled(client, users):
    h = users["clinician"]["headers"]
    case_id, _ = _new_case_with_scan(client, users, "large.png", _image_bytes(1500, 1500))

    r = client.post(f"/cases/{case_id}/preprocess", headers=h)
    assert r.status_code == 200, r.text
    assert len(r.json()["stages"]) == 6


# ------------------------------------------------------------------ image formats
@pytest.mark.parametrize(
    "mode,fmt,filename,mime",
    [
        pytest.param("L", "PNG", "gray.png", "image/png", id="grayscale-png"),
        pytest.param("RGB", "PNG", "rgb.png", "image/png", id="rgb-png"),
        pytest.param("RGBA", "PNG", "rgba.png", "image/png", id="rgba-png"),
        pytest.param("RGB", "JPEG", "scan.jpg", "image/jpeg", id="rgb-jpeg"),
    ],
)
def test_common_image_formats_are_accepted(client, users, mode, fmt, filename, mime):
    h = users["clinician"]["headers"]
    content = _image_bytes(128, 128, mode=mode, fmt=fmt)
    case_id, up = _new_case_with_scan(client, users, filename, content, mime)
    assert up.status_code == 200, up.text

    r = client.post(f"/cases/{case_id}/preprocess", headers=h)
    assert r.status_code == 200, r.text
    assert len(r.json()["stages"]) == 6


# ------------------------------------------------------------------ odd content
def test_blank_black_image_does_not_crash(client, users):
    h = users["clinician"]["headers"]
    buf = io.BytesIO()
    Image.new("L", (128, 128), 0).save(buf, format="PNG")
    case_id, _ = _new_case_with_scan(client, users, "blank.png", buf.getvalue())

    r = client.post(f"/cases/{case_id}/preprocess", headers=h)
    assert r.status_code in (200, 400)  # a clean answer either way, never a server error