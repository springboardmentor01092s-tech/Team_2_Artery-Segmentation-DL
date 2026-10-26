"""Authenticated, read-only research evidence dashboard; never starts training."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from .evaluation_workspace import readers

APP_ROOT=Path(__file__).resolve().parents[2]
router=APIRouter(prefix='/api/research-progress',tags=['Research progress'])


def research_root():
    configured=os.getenv('COROVISION_RESEARCH_ROOT')
    if configured:
        return Path(configured).resolve()
    parent=APP_ROOT.parent
    return parent if (parent/'research_optimization').is_dir() else APP_ROOT


def evidence_paths():
    root=research_root()
    return {
        'framework-status':('Framework verification',root/'reports/model_framework_20261026/IMPLEMENTATION_STATUS.md',root),
        'framework-inventory':('Baseline inventory',root/'reports/model_framework_20261026/baseline_inventory.json',root),
        'framework-matrix':('Technique compatibility matrix',root/'reports/model_framework_20261026/COMPATIBILITY.md',root),
        'pilot-result':('ARCADE measured comparison',root/'experiments/arcade_topology_pilot_20261025/comparison.json',root),
        'pilot-plan':('ARCADE trial configuration',root/'experiments/arcade_topology_pilot_20261025/config.json',root),
        'artery-next-plan':('Prepared artery postprocessing plan',root/'experiments/arcade_frozen_holes_20261026/PLAN.md',root),
        'quality-notes':('Dataset quality findings',root/'reports/improvement_20261025/QUALITY_ACTIONS.md',root),
        'next-experiments':('Ranked next work',root/'research_optimization/NEXT_EXPERIMENTS.md',root),
        'download-intake':('Kaggle download verification',APP_ROOT/'reports/KAGGLE_DOWNLOAD_INTAKE_20261026.md',APP_ROOT),
        'download-manifest':('Kaggle checkpoint hashes',APP_ROOT/'reports/kaggle_download_reconciliation_20261026.json',APP_ROOT),
        'dashboard-verification':('Progress dashboard verification',APP_ROOT/'reports/RESEARCH_PROGRESS_DASHBOARD.md',APP_ROOT),
        'live-result':('Latest monitored research result',root/'reports/research_live/latest_result.json',root),
        'live-history':('Monitored job history',root/'reports/research_live/history.jsonl',root),
        'artery-local-plan':('Frozen artery local-cache adapter',root/'experiments/arcade_frozen_holes_20261026/LOCAL_CACHE_ADAPTER.md',root),
        'artery-frozen-result':('Frozen artery postprocessing comparison',root/'experiments/arcade_frozen_holes_20261026/local_evaluation/comparison.json',root),
    }


def safe_file(path,root):
    return path.resolve().is_relative_to(root.resolve()) and path.is_file() and path.stat().st_size<=4*1024**2


def load(path,root,warnings):
    if not safe_file(path,root):
        return None
    try:
        return json.loads(path.read_text())
    except (ValueError,OSError):
        warnings.append('A research evidence file could not be read; its data is unavailable.')
        return None


def utc_mtime(path):
    return datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()


def live_telemetry(root,warnings):
    row=load(root/'reports/research_live/state.json',root,warnings)
    default=dict(state='not_connected',confirmed_running_jobs=None,
        detail='No monitored local job has reported yet. Kaggle live telemetry is not connected.')
    if not isinstance(row,dict):return default
    try:
        heartbeat=datetime.fromisoformat(row['heartbeat_at'])
        age=(datetime.now(timezone.utc)-heartbeat).total_seconds()
        state=row['state']
        if state not in {'running','completed','rejected','blocked','failed'} or not re.fullmatch('[0-9a-f]{32}',row['job_id']):return default
        if state=='running':
            alive=False
            if type(row.get('pid')) is int and row['pid']>0:
                try:os.kill(row['pid'],0);alive=True
                except (ProcessLookupError,PermissionError):pass
            if not alive or not 0<=age<=45:state='stale'
        completed=row.get('completed_units');total=row.get('total_units')
        if type(completed) is not int or completed<0:completed=None
        if type(total) is not int or total<=0:total=None
        if completed is not None and total is not None and completed>total:completed=None
        return dict(state=state,confirmed_running_jobs=1 if state=='running' else 0 if state in {'completed','rejected','blocked','failed'} else None,
            job_id=row['job_id'],title=str(row.get('title','Research job'))[:180],
            task=str(row.get('task',''))[:80],kind=str(row.get('kind',''))[:80],
            step=str(row.get('step',''))[:240],heartbeat_at=heartbeat.isoformat(),
            started_at=row.get('started_at'),finished_at=row.get('finished_at'),
            completed_units=completed,total_units=total,
            elapsed_seconds=row.get('elapsed_seconds'),
            detail='Local worker heartbeat connected. Counts are completed work units, not accuracy gains. Kaggle live telemetry is not connected.' if state!='stale' else 'Worker heartbeat is stale or its process stopped. Running status is not confirmed.')
    except (ValueError,KeyError,TypeError,OverflowError):return default


def snapshot():
    warnings=[];root=research_root();paths=evidence_paths(); evidence=[]
    for key,(label,path,base) in paths.items():
        available=safe_file(path,base)
        evidence.append(dict(id=key,label=label,available=available,
            updated_at=utc_mtime(path) if available else None,
            url='/api/research-progress/evidence/'+key if available else None))
    available={e['id']:e['available'] for e in evidence}
    ledger=load(root/'reports/improvement_20261025/improvement_ledger.json',root,warnings) or {}
    if not isinstance(ledger,dict): ledger={}
    pilot=load(paths['pilot-result'][1],root,warnings)
    downloads=load(paths['download-manifest'][1],APP_ROOT,warnings)
    experiments=[]
    if isinstance(pilot,dict) and isinstance(pilot.get('baseline'),dict) and isinstance(pilot.get('candidate'),dict):
        b,c=pilot['baseline'],pilot['candidate']
        if all(type(x) in (int,float) and 0<=x<=1 for x in (b.get('mean_dice'),c.get('mean_dice'))):
            experiments.append(dict(id='arcade-topology-20261025',task='ARCADE artery',
                title='32-update topology-loss pilot',status=pilot.get('decision','unknown'),
                metric='Mean per-image Dice',baseline=b['mean_dice'],candidate=c['mean_dice'],
                delta=c['mean_dice']-b['mean_dice'],baseline_fn=b.get('fn'),candidate_fn=c.get('fn'),
                baseline_fp=b.get('fp'),candidate_fp=c.get('fp'),evidence_id='pilot-result',
                measured_at=utc_mtime(paths['pilot-result'][1]),
                limitation='Development-exposed validation; historical completed trial, not a running job.'))
    inventory=load(paths['framework-inventory'][1],root,warnings)
    frozen=load(paths['artery-frozen-result'][1],root,warnings)
    if isinstance(frozen,dict) and frozen.get('training_performed') is False and frozen.get('test_used') is False:
        b,c=frozen.get('baseline',{}),frozen.get('candidate',{})
        if isinstance(b,dict) and isinstance(c,dict) and all(type(x) in (int,float) and 0<=x<=1 for x in (b.get('mean_dice'),c.get('mean_dice'))):
            experiments.append(dict(id='arcade-frozen-holes-20261026',task='ARCADE artery',
                title='Fixed enclosed-hole postprocessing',status=frozen.get('decision','unknown'),
                metric='Mean per-image Dice',baseline=b['mean_dice'],candidate=c['mean_dice'],delta=c['mean_dice']-b['mean_dice'],
                baseline_fn=b.get('fn'),candidate_fn=c.get('fn'),baseline_fp=b.get('fp'),candidate_fp=c.get('fp'),
                evidence_id='artery-frozen-result',measured_at=utc_mtime(paths['artery-frozen-result'][1]),
                limitation='Frozen checkpoint, unchanged development-validation cohort; not clinical validation or automatic activation.'))
    tasks=[]
    titles={'arcade_artery':'ARCADE artery','arcade_instances':'ARCADE anatomical instances',
        'arcade_stenosis':'ARCADE stenosis','dca134':'DCA134','stenosis_archive':'Stenosis archive',
        'cadica':'CADICA','imagecas':'ImageCAS','imagecasx':'ImageCAS-X','aortaseg':'AortaSeg',
        'hepatic_vessel':'Hepatic vessels','hepatic_tumour':'Hepatic tumours','ica_intake':'ICA intake','severity':'Severity modeling'}
    if isinstance(inventory,list):
        for item in inventory[:30]:
            if not isinstance(item,dict): continue
            identity=item.get('task');enabled=item.get('enabled') is True
            tasks.append(dict(id=identity,title=titles.get(identity,str(identity)),
                status='No new evaluation recorded' if enabled else 'Excluded / held',
                checkpoint_present=item.get('checkpoint_sha256') is not None,
                checkpoint_sha256=item.get('checkpoint_sha256'),
                detail=str(item.get('limitation',''))[:500],evidence_id='framework-inventory'))
        for task in tasks:
            if task['id']=='arcade_artery' and available['artery-next-plan']:
                task.update(status='Prepared · not executed',detail='A frozen-output hole-repair test is prepared. The previous measured trial was rejected; baseline retained.',evidence_id='artery-next-plan')
                if len(experiments)>1:task.update(status=experiments[-1]['status'].replace('_',' '),detail='Frozen postprocessing comparison saved. Production baseline unchanged.',evidence_id='artery-frozen-result')
            if task['id'] in {'imagecas','imagecasx'} and downloads:
                task.update(status='Resume checkpoint quarantined',detail='Downloaded resume tensors differ from the original baseline. Matched validation is pending; no activation.',evidence_id='download-intake')
    registered=unmatched=bundles=None
    if isinstance(downloads,dict):
        checkpoints=[row for row in downloads.get('checkpoints',[]) if isinstance(row,dict)]
        registered=sum(bool(row.get('handoff_matches')) for row in checkpoints)
        unmatched=sum(not row.get('handoff_matches') for row in checkpoints)
        bundles=sum(isinstance(row,dict) and row.get('status')=='staged_verified' for row in downloads.get('archives',[]))
    framework_tests=None
    if available['framework-status']:
        text=paths['framework-status'][1].read_text()
        match=re.search(r'\*\*(\d+) tests passed',text)
        if match: framework_tests=int(match[1])
    activity=[]
    journal=APP_ROOT/'reports/research_progress/activity.jsonl'
    if safe_file(journal,APP_ROOT):
        for line in journal.read_text().splitlines()[-100:]:
            try:
                event=json.loads(line)
                if not isinstance(event,dict): continue
                if event.get('evidence_id') not in paths or event.get('status') not in {'completed','prepared','rejected','blocked'}:
                    continue
                timestamp=datetime.fromisoformat(event['recorded_at'])
                if timestamp.tzinfo is None: continue
                activity.append(dict(id=str(event['id'])[:80],title=str(event['title'])[:180],
                    detail=str(event.get('detail',''))[:600],status=event['status'],
                    recorded_at=timestamp.isoformat(),evidence_id=event['evidence_id']))
            except (ValueError,KeyError,TypeError):
                warnings.append('An invalid activity entry was omitted.')
    activity.sort(key=lambda row:row['recorded_at'],reverse=True)
    telemetry=live_telemetry(root,warnings)
    latest=load(root/'reports/research_live/latest_result.json',root,warnings)
    next_trial=latest.get('local_trial_not_before') if isinstance(latest,dict) else None
    next_action=str(latest.get('next_action','Run the next eligible matched validation-only comparison.'))[:600] if isinstance(latest,dict) else 'ARCADE first: verify lesion annotations, then run one matched validation-only comparison.'
    if available['artery-local-plan'] and not available['artery-frozen-result']:
        next_action='ARCADE artery: metadata-compatible 512-grid baseline caches located. The fixed enclosed-hole comparison is queued for the next eligible schedule run; full per-case baseline parity must pass at execution. Stenosis empty-annotation review remains unresolved. No retraining or automatic activation.'
    history=root/'reports/research_live/history.jsonl'
    if safe_file(history,root):
        for line in history.read_text().splitlines()[-30:]:
            try:
                job=json.loads(line);identity=job['job_id']
                if not re.fullmatch('[0-9a-f]{32}',identity) or job['state'] not in {'completed','rejected','blocked','failed'}:continue
                path=root/'reports/research_live/jobs'/identity/'result.json'
                key='job-'+identity;present=safe_file(path,root)
                evidence.append(dict(id=key,label=str(job.get('title','Research job'))[:180],available=present,
                    updated_at=utc_mtime(path) if present else None,url='/api/research-progress/evidence/'+key if present else None))
                timestamp=datetime.fromisoformat(job['finished_at'])
                if timestamp.tzinfo is None:continue
                activity.append(dict(id=identity,title=str(job.get('title','Research job'))[:180],
                    detail=f"{job.get('kind','Research')} · {job.get('completed_units',0)} completed units. {str(job.get('step',''))[:240]}",
                    status=job['state'],recorded_at=timestamp.isoformat(),evidence_id=key))
            except (ValueError,KeyError,TypeError):warnings.append('An invalid job-history entry was omitted.')
    activity.sort(key=lambda row:row['recorded_at'],reverse=True)
    last=max((e['updated_at'] for e in evidence if e['updated_at']),default=None)
    return dict(checked_at=datetime.now(timezone.utc).isoformat(),last_evidence_at=last,
        telemetry=telemetry,next_local_trial_at=next_trial,
        training_authorized=ledger.get('policy',{}).get('training_authorized') if isinstance(ledger.get('policy',{}),dict) else None,
        summary=dict(recorded_experiments=len(experiments),
            measured_gains=sum(e['delta']>0 and e['status']=='candidate_requires_independent_review' for e in experiments),
            framework_tests=framework_tests,downloaded_bundles=bundles,
            verified_checkpoint_matches=registered,quarantined_checkpoints=unmatched),
        experiments=experiments,tasks=tasks,activity=activity[:30],evidence=evidence,warnings=warnings,
        next_action=next_action,
        caveat='Counts summarize the evidence shown here, not every historical experiment. Framework tests and downloads are not accuracy gains.')


@router.get('')
def progress(user=Depends(readers)):
    return snapshot()


@router.get('/evidence/{identity}')
def get_evidence(identity:str,user=Depends(readers)):
    row=evidence_paths().get(identity)
    if row is None and re.fullmatch('job-[0-9a-f]{32}',identity):
        root=research_root();row=('Monitored result',root/'reports/research_live/jobs'/identity[4:]/'result.json',root)
    if row is None or not safe_file(row[1],row[2]):
        raise HTTPException(404,'Evidence unavailable')
    _,path,_=row
    content=path.read_text().replace(str(research_root()),'[workspace]').replace(str(APP_ROOT),'[application]')
    suffix='json' if path.suffix=='.json' else 'md'
    return Response(content,media_type='application/json' if suffix=='json' else 'text/plain',
        headers={'Content-Disposition':f'attachment; filename="{identity}.{suffix}"',
                 'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
