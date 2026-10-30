import os
import json
import uuid
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..preprocessing import run_pipeline
from ..audit import log_action

router = APIRouter(prefix="/cases", tags=["Cases"])

UPLOAD_DIR = "uploads"
ALLOWED_EXT = {".png", ".jpg", ".jpeg"}

VIEW_ALL_ROLES = {"admin", "researcher", "data_scientist"}
WRITE_ROLES = {"clinician", "admin"}
PREPROCESS_ROLES = {"clinician", "admin", "data_scientist"}


def require_role(user, roles, message):
    if user.role not in roles:
        raise HTTPException(status_code=403, detail=message)


def get_case_for_user(case_id, db, user, write=False) -> models.Case:
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    is_owner = case.owner_id == user.id
    if write:
        if user.role == "admin" or (user.role in WRITE_ROLES and is_owner):
            return case
        raise HTTPException(status_code=403, detail="Your role cannot modify this case")
    if is_owner or user.role in VIEW_ALL_ROLES:
        return case
    raise HTTPException(status_code=404, detail="Case not found")


@router.post("", response_model=schemas.CaseOut, status_code=201)
def create_case(
    data: schemas.CaseCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    require_role(user, WRITE_ROLES, "Your role cannot create cases")
    case = models.Case(**data.model_dump(), owner_id=user.id)
    db.add(case)
    db.commit()
    db.refresh(case)
    log_action(db, user, "create_case", f"patient {case.patient_id} (case {case.id})")
    return case


@router.get("", response_model=list[schemas.CaseOut])
def list_cases(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.Case)
    if user.role not in VIEW_ALL_ROLES:
        q = q.filter(models.Case.owner_id == user.id)
    return q.order_by(models.Case.id.desc()).all()


@router.get("/results/summary")
def results_summary(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    """Which tasks have saved results, per case: {"2": ["syntax", "stenosis"]}"""
    q = db.query(models.SegmentationResult.case_id, models.SegmentationResult.task).join(
        models.Case, models.Case.id == models.SegmentationResult.case_id
    )
    if user.role not in VIEW_ALL_ROLES:
        q = q.filter(models.Case.owner_id == user.id)
    summary = {}
    for case_id, task in q.all():
        summary.setdefault(case_id, []).append(task)
    return summary


@router.get("/{case_id}", response_model=schemas.CaseOut)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    return get_case_for_user(case_id, db, user)


@router.put("/{case_id}", response_model=schemas.CaseOut)
def update_case(
    case_id: int,
    data: schemas.CaseCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    case = get_case_for_user(case_id, db, user, write=True)
    for key, value in data.model_dump().items():
        setattr(case, key, value)
    db.commit()
    db.refresh(case)
    log_action(db, user, "update_case", f"patient {case.patient_id} (case {case.id})")
    return case


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    case = get_case_for_user(case_id, db, user, write=True)
    info = f"patient {case.patient_id} (case {case.id})"
    db.query(models.SegmentationResult).filter(
        models.SegmentationResult.case_id == case.id
    ).delete()
    db.delete(case)
    db.commit()
    log_action(db, user, "delete_case", info)


@router.post("/{case_id}/upload", response_model=schemas.CaseOut)
def upload_image(
    case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    case = get_case_for_user(case_id, db, user, write=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Only PNG or JPG images are allowed")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    name = f"case_{case_id}_{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, name), "wb") as out:
        shutil.copyfileobj(file.file, out)
    case.image_path = name
    db.commit()
    db.refresh(case)
    log_action(db, user, "upload_scan", f"case {case.id}: {file.filename}")
    return case


@router.post("/{case_id}/preprocess")
def preprocess_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    case = get_case_for_user(case_id, db, user)
    require_role(user, PREPROCESS_ROLES, "Your role cannot run preprocessing")
    if not case.image_path:
        raise HTTPException(status_code=400, detail="Upload a scan first")
    try:
        stages = run_pipeline(
            os.path.join(UPLOAD_DIR, case.image_path),
            os.path.join(UPLOAD_DIR, "processed"),
            f"case_{case_id}",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preprocessing failed: {e}")
    case.analysis_status = "Preprocessed"
    db.commit()
    log_action(db, user, "preprocess", f"case {case.id}")
    return {
        "stages": [
            {"name": s["name"], "url": f"/uploads/processed/{s['file']}"}
            for s in stages
        ]
    }


@router.post("/{case_id}/segment")
def segment_case(
    case_id: int,
    task: str = "syntax",
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    from ..ml import predict_mask, MODEL_INFO

    case = get_case_for_user(case_id, db, user)
    require_role(user, PREPROCESS_ROLES, "Your role cannot run analysis")
    if task not in MODEL_INFO:
        raise HTTPException(status_code=400, detail="task must be 'syntax' or 'stenosis'")
    if not case.image_path:
        raise HTTPException(status_code=400, detail="Upload a scan first")
    try:
        out = predict_mask(
            os.path.join(UPLOAD_DIR, case.image_path),
            task,
            os.path.join(UPLOAD_DIR, "results"),
            f"case_{case_id}_{task}",
        )
        from ..analysis import analyze_vessels
        results_dir = os.path.join(UPLOAD_DIR, "results")
        vessel = analyze_vessels(
            os.path.join(UPLOAD_DIR, case.image_path),
            os.path.join(results_dir, out["mask"]),
            results_dir,
            f"case_{case_id}_{task}",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {e}")

    case.model_version = out["model_version"]
    case.analysis_status = "Analysis complete"

    payload = {
        "task": task,
        "mask_url": f"/uploads/results/{out['mask']}",
        "overlay_url": f"/uploads/results/{out['overlay']}",
        "foreground_percent": out["foreground_percent"],
        "max_probability": out["max_probability"],
        "threshold": out["threshold"],
        "model_version": out["model_version"],
        "vessel": {
            **vessel,
            "clean_url": f"/uploads/results/{vessel['clean']}",
            "centerline_url": f"/uploads/results/{vessel['centerline']}",
        },
    }

    # save (or replace) the result for this case + task
    saved = (
        db.query(models.SegmentationResult)
        .filter(
            models.SegmentationResult.case_id == case.id,
            models.SegmentationResult.task == task,
        )
        .first()
    )
    if saved:
        saved.result_json = json.dumps(payload)
        saved.created_at = datetime.now(timezone.utc)
    else:
        db.add(
            models.SegmentationResult(
                case_id=case.id, task=task, result_json=json.dumps(payload)
            )
        )
    db.commit()
    log_action(db, user, f"segment_{task}", f"case {case.id}")
    return payload


@router.get("/{case_id}/results")
def get_saved_results(
    case_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    """Saved segmentation results for a case, by task: {"syntax": {...}, "stenosis": {...}}"""
    case = get_case_for_user(case_id, db, user)
    rows = (
        db.query(models.SegmentationResult)
        .filter(models.SegmentationResult.case_id == case.id)
        .all()
    )
    return {r.task: json.loads(r.result_json) for r in rows}