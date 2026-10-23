from io import BytesIO

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid

from app import main
from app.main import app
from app.preprocessing import InvalidImage, prepare_image, processed_spacing_mm


def login(client, email):
    from conftest import authorize_test_researcher
    password = "long-demo-password-123"
    assert client.post("/api/auth/register", json={"email": email, "password": password}).status_code == 201
    authorize_test_researcher(email)
    token = client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("format_name,extension", [
    ("WEBP", "webp"), ("TIFF", "tiff"), ("BMP", "bmp"), ("GIF", "gif"),
])
def test_additional_image_formats_are_converted(format_name, extension):
    source = BytesIO()
    Image.new("RGB", (80, 60), (80, 130, 170)).save(source, format=format_name)
    preview, width, height, media_type, spacing = prepare_image(source.getvalue(), f"study.{extension}")
    assert (width, height, spacing) == (80, 60, None)
    assert media_type.startswith("image/")
    assert Image.open(BytesIO(preview)).size == (512, 512)


def test_multiple_images_can_be_added_to_one_case():
    with TestClient(app) as client:
        headers = login(client, "batch-upload@example.org")
        case_id = client.post("/api/cases", headers=headers, json={"case_code": "BATCH-001"}).json()["id"]
        for format_name, extension in [("PNG", "png"), ("WEBP", "webp"), ("TIFF", "tif")]:
            source = BytesIO()
            Image.new("RGB", (64, 64), (80, 130, 170)).save(source, format=format_name)
            response = client.post(
                f"/api/cases/{case_id}/images", headers=headers,
                files={"file": (f"study.{extension}", source.getvalue(), "application/octet-stream")},
            )
            assert response.status_code == 201, response.text
        case = client.get(f"/api/cases/{case_id}", headers=headers).json()
        assert len(case["images"]) == 3


def test_pdf_page_conversion_and_recorded_pipeline():
    source = BytesIO()
    Image.new("RGB", (128, 96), (80, 130, 170)).save(source, format="PDF")
    preview, width, height, media_type, spacing = prepare_image(source.getvalue(), "scan.pdf", page_index=0)
    assert (width, height, media_type, spacing) == (2048, 1536, "application/pdf", None)
    assert Image.open(BytesIO(preview)).size == (512, 512)
    with pytest.raises(InvalidImage, match="PDF page"):
        prepare_image(source.getvalue(), "scan.pdf", page_index=12)
    with TestClient(app) as client:
        headers = login(client, "pdf-upload@example.org")
        case_id = client.post("/api/cases", headers=headers, json={"case_code": "PDF-001"}).json()["id"]
        response = client.post(f"/api/cases/{case_id}/images", headers=headers,
                               files={"file": ("scan.pdf", source.getvalue(), "application/pdf")})
        assert response.status_code == 201, response.text
        assert response.json()["page_index"] == 0
        image = client.get(f"/api/cases/{case_id}", headers=headers).json()["images"][0]
        assert image["page_index"] == 0
        assert {"pdf_page_rasterization", "grayscale_conversion", "aspect_preserving_resize"} <= set(image["preprocessing"])
        assert "optional_median_noise_reduction" not in image["preprocessing"]
        assert "optional_clipped_autocontrast" not in image["preprocessing"]


def test_unsupported_document_and_processed_spacing():
    assert processed_spacing_mm("0.3,0.4", 1024, 512, None) == "0.6,0.8"
    assert processed_spacing_mm("0.3,0.4", 1024, 512, (0, 0, 512, 512)) == "0.3,0.4"
    with TestClient(app) as client:
        headers = login(client, "document-reject@example.org")
        case_id = client.post("/api/cases", headers=headers, json={"case_code": "DOC-001"}).json()["id"]
        response = client.post(f"/api/cases/{case_id}/images", headers=headers,
                               files={"file": ("notes.docx", b"not-an-image", "application/octet-stream")})
        assert response.status_code == 415


