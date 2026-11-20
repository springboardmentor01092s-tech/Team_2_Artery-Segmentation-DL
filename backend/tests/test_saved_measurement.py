import numpy as np
from io import BytesIO
from types import SimpleNamespace

from PIL import Image
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid

from app.image_panels import report_images
from app.saved_measurement import measure_candidate, source_mask


def test_source_mask_decodes_retained_dicom_instead_of_using_pillow(tmp_path):
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset("source.dcm", {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.Rows = dataset.Columns = 40
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.PixelData = np.arange(1600, dtype=np.uint16).reshape(40, 40).tobytes()
    buffer = BytesIO()
    dataset.save_as(buffer, enforce_file_format=True)
    source_path = tmp_path / "source.dcm"
    source_path.write_bytes(buffer.getvalue())
    mask_path = tmp_path / "mask.png"
    expected_mask = np.zeros((40, 40), dtype=np.uint8)
    expected_mask[10:30, 15:25] = 255
    Image.fromarray(expected_mask).save(mask_path)
    image = SimpleNamespace(original_path=str(source_path), original_name="source.dcm",
                            frame_index=None, width=40, height=40,
                            preprocessing_config_json="{}")

    mask, gray = source_mask(image, mask_path)

    assert mask.shape == gray.shape == (40, 40)
    assert np.array_equal(mask, expected_mask > 0)
    assert np.isfinite(gray).all()
    assert gray.min() == 0
    assert gray.max() == 1


def test_report_images_converts_retained_dicom_to_printable_png(tmp_path):
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset("source.dcm", {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.Rows = dataset.Columns = 16
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.PixelData = np.arange(256, dtype=np.uint16).reshape(16, 16).tobytes()
    source_path = tmp_path / "source.dcm"
    dataset.save_as(source_path, enforce_file_format=True)
    overlay_path = tmp_path / "run.png"
    Image.new("RGB", (16, 16), "red").save(overlay_path)
    image = SimpleNamespace(id="image", original_path=str(source_path), original_name="source.dcm",
                            preview_path=str(overlay_path), frame_index=None)
    event = SimpleNamespace(id="run", overlay_path=str(overlay_path))

    rows = report_images(image, event, panels=[
        {'key': 'original', 'title': 'Original', 'description': 'Source'},
        {'key': 'overlay', 'title': 'Overlay', 'description': 'Prediction'},
    ])

    assert isinstance(rows[0][1], BytesIO)
    with Image.open(rows[0][1]) as printable:
        assert printable.format == "PNG"
        assert printable.size == (16, 16)
    assert rows[1][1] == overlay_path


def test_unique_vessel_measurement_and_sensitivity():
    mask=np.zeros((80,120),bool);mask[28:52,4:116]=True
    mask[28:34,45:76]=False;mask[46:52,45:76]=False
    candidate={'candidate_id':'synthetic-C1','bbox_source_xyxy':[48,25,72,55]}
    result=measure_candidate(mask,.2+.7*mask,candidate,'synthetic-run')
    assert result['status']=='experimental_measurement',result
    assert abs(result['narrowing_percent']-50)<3
    assert result['association']['status']=='unique_geometric_path'
    assert len(result['sensitivity']['variants'])==2
    assert result['severity']['category'] is None
    informed=measure_candidate(mask,.2+.7*mask,candidate,'synthetic-run',authorization=dict(
        protocol_id='COROVISION_CADRADS_INFORMED_XCA',protocol_version='1.0.0',
        status='researcher_authorized',authorized_by='synthetic-test',authorized_at='2026-11-11'))
    assert informed['severity']['protocol_id']=='COROVISION_CADRADS_INFORMED_XCA'
    assert informed['severity']['category'] is None
    assert 'crosses' in informed['severity']['reason']


def test_ambiguous_and_missing_source_mapping():
    mask=np.zeros((80,120),bool);mask[20:30,4:116]=True;mask[45:55,4:116]=True
    result=measure_candidate(mask,.2+.7*mask,{'candidate_id':'C','bbox_source_xyxy':[40,10,80,60]},'r')
    assert result['status']=='abstained'
    assert measure_candidate(mask,.2+.7*mask,{'candidate_id':'C'},'r')['reasons']==['original_coordinate_mapping_unreliable']


def test_truncated_candidate_reference_on_narrow_plateau_abstains():
    mask=np.zeros((80,120),bool);mask[28:52,4:116]=True
    mask[28:34,35:86]=False;mask[46:52,35:86]=False
    result=measure_candidate(mask,.2+.7*mask,{'candidate_id':'partial','bbox_source_xyxy':[50,25,70,55]},'r')
    assert result['status']=='abstained'
    assert result['narrowing_percent'] is None
    assert 'reference_suitability_unconfirmed_equal_widths' in result['reasons']
