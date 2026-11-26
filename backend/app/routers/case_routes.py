import os
import re
import json
import uuid
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..preprocessing import run_pipeline
from ..audit import log_action
from ..report import build_report_data, build_csv, build_pdf
from app.stenosis_pipeline import run_stenosis_pipeline
from app.ml import predict_mask
from app.analysis import analyze_vessels


router = APIRouter(prefix="/cases", tags=["Cases"])

UPLOAD_DIR = "uploads"
PROCESSED_DIR = os.path.join(UPLOAD_DIR, "processed")
ALLOWED_EXT = {".png", ".jpg", ".jpeg"}

VIEW_ALL_ROLES = {"admin", "researcher", "data_scientist"}
WRITE_ROLES = {"clinician", "admin"}
PREPROCESS_ROLES = {"clinician", "admin", "data_scientist"}

# stage file names written by preprocessing.run_pipeline, with report labels
STAGE_LABELS = [
    ("1_original", "Original"),
    ("2_normalized", "Normalized"),
    ("3_denoised", "Denoised"),
    ("4_contrast", "Contrast enhanced"),
    ("5_roi", "ROI crop"),
    ("6_model_input", "Model input"),
]


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


def pipeline_json_path(case_id):
    return os.path.join(UPLOAD_DIR, "results", f"case_{case_id}_pipeline.json")


def run_and_save_pipeline(case, db):
    """Run the full stenosis pipeline for a case and save its output as JSON."""
    results_dir = os.path.join(UPLOAD_DIR, "results")
    image_path = os.path.join(UPLOAD_DIR, case.image_path)

    def segment_fn(path, task):
        prefix = f"case_{case.id}_{task}"
        out = predict_mask(path, task, results_dir, prefix)
        res = {
            "task": task,
            "mask_url": f"/uploads/results/{out['mask']}",
            "overlay_url": f"/uploads/results/{out['overlay']}",
            "model_version": out["model_version"],
        }
        if task == "syntax":
            vessel = analyze_vessels(
                path, os.path.join(results_dir, out["mask"]), results_dir, prefix
            )
            res["vessel"] = {
                **vessel,
                "clean_url": f"/uploads/results/{vessel['clean']}",
                "centerline_url": f"/uploads/results/{vessel['centerline']}",
            }
        return res

    result = run_stenosis_pipeline(case.id, image_path, segment_fn)
    data = result.to_dict()

    os.makedirs(results_dir, exist_ok=True)
    with open(pipeline_json_path(case.id), "w") as f:
        json.dump(data, f, default=str)

    case.analysis_status = "Stenosis pipeline complete"
    db.commit()
    return data


def get_preprocessing_stages(case):
    """Preprocessing stage images of a case (created now if they do not exist yet)."""
    files = [f"case_{case.id}_{name}.png" for name, _ in STAGE_LABELS]
    if not all(os.path.exists(os.path.join(PROCESSED_DIR, f)) for f in files):
        try:
            run_pipeline(
                os.path.join(UPLOAD_DIR, case.image_path), PROCESSED_DIR, f"case_{case.id}"
            )
        except Exception:
            return []
    stages = []
    for (name, label), fname in zip(STAGE_LABELS, files):
        if os.path.exists(os.path.join(PROCESSED_DIR, fname)):
            stages.append({"name": label, "url": f"/uploads/processed/{fname}"})
    return stages


def get_case_history(db, case_id, limit=30):
    """Audit-log entries that belong to one case, oldest first."""
    rows = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.detail.like(f"%case {case_id}%"))
        .order_by(models.AuditLog.id.asc())
        .all()
    )
    pattern = re.compile(rf"case {case_id}(?!\d)")
    out = []
    for r in rows:
        if r.detail and pattern.search(r.detail):
            out.append(
                {
                    "time": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "-",
                    "user": r.user_name,
                    "role": r.role,
                    "action": r.action,
                    "detail": r.detail,
                }
            )
    return out[-limit:]


def load_json_file(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(text))


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


@router.get("/model-metrics")
def model_metrics(user: models.User = Depends(auth.get_current_user)):
    """Test-set performance of the stenosis classifier (written by evaluate.py)."""
    path = os.path.join("weights", "classifier_metrics.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Run evaluate.py first")
    with open(path) as f:
        return json.load(f)


@router.get("/model-comparison")
def model_comparison(user: models.User = Depends(auth.get_current_user)):
    """U-Net vs Attention U-Net results (weights/model_comparison.json)."""
    data = load_json_file(os.path.join("weights", "model_comparison.json"))
    if data is None:
        raise HTTPException(status_code=404, detail="model_comparison.json not found")
    return data


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
            PROCESSED_DIR,
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


@router.post("/{case_id}/stenosis-pipeline")
def stenosis_pipeline(
    case_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    case = get_case_for_user(case_id, db, user)
    require_role(user, PREPROCESS_ROLES, "Your role cannot run analysis")
    if not case.image_path:
        raise HTTPException(status_code=400, detail="Upload a scan first")

    try:
        data = run_and_save_pipeline(case, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Stenosis pipeline failed: {e}")

    log_action(db, user, "stenosis_pipeline", f"case {case.id}")
    return data


@router.get("/{case_id}/report")
def case_report(
    case_id: int,
    format: str = "pdf",
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    """Download the full analysis report of a case as pdf, csv or json."""
    fmt = format.lower()
    if fmt not in {"pdf", "csv", "json"}:
        raise HTTPException(status_code=400, detail="format must be pdf, csv or json")

    case = get_case_for_user(case_id, db, user)
    if not case.image_path:
        raise HTTPException(status_code=400, detail="Upload a scan first")

    # use the saved pipeline output; run the pipeline once if there is none yet
    pipeline = load_json_file(pipeline_json_path(case.id))
    if pipeline is None and user.role in PREPROCESS_ROLES:
        try:
            pipeline = run_and_save_pipeline(case, db)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Stenosis pipeline failed: {e}")
    if pipeline is None:
        raise HTTPException(
            status_code=400,
            detail="No analysis yet. Ask a clinician to run the stenosis pipeline for this case.",
        )

    metrics = load_json_file(os.path.join("weights", "classifier_metrics.json"))
    comparison = load_json_file(os.path.join("weights", "model_comparison.json"))

    data = build_report_data(
        case,
        pipeline,
        metrics,
        user.name,
        preprocessing=get_preprocessing_stages(case),
        history=get_case_history(db, case.id),
        comparison=comparison,
    )
    filename = f"report_{safe_name(case.patient_id)}.{fmt}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    log_action(db, user, f"report_{fmt}", f"case {case.id}")

    if fmt == "json":
        return Response(json.dumps(data, indent=2, default=str), media_type="application/json", headers=headers)
    if fmt == "csv":
        return Response(build_csv(data), media_type="text/csv", headers=headers)
    return Response(build_pdf(data), media_type="application/pdf", headers=headers)