from hashlib import sha256
import pytest
from PIL import Image
from app.reference_collection import convert_draft, lock_cohort, import_and_lock_csv, verify_locked_cohort


def test_geometry_hash_and_lock(tmp_path):
    image=tmp_path/'fixture.png';Image.new('L',(64,64)).save(image)
    draft=dict(source_dataset='synthetic-test',case_id='c',study_id='s',lesion_id='l',
        reference_segment_id='r',reviewer='test-fixture',notes='Synthetic software test only',
        frame_id=image.name,measured_at='2026-11-11T00:00:00Z',blinded=True,quality='eligible',
        source_image_sha256=sha256(image.read_bytes()).hexdigest(),
        endpoints=[dict(tool=t,x=x,y=y) for t,x,y in [('mld',10,10),('mld',10,20),('rvd',30,10),('rvd',30,30)]],
        minimum_diameter=10,reference_diameter=20,reference_method='synthetic fixture',reference_method_version='1')
    row=convert_draft(draft,image)
    receipt=lock_cohort([row],tmp_path/'locked','fixture-v1')
    assert receipt['rows']==1
    with pytest.raises(FileExistsError):lock_cohort([row],tmp_path/'locked','fixture-v2')
    with pytest.raises(ValueError):convert_draft({**draft,'minimum_diameter':11},image)
    with pytest.raises(ValueError):convert_draft({**draft,'source_image_sha256':'0'*64},image)
    with pytest.raises(ValueError):convert_draft({**draft,'quality':'draft'},image)
    import csv
    exported=tmp_path/'browser.csv'
    with exported.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader();writer.writerow(row)
    receipt=import_and_lock_csv(exported,tmp_path,tmp_path/'roundtrip','synthetic-roundtrip-v1')
    assert receipt['rows']==1
    reopened=verify_locked_cohort(tmp_path/'roundtrip')
    assert float(reopened[0]['minimum_diameter'])==10
    assert reopened[0]['lesion_location_original_xy']==row['lesion_location_original_xy']
    (tmp_path/'roundtrip'/'references.csv').write_text('tampered')
    with pytest.raises(ValueError,match='SHA-256'):verify_locked_cohort(tmp_path/'roundtrip')