def test_case_metadata_roi_and_append_only_analysis(monkeypatch):
    with TestClient(app) as client:
        owner = login(client, "history-owner@example.org")
        outsider = login(client, "history-other@example.org")
        created = client.post("/api/cases", headers=owner, json={
            "case_code": "DEID-1", "patient_code": "RESEARCH-001", "age_band": "60_69",
            "clinical_metadata_enabled": True,
            "gender": "unknown", "medical_history": ["hypertension"],
            "risk_factors": ["smoking"], "clinical_notes": "Public de-identified sample",
        })
        assert created.status_code == 201, created.text
        case_id = created.json()["id"]
        assert created.json()["patient_code"] == "RESEARCH-001"
        assert client.patch(f"/api/cases/{case_id}", headers=outsider,
                            json={"gender": "female"}).status_code == 404
        assert client.patch(f"/api/cases/{case_id}", headers=owner,
                            json={"clinical_notes": "Call person@example.com"}).status_code == 422
        changed = client.patch(f"/api/cases/{case_id}", headers=owner,
                               json={"gender": "female", "scan_date": "2020-01-01"})
        assert changed.status_code == 200, changed.text
        assert changed.json()["scan_date"] == "2020-01-01"

        sample = Image.new("L", (100, 90), 120)
        source = BytesIO()
        sample.save(source, format="PNG")
        invalid_roi = client.post(f"/api/cases/{case_id}/images", headers=owner,
                                  files={"file": ("sample.png", source.getvalue(), "image/png")},
                                  data={"roi": "90,80,60,50"})
        assert invalid_roi.status_code == 422
        upload = client.post(f"/api/cases/{case_id}/images", headers=owner,
                             files={"file": ("sample.png", source.getvalue(), "image/png")},
                             data={"roi": "10,10,60,50"})
        assert upload.status_code == 201, upload.text
        image_id = upload.json()["id"]
        assert upload.json()["roi_box"] == "10,10,60,50"
        case = client.get(f"/api/cases/{case_id}", headers=owner).json()
        assert "roi_crop" in case["images"][0]["preprocessing"]
        preview = client.get(upload.json()["preview_url"], headers=owner)
        assert Image.open(BytesIO(preview.content)).size == (512, 512)

        monkeypatch.setattr(main, "models_ready", lambda: True)
        count = iter(((10, 2), (14, 5)))
        monkeypatch.setattr(main, "analyze", lambda path, spacing=None: (
            source.getvalue(), *next(count),
            {"centerline_paths": [], "branch_points": [], "endpoint_points": [], "quality_flags": []},
            None, None, None, None, {"calibration": "unavailable"}, source.getvalue(),
        ))
        first = client.post(f"/api/images/{image_id}/analyze", headers=owner)
        second = client.post(f"/api/images/{image_id}/analyze", headers=owner)
        assert first.status_code == second.status_code == 200
        history = client.get(f"/api/images/{image_id}/analyses", headers=owner).json()
        assert len(history) == 2
        refreshed_case = client.get(f"/api/cases/{case_id}", headers=owner).json()
        assert refreshed_case["images"][0]["latest_analysis_id"] == history[0]["id"]
        assert {item["artery_pixels"] for item in history} == {10, 14}
        assert client.get(history[1]["overlay_url"], headers=owner).status_code == 200
        comparison = client.get(f"/api/images/{image_id}/analysis/compare", headers=owner,
                                params={"left_id": history[1]["id"], "right_id": history[0]["id"]})
        assert comparison.status_code == 200
        assert comparison.json()["difference"] == {"artery_pixels": 4, "stenosis_pixels": 3}
        assert client.get(f"/api/cases/{case_id}/analyses", headers=owner).status_code == 200
        assert client.get(f"/api/cases/{case_id}/analyses", headers=outsider).status_code == 404
        assert client.get(history[0]["overlay_url"], headers=outsider).status_code == 404


def test_multiframe_dicom_selection_spacing_and_identifier_rejection():
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset("sample.dcm", {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.Rows = 40
    dataset.Columns = 40
    dataset.NumberOfFrames = "2"
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.PixelSpacing = [0.3, 0.4]
    dataset.PixelData = np.arange(3200, dtype=np.uint16).reshape(2, 40, 40).tobytes()
    buffer = BytesIO()
    dataset.save_as(buffer, enforce_file_format=True)
    raw = buffer.getvalue()
    with pytest.raises(InvalidImage, match="Choose a frame"):
        prepare_image(raw, "sample.dcm")
    processed, width, height, media, spacing = prepare_image(raw, "sample.dcm", frame_index=1)
    assert Image.open(BytesIO(processed)).size == (512, 512)
    assert (width, height, media, spacing) == (40, 40, "application/dicom", "0.3,0.4")
    with TestClient(app) as client:
        headers = login(client, "dicom-frame@example.org")
        case_id = client.post("/api/cases", headers=headers, json={"case_code": "DICOM-DEID"}).json()["id"]
        missing_frame = client.post(f"/api/cases/{case_id}/images", headers=headers,
                                    files={"file": ("sample.dcm", raw, "application/dicom")})
        assert missing_frame.status_code == 422
        uploaded = client.post(f"/api/cases/{case_id}/images", headers=headers,
                               files={"file": ("sample.dcm", raw, "application/dicom")},
                               data={"frame_index": "1"})
        assert uploaded.status_code == 201, uploaded.text
        assert uploaded.json()["spacing_mm"] == "0.3,0.4"
        assert uploaded.json()["frame_index"] == 1
    dataset.PatientName = "Identifying Name"
    buffer = BytesIO()
    dataset.save_as(buffer, enforce_file_format=True)
    with pytest.raises(InvalidImage, match="identifying DICOM tags"):
        prepare_image(buffer.getvalue(), "sample.dcm", frame_index=0)
