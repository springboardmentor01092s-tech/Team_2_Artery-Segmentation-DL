"""Live code-to-output demonstration through authenticated application APIs.

Runs frozen inference on the existing de-identified demo asset. No training.
Credentials stay local and are never printed or embedded in generated files.
"""
import argparse
import json
import time
from pathlib import Path
from uuid import uuid4
from html import escape
import httpx

ROOT = Path(__file__).resolve().parents[1]


def excerpt(path, start, stop):
    lines = path.read_text().splitlines()
    return '\n'.join(f'{i+1}: {line}' for i,line in enumerate(lines) if start <= i+1 <= stop)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-id', default='7b62cf5c-7deb-4a38-bfa7-e8bcfafa5ac6')
    args=parser.parse_args()
    credentials=json.loads((ROOT/'backend/demo-credentials.json').read_text())['accounts']
    account=next(a for a in credentials if a['email']=='researcher.demo@example.com')
    destination=ROOT/'reports'/('live_code_demo_'+uuid4().hex[:8])
    destination.mkdir(exist_ok=False)
    print('1. Frozen-model inference code: backend/app/trained_release.py')
    print(excerpt(ROOT/'backend/app/trained_release.py',85,107))
    print('\n2. Geometry implementation: backend/app/analysis_model.py, analyze_vessel_geometry')
    print('   Skeleton -> graph paths -> spacing-aware lengths -> approximate widths. No optimizer.')
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=120) as client:
        response=client.post('/api/auth/login',json={'email':account['email'],'password':account['password']})
        response.raise_for_status();client.headers['Authorization']='Bearer '+response.json()['access_token']
        response=client.post(f'/api/images/{args.asset_id}/analysis/jobs',json={'idempotency_key':uuid4().hex})
        response.raise_for_status();job=response.json();deadline=time.monotonic()+180
        print('\n3. Submitted actual frozen inference job:',job['id'],flush=True)
        previous=None
        while True:
            response=client.get(job['status_url']);response.raise_for_status();job=response.json()
            if job['status']!=previous: print('   Job:',job['status'],flush=True);previous=job['status']
            if job['status'] in {'completed','failed'}:break
            if time.monotonic()>deadline:raise TimeoutError('Job still pending; inspect its saved status rather than resubmitting.')
            time.sleep(.5)
        if job['status']!='completed':raise RuntimeError(str(job.get('error_detail')))
        response=client.get(job['result_url']);response.raise_for_status();result=response.json()
        assert result['id']==job['result_event_id'] and result['image_id']==args.asset_id
        (destination/'result.json').write_text(json.dumps(result,indent=2))
        base=f'/api/images/{args.asset_id}/analyses/{result["id"]}/panels/'
        figures=[]
        for key,label in [('original','Original image'),('processed','Processed input'),('artery_mask','Predicted artery mask'),('centerline','Extracted centerline'),('boundary','Mask boundary'),('overlay','Artery and stenosis overlay')]:
            response=client.get(base+key);response.raise_for_status();assert response.headers.get('content-type','').startswith('image/')
            (destination/(key+'.png')).write_bytes(response.content)
            figures.append(f'<figure><img src="{key}.png" alt="{label}"><figcaption>{label}</figcaption></figure>')
        geometry=result['vessel_analysis']
        summary={key:geometry.get(key) for key in ['centerline_length','mean_diameter','diameter_unit','branching_points','endpoints','calibration']}
        print('\n4. Fresh measured outputs:',json.dumps(summary,indent=2))
        print('   Stenosis mask pixels:',result['stenosis_pixels'])
        print('   Severity:',result['structured_result']['severity']['status'])
        snippets=excerpt(ROOT/'backend/app/trained_release.py',85,107)+'\n\n'+excerpt(ROOT/'backend/app/analysis_model.py',177,203)
        html='<!doctype html><meta charset="utf-8"><title>CoroVision live code demonstration</title><style>body{font:16px/1.6 system-ui;margin:30px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}figure{margin:0}img{width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef2f6;padding:16px}</style>'
        html+=f'<h1>Fresh frozen-inference demonstration</h1><p>Run {escape(result["id"])} · model {escape(result["model_version"])}. No training. Research estimates, not diagnosis. No reference mask was supplied, so image-specific accuracy is unavailable.</p>'
        html+='<h2>Executed model path</h2><pre>'+escape(snippets)+'</pre><h2>Newly generated outputs</h2><section>'+''.join(figures)+'</section><h2>Measurements</h2><pre>'+escape(json.dumps(summary,indent=2))+'</pre><p>Widths are approximate; physical calibration and validated local/reference diameter protocol are required for narrowing. Severity remains unavailable. This is not an advanced-model comparison.</p>'
        (destination/'index.html').write_text(html)
        print('\n5. Open this fresh output in Chrome:',destination/'index.html')


if __name__=='__main__':main()
