from io import BytesIO
import json
from zipfile import ZipFile

import numpy as np
import pytest
import SimpleITK as sitk
from fastapi.testclient import TestClient

from app.main import app
from app.volume_preprocessing import (prepare_volume, augment_training_volume, geometry,
                                      validate, read_volume, register_rigid)


def volume():
    z, y, x = np.indices((16, 18, 20))
    image = sitk.GetImageFromArray((x*x+y*3+z*5).astype(np.float32))
    image.SetSpacing((.7, .9, 2.))
    image.SetOrigin((12., -7., 30.))
    image.SetDirection((0., -1., 0., 1., 0., 0., 0., 0., 1.))
    mask = sitk.GetImageFromArray(np.where(x < 8, 0, np.where(x < 14, 1, 2)).astype(np.uint8))
    mask.CopyInformation(image)
    return image, mask


def test_geometry_roi_resolution_labels_slice():
    image, mask = volume()
    prepared, labels, tensor, selected, record, _ = prepare_volume(
        image, mask=mask, roi=[2, 3, 4, 12, 10, 8], spacing=[1., 1., 1.], slice_index=3,
        denoise=True, enhance=True)
    assert prepared.GetOrigin() == image.TransformIndexToPhysicalPoint((2, 3, 4))
    assert prepared.GetDirection() == image.GetDirection()
    assert geometry(prepared) == geometry(labels)
    assert set(np.unique(sitk.GetArrayFromImage(labels))) <= {0, 1, 2}
    np.testing.assert_allclose((np.array(prepared.GetSize())-1)*prepared.GetSpacing(),
                               (np.array([12, 10, 8])-1)*image.GetSpacing())
    assert tensor.dtype == np.float32 and tensor.shape[0] == 1
    np.testing.assert_array_equal(selected[0], tensor[0, 3])
    assert np.isfinite(tensor).all() and tensor.min() >= 0 and tensor.max() <= 1
    assert record["steps"].index("optional_local_contrast_enhancement") < record["steps"].index("physical_origin_preserving_roi_crop")
    assert geometry(image)["size_xyz"] == [20, 18, 16]  # source untouched


@pytest.mark.parametrize("size", [(1001, 777), (777, 1001), (32, 8192), (400, 300), (1019, 519)])
def test_2d_spacing_geometry_matches_real_resize(size):
    from PIL import Image
    from app.preprocessing import content_geometry, processed_spacing_mm
    preview = Image.new("L", size)
    preview.thumbnail((512, 512), Image.Resampling.LANCZOS)
    assert content_geometry(*size)["content_size_xy"] == list(preview.size)
    spacing = [float(v) for v in processed_spacing_mm("0.3,0.4", *size, None).split(",")]
    np.testing.assert_allclose(spacing, [.3*size[1]/preview.height, .4*size[0]/preview.width])


