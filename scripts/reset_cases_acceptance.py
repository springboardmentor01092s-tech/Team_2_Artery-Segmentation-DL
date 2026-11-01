"""Explicit user-requested recoverable case reset and real application smoke check."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[1]

def main():
    output = ROOT / 'reports' / ('fresh_cases_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(exist_ok=False)
    image = Path('/Volumes/HP SSD/artertry segmentation/Dataset/2D/ARCADE/syntax/val/images/1.png')
    volume = ROOT / 'external_artifacts/public_cta_acceptance/CTACardio_original_hu.nii.gz'
    assert hashlib.sha256(image.read_bytes()).hexdigest() == '748a2d4fcd2df8a11e5c1b836abbdf5201d21f75be808e0e71865ef8cda7bf55'
    assert hashlib.sha256(volume.read_bytes()).hexdigest() == 'b2a26becb48c2850e752449bf51f62fe26cc2d2174a0ee3e6b3bd6f3230a4ef8'
    accounts = json.loads((ROOT/'backend/demo-credentials.json').read_text())['accounts']
    clients, inventory = [], {}
    for account in accounts:
        client = httpx.Client(base_url='http://127.0.0.1:8000', timeout=180)
        response = client.post('/api/auth/login', json={'email': account['email'], 'password': account['password']})
        response.raise_for_status()
        client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
        me = client.get('/api/auth/me'); me.raise_for_status()
        clients.append((client, me.json()))
        response = client.get('/api/cases')
        if response.status_code == 200:
            for case in response.json(): inventory[case['id']] = case
    (output/'before.json').write_text(json.dumps(list(inventory.values()), indent=2))
    admin = next(client for client, me in clients if me['role'] == 'admin')
    researcher = next(client for client, me in clients if me['role'] == 'researcher')
    for case_id in inventory:
        owner = next(client for client, me in clients if me['id'] == inventory[case_id]['owner_id'])
        response = owner.delete('/api/cases/'+case_id); response.raise_for_status()
    print(json.dumps({'moved_to_recoverable_trash':len(inventory)}), flush=True)
    result = {'deleted_case_ids':list(inventory), 'deletion':'administrator trash; originals retained',
              'scope':'Real application acceptance, not accuracy evaluation or model improvement'}
    for kind, source in [('2d', image), ('3d', volume)]:
        response = researcher.post('/api/cases', json={'case_code':'FRESH-'+kind.upper()+'-'+uuid4().hex[:6],
            'modality':'XCA' if kind=='2d' else 'CTA', 'anatomy':'coronary',
            'intended_task':'artery_and_stenosis' if kind=='2d' else 'volume_preparation',
            'notes':'De-identified public workflow acceptance fixture; no accuracy or diagnostic claim.'})
        response.raise_for_status(); case = response.json()
        result[kind] = {'case_id':case['id'], 'case_code':case['case_code']}
        with source.open('rb') as stream:
            if kind == '2d':
                response = researcher.post(f'/api/cases/{case["id"]}/images', files={'file':('public-arcade.png',stream,'image/png')})
                response.raise_for_status(); asset=response.json()
                response=researcher.post(f'/api/images/{asset["id"]}/analysis/jobs',json={'idempotency_key':uuid4().hex})
            else:
                response=researcher.post(f'/api/cases/{case["id"]}/volumes/analyses',
                    files={'file':(source.name,stream,'application/gzip')},
                    data={'hu_confirmed':'true','research_confirmed':'true','input_kind':'medical_study'})
        response.raise_for_status(); job=response.json()
        for _ in range(360):
            if kind=='2d':
                response=researcher.get(job['status_url']); response.raise_for_status(); job=response.json()
            else:
                response=researcher.get(f'/api/cases/{case["id"]}/volumes/analyses'); response.raise_for_status()
                job=next(row for row in response.json() if row['id']==job['id'])
            if job['status'] in {'completed','failed'}: break
            time.sleep(.5)
        result[kind]['job']=job
        (output/'receipt.json').write_text(json.dumps(result,indent=2))
        assert job['status']=='completed', str(job)
        if kind=='2d':
            response=researcher.get(job['result_url']); response.raise_for_status(); saved=response.json()
            structured=saved['structured_result']; artifacts=structured['artifacts']
            response=researcher.get(f'/api/images/{asset["id"]}/analyses'); response.raise_for_status()
            event=response.json()[0]
            response=researcher.post(f'/api/cases/{case["id"]}/research-reports',json={'image_id':asset['id'],'analysis_event_id':event['id']})
            response.raise_for_status(); report=response.json()
            result[kind]['report_id']=report['report_id']
            for fmt in ['json','csv','pdf']:
                response=researcher.get(f'/api/cases/{case["id"]}/research-reports/{report["report_id"]}/export/{fmt}')
                response.raise_for_status(); assert response.content
                (output/('report.'+fmt)).write_bytes(response.content)
            result[kind]['stages']=structured['stages']
            result[kind]['explanation']=structured['explanation']
        else: artifacts=job['artifacts']
        checks={}
        for name,url in artifacts.items():
            if not isinstance(url,str) or not url.startswith('/api/'): continue
            response=researcher.get(url); response.raise_for_status(); assert response.content
            checks[name]={'bytes':len(response.content),'sha256':hashlib.sha256(response.content).hexdigest()}
        result[kind]['artifacts_verified']=checks
        (output/'receipt.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({'kind':kind,'case':case['case_code'],'status':job['status'],'artifacts':list(checks)}),flush=True)
    print(str(output),flush=True)

if __name__=='__main__': main()
