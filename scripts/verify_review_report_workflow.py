"""Read/export the browser-created public test snapshot; never create medical decisions."""
import csv
import hashlib
import json
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    fixture = json.loads((ROOT/'reports/public_image_integration_receipt.json').read_text())
    accounts = json.loads((ROOT/'backend/demo-credentials.json').read_text())['accounts']
    account = next(a for a in accounts if a['email'] == 'radiologist.demo@example.com')
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=60) as client:
        login = client.post('/api/auth/login', json={'email': account['email'], 'password': account['password']})
        login.raise_for_status()
        client.headers['Authorization'] = 'Bearer ' + login.json()['access_token']
        base = f"/api/cases/{fixture['case_id']}/research-reports"
        versions = client.get(base); versions.raise_for_status()
        assert versions.json(), 'Save the public test report through the UI first'
        index = versions.json()[-1]
        snapshot = client.get(base+'/'+index['id']); snapshot.raise_for_status(); snapshot = snapshot.json()
        run = snapshot['analysis']
        assert run['image_id'] == fixture['asset_id'] == snapshot['image']['id']
        assert snapshot['human_review']['analysis_event_id'] == run['id']
        assert snapshot['human_review']['stenosis_severity'] == 'insufficient_evidence'
        history = client.get(f"/api/images/{fixture['asset_id']}/analyses"); history.raise_for_status()
        assert len(history.json()) >= 3 and history.json()[0]['id'] != run['id'], 'Rerun required for preservation check'
        checks = {}
        for format in ('json', 'csv', 'pdf'):
            response = client.get(base+'/'+index['id']+'/export/'+format); response.raise_for_status()
            if format == 'json':
                assert response.json() == snapshot
            elif format == 'csv':
                row = next(csv.DictReader(response.text.splitlines()))
                assert row['analysis_run_id'] == run['id'] and int(row['artery_pixels']) == run['artery_pixels']
            else:
                assert response.content.startswith(b'%PDF-')
                Path('/tmp/corovision-public-research-report.pdf').write_bytes(response.content)
            checks[format] = {'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}
        receipt = {'case_id': fixture['case_id'], 'asset_id': fixture['asset_id'], 'report_id': index['id'],
                   'report_analysis_id': run['id'], 'latest_analysis_id': history.json()[0]['id'],
                   'history_runs': len(history.json()), 'report_preserved_after_rerun': True,
                   'run_linked_review': True, 'exports_verified': checks,
                   'scope': 'Public development-exposed ARCADE fixture, workflow acceptance only; no clinical validation.'}
        (ROOT/'reports/review_report_integration_receipt.json').write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt))


if __name__ == '__main__':
    main()
