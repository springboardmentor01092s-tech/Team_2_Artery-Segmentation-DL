"""Case-scoped, persisted research inference with immutable per-run artifacts."""
import hashlib
import json
import logging
from pathlib import Path
import re
import shutil
import threading
from uuid import uuid4

from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db,SessionLocal
from .models import TaskInferenceRun,User
from .security import current_user
from .task_models import SPECS,catalog,installed,run_image

router=APIRouter(tags=['Task inference'])
SLOTS=threading.BoundedSemaphore(2)
RUN_LOCK=threading.Lock()


def output(row):
    from .main import STORAGE
    result=json.loads(row.result_json) if row.result_json else None
    folder=STORAGE/'task_runs'/row.id/'outputs'
    names=[p.name for p in folder.iterdir() if artifact_name(p.name)] if row.status=='completed' and folder.is_dir() else []
    return dict(id=row.id,case_id=row.case_id,image_id=row.image_id,task_id=row.task_id,
        status=row.status,error=row.error,created_at=row.created_at,input_sha256=row.input_sha256,result=result,
        artifacts={name:f'/api/cases/{row.case_id}/task-analyses/{row.id}/artifacts/{name}' for name in names})


def artifact_name(name):
    return name in {'overlay.png','mask.png','probability.npz','result.json'} or bool(re.fullmatch(r'instance_\d{3}\.png',name))


def execute(identity):
    from .main import STORAGE
    try:
        with RUN_LOCK,SessionLocal() as db:
            row=db.get(TaskInferenceRun,identity)
            if not row or row.status!='queued':return
            row.status='running';db.commit()
            folder=STORAGE/'task_runs'/row.id
            try:
                source=folder/'input.png'
                if hashlib.sha256(source.read_bytes()).hexdigest()!=row.input_sha256:raise ValueError('Input integrity mismatch')
                result=run_image(row.task_id,source,folder/'outputs')
                result.update(run_id=row.id,case_id=row.case_id,image_id=row.image_id,input_sha256=row.input_sha256)
                (folder/'outputs/result.json').write_text(json.dumps(result,indent=2,allow_nan=False))
                row.result_json=json.dumps(result,allow_nan=False);row.status='completed'
            except Exception:
                logging.getLogger('corovision.operations').exception('Task inference failed run=%s',identity)
                row.status='failed';row.error='Task inference failed; no verified output was produced. Check the task checkpoint and input contract.'
            db.commit()
    finally:SLOTS.release()


@router.get('/api/task-models')
def task_models(user:User=Depends(current_user)):
    if user.role=='viewer':raise HTTPException(403,'Research models require an operational or research role')
    return dict(tasks=catalog(),research_only=True,automatic_activation=False)


class TaskInput(BaseModel):
    image_id:str
    task_id:str
    research_confirmed:bool=False


@router.post('/api/cases/{case_id}/task-analyses',status_code=202)
def create_task(case_id:str,data:TaskInput,background:BackgroundTasks,user:User=Depends(current_user),db:Session=Depends(get_db)):
    from .main import analysis_input,STORAGE,audit
    image=analysis_input(data.image_id,user,db)
    if image.case_id!=case_id:raise HTTPException(404,'Image does not belong to this case')
    spec=SPECS.get(data.task_id)
    if not spec or spec['kind'] not in {'vessel','boxes','instances'}:raise HTTPException(422,'Select an available 2D task adapter')
    if not data.research_confirmed:raise HTTPException(422,'Confirm research-only use')
    if not installed(data.task_id):raise HTTPException(503,'Hash-verified task checkpoint unavailable')
    if (image.width,image.height)!=(512,512):raise HTTPException(422,'Use an unenhanced 512-square XCA asset')
    source=Path(image.preview_path);digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if image.processed_sha256 and digest!=image.processed_sha256:raise HTTPException(409,'Saved input hash changed')
    if not SLOTS.acquire(blocking=False):raise HTTPException(429,'Task queue is full')
    try:
        row=TaskInferenceRun(id=str(uuid4()),case_id=case_id,image_id=image.id,created_by=user.id,
            task_id=data.task_id,input_sha256=digest,status='queued')
        folder=STORAGE/'task_runs'/row.id;folder.mkdir(parents=True,exist_ok=False)
        shutil.copyfile(source,folder/'input.png');db.add(row);audit(db,user.id,'research_task_inference_queued',case_id);db.commit()
        response=output(row)
    except Exception:SLOTS.release();raise
    background.add_task(execute,row.id)
    return response


@router.get('/api/cases/{case_id}/task-analyses')
def list_tasks(case_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    from .main import accessible_case,require_case_role
    require_case_role(user);accessible_case(case_id,user,db)
    return [output(row) for row in db.scalars(select(TaskInferenceRun).where(TaskInferenceRun.case_id==case_id).order_by(TaskInferenceRun.created_at.desc()).limit(50))]


@router.get('/api/cases/{case_id}/task-analyses/{run_id}/artifacts/{name}')
def artifact(case_id:str,run_id:str,name:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    from .main import accessible_case,require_case_role,STORAGE
    require_case_role(user);accessible_case(case_id,user,db)
    row=db.get(TaskInferenceRun,run_id)
    if not row or row.case_id!=case_id or row.status!='completed' or not artifact_name(name):raise HTTPException(404,'Task artifact unavailable')
    path=STORAGE/'task_runs'/row.id/'outputs'/name
    if not path.is_file():raise HTTPException(404,'Task artifact missing')
    return FileResponse(path,media_type='image/png' if name.endswith('.png') else 'application/json' if name.endswith('.json') else 'application/octet-stream',filename=name)
