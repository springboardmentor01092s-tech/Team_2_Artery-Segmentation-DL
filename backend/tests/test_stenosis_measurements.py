"""Fixture measurements never constitute patient measurements or accuracy."""
from io import BytesIO
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import main
from app.narrowing import severity_from_protocol
from test_rbac_system import make_user


def protocol():
    return dict(id='synthetic-only', version='1', reference='fixture reference, not clinical',
        approved_by='fixture', status='approved_for_research',
        bands=[dict(lower=0, upper=40, label='A'), dict(lower=40, upper=100, label='B')])


def test_protocol_boundaries_and_fail_closed():
    assert severity_from_protocol(20, None)['category'] is None
    assert severity_from_protocol(0, protocol())['category'] == 'A'
    assert severity_from_protocol(40, protocol())['category'] == 'B'
    assert severity_from_protocol(100, protocol())['category'] == 'B'
    for value in (-1, 101, float('nan'), True):
        with pytest.raises(ValueError): severity_from_protocol(value, protocol())
    for change in ({'status':'proposed'}, {'reference':''}, {'bands':[]}):
        with pytest.raises(ValueError): severity_from_protocol(20, {**protocol(), **change})
    bad = protocol(); bad['bands'][1]['lower'] = 41
    with pytest.raises(ValueError): severity_from_protocol(20, bad)
    for malformed in ([], 'invalid', {**protocol(), 'bands':[None]}):
        with pytest.raises(ValueError): severity_from_protocol(20, malformed)


def test_reviewed_measurement_identity_rbac_history_and_reports(monkeypatch):
    monkeypatch.delenv('STENOSIS_SEVERITY_PROTOCOL', raising=False)
    monkeypatch.setattr(main, 'models_ready', lambda: True)
    raw = BytesIO(); Image.new('L', (512,512),128).save(raw,'PNG')
    monkeypatch.setattr(main,'analyze',lambda path,spacing=None:(raw.getvalue(),100,10,
        {'quality_flags':[]},None,None,None,None,
        {'instance_detections':[{'candidate_id':'C1','bbox_prepared_xyxy':[10,10,20,20],
            'model_score':.5,'category_id':26}]},None))
    with TestClient(main.app) as client:
        _,owner=make_user(f'measure-{uuid4().hex}@example.org','doctor')
        _,outsider=make_user(f'measure-{uuid4().hex}@example.org','doctor')
        _,researcher=make_user(f'measure-{uuid4().hex}@example.org','researcher')
        case=client.post('/api/cases',headers=owner,json={'case_code':uuid4().hex}).json()
        base=f"/api/cases/{case['id']}"
        image=client.post(base+'/images',headers=owner,files={'file':('test.png',raw.getvalue(),'image/png')}).json()
        event=client.post(f"/api/images/{image['id']}/analyze",headers=owner).json()
        assert 'id' in event,event
        path=base+'/stenosis-measurements'
        data=dict(image_id=image['id'],analysis_event_id=event['id'],candidate_id='C1',
            minimum_diameter_mm=1,reference_diameter_mm=4,measurement_frame='fixture frame',
            reference_segment_id='R1',protocol_id='fixture-only',calibration_evidence='fixture calibration',
            measurement_evidence='synthetic reviewed locations',calibration_verified=True,reference_selection_reviewed=True)
        assert client.post(path,json=data).status_code==401
        assert client.post(path,headers=outsider,json=data).status_code==404
        assert client.post(path,headers=researcher,json=data).status_code==403
        assert client.post(path,headers=owner,json={**data,'candidate_id':'missing'}).status_code==422
        assert client.post(path,headers=owner,json={**data,'minimum_diameter_mm':5}).status_code==422
        assert client.post(path,headers=owner,json={**data,'calibration_verified':False}).status_code==422
        assert client.post(path,headers=owner,json={**data,'calibration_verified':1}).status_code==422
        assert client.post(path,headers=owner,json={**data,'minimum_diameter_mm':True}).status_code==422
        saved=client.post(path,headers=owner,json=data)
        assert saved.status_code==201,saved.text
        first=saved.json();assert first['result']['narrowing_percent']==75
        assert first['result']['severity']['category'] is None
        second=client.post(path,headers=owner,json={**data,'minimum_diameter_mm':2}).json()
        assert second['id']!=first['id'] and second['result']['narrowing_percent']==50
        rows=client.get(path,headers=owner,params={'analysis_event_id':event['id']}).json()
        assert len(rows)==2 and first in rows
        assert client.get(path,headers=outsider,params={'analysis_event_id':event['id']}).status_code==404
        assert client.get(path,headers=owner,params={'analysis_event_id':'missing'}).status_code==404
        unchanged=client.get(f"/api/images/{image['id']}/analyses",headers=owner).json()
        assert unchanged[0]['id']==event['id']
        report=client.post(base+'/research-reports',headers=owner,json={'image_id':image['id'],'analysis_event_id':event['id']})
        assert report.status_code==201,report.text
        assert len(report.json()['reviewed_stenosis_measurements'])==2
        report_url=base+'/research-reports/'+report.json()['report_id']
        csv=client.get(report_url+'/export/csv',headers=owner)
        assert csv.status_code==200 and 'reviewed_stenosis_measurements' in csv.text
        pdf=client.get(report_url+'/export/pdf',headers=owner)
        assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-')
        before=report.json()
        client.post(path,headers=owner,json=data)
        assert client.get(report_url,headers=owner).json()==before
