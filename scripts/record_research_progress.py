"""Record an evidence-linked completed research action; never launches a job."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--title',required=True)
    parser.add_argument('--detail',default='')
    parser.add_argument('--status',choices=['completed','prepared','rejected','blocked'],required=True)
    parser.add_argument('--evidence-id',required=True)
    args=parser.parse_args()
    if len(args.title)>180 or len(args.detail)>600:
        raise ValueError('Activity text too long')
    import sys
    sys.path.insert(0,str(ROOT/'backend'))
    from app.research_progress import evidence_paths,safe_file
    evidence=evidence_paths().get(args.evidence_id)
    if evidence is None or not safe_file(evidence[1],evidence[2]):
        raise ValueError('A real allowlisted evidence file is required')
    event=dict(id=uuid4().hex,recorded_at=datetime.now(timezone.utc).isoformat(),
        title=args.title,detail=args.detail,status=args.status,evidence_id=args.evidence_id)
    path=ROOT/'reports/research_progress/activity.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as handle:
        handle.write(json.dumps(event)+'\n')
    print(json.dumps(event))


if __name__=='__main__':
    main()
