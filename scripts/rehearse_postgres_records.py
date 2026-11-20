"""Seed or verify synthetic records in explicitly named disposable databases."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.database import Base
from app.models import User, Case, VolumeAnalysis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--seed', action='store_true')
    args = parser.parse_args()
    url = make_url(args.url)
    if url.host not in ('localhost', '127.0.0.1') or not (url.database or '').startswith('corovision_rehearsal_'):
        raise SystemExit('Only localhost databases named corovision_rehearsal_* are permitted')
    engine = create_engine(url)
    try:
        if args.seed:
            Base.metadata.create_all(engine)
        with Session(engine) as db:
            if args.seed:
                if db.scalar(select(User).limit(1)) is not None:
                    raise SystemExit('Refusing to seed a populated database')
                user = User(id='rehearsal-user', email='synthetic@example.invalid',
                            password_hash='disabled-synthetic-account', role='researcher')
                db.add(user)
                db.flush()
                db.add(Case(id='rehearsal-case', owner_id=user.id, case_code='SYNTHETIC-PG-REHEARSAL',
                            modality='CTA', anatomy='coronary'))
                db.flush()
                db.add(VolumeAnalysis(id='rehearsal-run', case_id='rehearsal-case', created_by=user.id,
                    status='completed', input_kind='synthetic_fixture', source_sha256='0'*64,
                    result_json=json.dumps({'fixture': True, 'severity': None, 'quality': 'abstained'})))
                db.commit()
            case = db.get(Case, 'rehearsal-case')
            run = db.get(VolumeAnalysis, 'rehearsal-run')
            assert case and run and run.case_id == case.id
            assert case.owner_id == run.created_by == 'rehearsal-user'
            assert json.loads(run.result_json)['severity'] is None
            snapshot = {'case': case.case_code, 'run': run.id, 'source': run.source_sha256,
                        'result': json.loads(run.result_json)}
            print(json.dumps({'status': 'PASS', 'snapshot': snapshot,
                'sha256': hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()}, sort_keys=True))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