def test_invalid_geometry_mask_and_selection():
    image, mask = volume()
    with pytest.raises(ValueError, match="spacing"):
        prepare_volume(image, spacing=[0, 1, 1])
    with pytest.raises(ValueError, match="ROI"):
        prepare_volume(image, roi=[-1, 0, 0, 4, 4, 4])
    with pytest.raises(ValueError, match="Slice"):
        prepare_volume(image, slice_index=100)
    mask.SetOrigin((0, 0, 0))
    with pytest.raises(ValueError, match="geometry"):
        prepare_volume(image, mask=mask)
    values = sitk.GetArrayFromImage(image); values[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        validate(sitk.GetImageFromArray(values))


def test_training_only_paired_augmentation():
    image, mask = volume()
    with pytest.raises(ValueError, match="training"):
        augment_training_volume(image, mask, seed=42, split="test")
    first, first_mask = augment_training_volume(image, mask, seed=42, split="train")
    second, second_mask = augment_training_volume(image, mask, seed=42, split="train")
    np.testing.assert_array_equal(sitk.GetArrayFromImage(first), sitk.GetArrayFromImage(second))
    np.testing.assert_array_equal(sitk.GetArrayFromImage(first_mask), sitk.GetArrayFromImage(second_mask))
    assert geometry(first) == geometry(image)
    assert set(np.unique(sitk.GetArrayFromImage(first_mask))) <= {0, 1, 2}


def test_rigid_registration_is_explicit_and_records_qc():
    image, _ = volume()
    transform, record = register_rigid(image, image)
    assert record["quality_control_required"] is True
    assert np.isfinite(record["metric"])
    assert np.isfinite(transform.TransformPoint((12, 0, 40))).all()


def test_nifti_units_and_reading(tmp_path):
    import nibabel as nib
    path = tmp_path / "unknown.nii.gz"
    nii = nib.Nifti1Image(np.zeros((8, 8, 8)), np.eye(4))
    nib.save(nii, path)
    with pytest.raises(ValueError, match="units"):
        read_volume(path)
    nii.header.set_xyzt_units("mm")
    nib.save(nii, path)
    assert read_volume(path).GetSize() == (8, 8, 8)


def test_dicom_series_geometry_and_identifiers(tmp_path):
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid
    series, study = generate_uid(), generate_uid()
    for index in range(3):
        meta = FileMetaDataset()
        meta.MediaStorageSOPClassUID = CTImageStorage
        meta.MediaStorageSOPInstanceUID = generate_uid()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        path = tmp_path / f"slice_{index}.dcm"
        ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0"*128)
        ds.SOPClassUID = CTImageStorage; ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
        ds.SeriesInstanceUID = series; ds.StudyInstanceUID = study
        ds.Modality = "CT"; ds.Rows = 32; ds.Columns = 32
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.ImagePositionPatient = [10, 20, index*2]
        ds.PixelSpacing = [.5, .7]; ds.SliceThickness = 2
        ds.SamplesPerPixel = 1; ds.PhotometricInterpretation = "MONOCHROME2"
        ds.BitsAllocated = 16; ds.BitsStored = 16; ds.HighBit = 15; ds.PixelRepresentation = 1
        ds.RescaleSlope = 2; ds.RescaleIntercept = -1000
        ds.PixelData = np.full((32, 32), index+100, dtype=np.int16).tobytes()
        ds.save_as(path, enforce_file_format=True)
    image = read_volume(tmp_path)
    np.testing.assert_allclose(image.GetSpacing(), [.7, .5, 2])
    assert image.GetOrigin() == (10, 20, 0)
    assert sitk.GetArrayFromImage(image)[0, 0, 0] == -800
    import pydicom
    path = tmp_path / "slice_0.dcm"
    ds = pydicom.dcmread(path); ds.PatientName = "Identified^Sample"; ds.save_as(path)
    with pytest.raises(ValueError, match="identifying"):
        read_volume(tmp_path)


def test_volume_upload_export_and_access(tmp_path):
    image, _ = volume()
    path = tmp_path / "sample.nii.gz"
    sitk.WriteImage(image, str(path))
    raw = path.read_bytes()
    with TestClient(app) as client:
        def login(email):
            from conftest import authorize_test_researcher
            assert client.post("/api/auth/register", json={"email": email, "password": "Volume-Test-2026!"}).status_code == 201
            authorize_test_researcher(email)
            token = client.post("/api/auth/login", json={"identifier": email, "password": "Volume-Test-2026!"}).json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        headers = login("volume-owner@example.org")
        outsider = login("volume-other@example.org")
        response = client.post("/api/cases", headers=headers, json={"case_code": "VOLUME-TEST", "modality": "CTA"})
        assert response.status_code == 201, response.text
        case_id = response.json()["id"]
        url = f"/api/cases/{case_id}/volumes/prepare"
        assert client.post(url, files={"file": ("sample.nii.gz", raw)}).status_code == 401
        assert client.post(url, headers=outsider, files={"file": ("sample.nii.gz", raw)}).status_code == 404
        assert client.post(url, headers=headers, files={"file": ("sample.png", raw)}).status_code == 415
        assert client.post(url, headers=headers, files={"file": ("broken.nii", b"invalid")}).status_code == 422
        assert client.post(url, headers=headers, files={"file": ("sample.nii.gz", raw)}, data={"spacing": "0,1,1"}).status_code == 422
        result = client.post(url, headers=headers, files={"file": ("sample.nii.gz", raw)}, data={"spacing": "1,1,1"})
        assert result.status_code == 200, result.text
        with ZipFile(BytesIO(result.content)) as archive:
            assert archive.testzip() is None
            assert archive.read("source.nii.gz") == raw
            assert {"prepared.nii.gz", "model_input_czyx.npy", "slice_preview.png"} <= set(archive.namelist())
            record = json.loads(archive.read("processing_record.json"))
            assert record["registration"] is None
            assert record["prepared_geometry"]["origin_lps_mm"] == list(image.GetOrigin())
