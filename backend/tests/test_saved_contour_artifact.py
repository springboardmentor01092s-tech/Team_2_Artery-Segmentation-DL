"""Synthetic saved-byte delivery checks; no model or medical-image compute."""
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from PIL import Image
from fastapi.testclient import TestClient
from app import main
from app.database import SessionLocal
from app.models import AnalysisEvent
from test_rbac_system import make_user

def test_saved_contour_bytes_are_run_bound_and_authorized(monkeypatch):
 raw=BytesIO();Image.new('L',(32,32),128).save(raw,'PNG');png=raw.getvalue()
 monkeypatch.setattr(main,'models_ready',lambda:True)
 monkeypatch.setattr(main,'analyze',lambda *args:(png,12,0,{},None,None,None,None,{},None))
 with TestClient(main.app) as c:
  _,owner=make_user(f'contour-{uuid4().hex}@example.org','researcher');_,other=make_user(f'other-{uuid4().hex}@example.org','researcher')
  case=c.post('/api/cases',headers=owner,json={'case_code':'SYNTHETIC-CONTOUR'}).json()
  image=c.post(f'/api/cases/{case["id"]}/images',headers=owner,files={'file':('synthetic.png',png,'image/png')}).json()
  result=c.post(f'/api/images/{image["id"]}/analyze',headers=owner).json();event_id=result['id']
  with SessionLocal() as db:
   event=db.get(AnalysisEvent,event_id);target=Path(event.overlay_path).with_name(f'{event_id}.vessel_contours_prepared.png');target.write_bytes(png)
  url=f'/api/images/{image["id"]}/analyses/{event_id}/artifacts/vessel_contours_prepared'
  response=c.get(url,headers=owner);assert response.status_code==200 and response.content==png
  assert response.headers['x-content-type-options']=='nosniff'
  assert c.get(url).status_code==401 and c.get(url,headers=other).status_code==404
  assert c.get(url.replace(event_id,'wrong-run'),headers=owner).status_code==404
