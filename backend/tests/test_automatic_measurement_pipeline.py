"""Isolated synthetic persisted-run test; no weights or patient references."""
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import numpy as np
from PIL import Image as PILImage
from fastapi.testclient import TestClient
from app import main
from app.database import SessionLocal
from app.models import AnalysisEvent
from test_rbac_system import make_user


def test_saved_source_mask_measurement_reports_and_access(monkeypatch):
    mask=np.zeros((512,512),bool);mask[240:264,30:480]=True
    mask[240:246,200:281]=False;mask[258:264,200:281]=False
    image=(51+178*mask).astype('uint8')
    stream=BytesIO();PILImage.fromarray(image).save(stream,'PNG');raw=stream.getvalue()
    monkeypatch.setattr(main,'models_ready',lambda:True)
    monkeypatch.setattr(main,'analyze',lambda path,spacing=None:(raw,int(mask.sum()),10,
        {'quality_flags':[]},None,None,None,None,{'instance_detections':[{'candidate_id':'C1',
        'bbox_prepared_xyxy':[198,230,282,275],'model_score':.7,'category_id':26}]},None))
    with TestClient(main.app) as client:
        _,owner=make_user(f'automatic-owner-{uuid4().hex}@example.org','doctor')
        _,other=make_user(f'automatic-other-{uuid4().hex}@example.org','doctor')
        case=client.post('/api/cases',headers=owner,json={'case_code':'SYNTHETIC-'+uuid4().hex,
            'modality':'XCA','anatomy':'coronary'}).json()
        image_row=client.post(f"/api/cases/{case['id']}/images",headers=owner,
            files={'file':('synthetic.png',raw,'image/png')}).json()
        event=client.post(f"/api/images/{image_row['id']}/analyze",headers=owner).json()
        with SessionLocal() as db:
            saved=db.get(AnalysisEvent,event['id']);overlay=Path(saved.overlay_path)
        PILImage.fromarray(mask.astype('uint8')*255).save(overlay.with_name(event['id']+'.artery_mask.png'))
        url=f"/api/cases/{case['id']}/automatic-measurements/{event['id']}"
        response=client.post(url,headers=owner)
        assert response.status_code==201,response.text
        record=response.json()['records'][0]
        assert record['status']=='experimental_measurement',record
        assert response.json()['measurement_method']['id']=='sgharshitha-centerline-diameter-adaptation-v1'
        assert record['measurement_method']['id']=='sgharshitha-centerline-diameter-adaptation-v1'
        assert abs(record['narrowing_percent']-50)<3
        assert len(record['sensitivity']['variants'])==2
        assert record['severity']['category'] is None
        assert client.post(url,headers=owner).json()==response.json()
        assert client.get(url,headers=other).status_code==404
        report=client.post(f"/api/cases/{case['id']}/research-reports",headers=owner,
            json={'image_id':image_row['id'],'analysis_event_id':event['id']})
        assert report.status_code==201,report.text
        assert report.json()['automatic_measurements']==[response.json()]
        base=f"/api/cases/{case['id']}/research-reports/{report.json()['report_id']}/export/"
        assert 'automatic_measurements' in client.get(base+'csv',headers=owner).text
        assert client.get(base+'pdf',headers=owner).content.startswith(b'%PDF')
        assert client.get(base+'zip',headers=owner).status_code==200
