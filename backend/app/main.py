import os
import json
import re
import hashlib
from contextlib import asynccontextmanager
from datetime import date, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import BASE_DIR, Base, SessionLocal, engine, get_db
from .migrations import upgrade_local_schema
from .auth_ext import identity_out, normalized_username, resolve_user, router as auth_ext_router
from .models import (
    ActionGrant, AnalysisEvent, AnalysisJob, AnalysisRun, AuditEvent, AuthSession, Case, CaseAccess,
    CaseComment, ClinicalReview, Image, LoginThrottle, Notification, NotificationDismissal,
    ReportRevision, RoleAccessRequest, User, UserIdentity, UserProfile, now
)
from .analysis_service import analyze, model_version, models_ready, validation_summary
from . import trained_release
from .analysis_result import build_result
from .inference_jobs import InferenceWorker
from .action_policy import allowed_action, effective_actions, CONDITIONAL_ACTIONS
from .case_contract import validate_case_configuration, supports_current_inference, case_modalities, case_tasks, validate_case_routes
from .preprocessing import InvalidImage, SUPPORTED_EXTENSIONS, TARGET_SIZE, STANDARD_PIPELINES, prepare_image, processed_spacing_mm, content_geometry
from .security import (
    AuthContext, create_token, current_auth, current_user, hash_password,
    session_expiry, verify_password,
)

STORAGE = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage"))
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
SUPPORTED_IMAGE_EXTENSIONS = SUPPORTED_EXTENSIONS


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    upgrade_local_schema(engine)
    with SessionLocal() as db:
        for run in db.scalars(select(AnalysisRun)).all():
            if db.scalar(select(AnalysisEvent).where(AnalysisEvent.image_id == run.image_id,
                                                     AnalysisEvent.overlay_path == run.overlay_path)) is None:
                db.add(AnalysisEvent(id=run.id, image_id=run.image_id,
                                     model_version=run.model_version, artery_pixels=run.artery_pixels,
                                     stenosis_pixels=run.stenosis_pixels, overlay_path=run.overlay_path,
                                     validation_json=json.dumps({"models": {}, "provenance_status": "legacy_backfill_unverified"}), created_at=run.created_at))
        db.commit()
    (STORAGE / "uploads").mkdir(parents=True, exist_ok=True)
    (STORAGE / "preprocessed").mkdir(parents=True, exist_ok=True)
    (STORAGE / "analysis").mkdir(parents=True, exist_ok=True)
    worker = None
    if os.getenv("COROVISION_INFERENCE_WORKER", "1") == "1":
        worker = InferenceWorker(execute_analysis_job)
        worker.start()
    try:
        yield
    finally:
        if worker:
            worker.close()


app = FastAPI(title="CoroVision AI API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+)(:\d+)?$",
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_ext_router)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(default="", max_length=100)
    username: str | None = None


class LoginIn(BaseModel):
    identifier: str | None = None
    email: EmailStr | None = None
    password: str
    remember: bool = False


class ProfileIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    current_password: str | None = None


class PasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)


class CaseIn(BaseModel):
    modalities: list[Literal["XCA", "CT", "CTA", "MRA"]] | None = Field(default=None, min_length=1, max_length=4)
    intended_tasks: list[Literal["artery_segmentation", "stenosis_localization", "artery_and_stenosis", "volume_preparation"]] | None = Field(default=None, min_length=1, max_length=4)
    case_code: str = Field(min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)
    patient_code: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{3,40}$")
    age_band: Literal["under_30", "30_39", "40_49", "50_59", "60_69", "70_79", "80_plus", "unknown"] | None = None
    gender: Literal["female", "male", "other", "unknown"] | None = None
    medical_history: list[Literal["hypertension", "diabetes", "prior_mi", "prior_pci", "hyperlipidemia", "none", "unknown"]] = Field(default_factory=list)
    risk_factors: list[Literal["smoking", "family_history", "obesity", "sedentary", "hypertension", "diabetes", "none", "unknown"]] = Field(default_factory=list)
    clinical_notes: str | None = Field(default=None, max_length=500)
    scan_date: date | None = None
    modality: Literal["XCA", "CT", "CTA", "MRA"] = "XCA"
    anatomy: Literal["coronary", "aorta", "cerebral", "hepatic"] = "coronary"
    intended_task: Literal["artery_segmentation", "stenosis_localization", "artery_and_stenosis", "volume_preparation"] = "artery_and_stenosis"
    source_dataset: str | None = Field(default=None, max_length=120)
    source_reference: str | None = Field(default=None, max_length=200)
    clinical_metadata_enabled: bool = False

    @field_validator("clinical_notes", "notes")
    @classmethod
    def reject_obvious_identifiers(cls, value):
        if value and (re.search(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", value)
                      or re.search(r"\b\+?\d[\d .()-]{8,}\d\b", value)):
            raise ValueError("Remove email addresses and phone numbers from de-identified notes")
        return value


class CasePatch(BaseModel):
    modality: Literal["XCA", "CT", "CTA", "MRA"] | None = None
    anatomy: Literal["coronary", "aorta", "cerebral", "hepatic"] | None = None
    intended_task: Literal["artery_segmentation", "stenosis_localization", "artery_and_stenosis", "volume_preparation"] | None = None
    source_dataset: str | None = Field(default=None, max_length=120)
    source_reference: str | None = Field(default=None, max_length=200)
    clinical_metadata_enabled: bool | None = None
    patient_code: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{3,40}$")
    age_band: Literal["under_30", "30_39", "40_49", "50_59", "60_69", "70_79", "80_plus", "unknown"] | None = None
    gender: Literal["female", "male", "other", "unknown"] | None = None
    medical_history: list[Literal["hypertension", "diabetes", "prior_mi", "prior_pci", "hyperlipidemia", "none", "unknown"]] | None = None
    risk_factors: list[Literal["smoking", "family_history", "obesity", "sedentary", "hypertension", "diabetes", "none", "unknown"]] | None = None
    clinical_notes: str | None = Field(default=None, max_length=500)
    scan_date: date | None = None

    @field_validator("clinical_notes")
    @classmethod
    def reject_obvious_identifiers(cls, value):
        return CaseIn.reject_obvious_identifiers(value)


class RoleIn(BaseModel):
    role: str


class StatusIn(BaseModel):
    status: Literal["active", "suspended", "pending", "deactivated"]


class ReportApprovalPermissionIn(BaseModel):
    enabled: bool


class ReportDecisionIn(BaseModel):
    decision: Literal["approved", "changes_requested"]
    notes: str | None = Field(default=None, max_length=1000)


class ModelActivationIn(BaseModel):
    architecture: Literal["tiny_unet", "attention_unet"]


class CaseCommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    category: Literal["general", "quality", "model", "review"] = "general"


class ClinicalReviewIn(BaseModel):
    decision: Literal["approved", "needs_followup", "rejected", "reviewed"]
    stenosis_severity: Literal["mild", "moderate", "severe", "none", "unspecified"] | None = "unspecified"
    notes: str | None = Field(default=None, max_length=1000)


class CaseAccessIn(BaseModel):
    user_email_or_id: str
    access_level: Literal["read", "review", "edit"] = "read"


ALL_ROLES = {"admin", "doctor", "clinician", "researcher", "ml_engineer", "technician", "viewer"}
CASE_ROLES = {"researcher", "doctor", "clinician", "technician", "viewer", "admin"}
ROLE_CASE_CREATORS = {"admin", "doctor", "clinician", "researcher", "technician"}
ROLE_IMAGE_UPLOADERS = {"admin", "doctor", "clinician", "researcher", "technician"}
ROLE_ANALYSIS_RUNNERS = {"admin", "doctor", "clinician", "researcher", "technician"}
ROLE_CLINICAL_REVIEWERS = {"doctor", "clinician", "admin"}
ROLE_MODEL_MANAGERS = {"admin", "researcher", "ml_engineer"}
ROLE_EXPORTERS = {"admin", "doctor", "clinician", "researcher"}

# Explicit local demo roster. This is disabled unless CV_LOCAL_DEMO_SHARING=1.
# The seeded team uses de-identified cases; regular users keep explicit assignments.
DEMO_TEAM_ACCESS = {
    "radiologist.demo@example.com": ("clinician", "edit"),
    "doctor.demo@example.com": ("doctor", "edit"),
    "researcher.demo@example.com": ("researcher", "read"),
    "technician.demo@example.com": ("technician", "edit"),
    "viewer.demo@example.com": ("viewer", "read"),
}


def share_case_with_demo_team(case: Case, owner: User, db: Session) -> int:
    if os.getenv("CV_LOCAL_DEMO_SHARING") != "1" or owner.email not in DEMO_TEAM_ACCESS and owner.email not in {
        "admin.demo@example.com", "mlengineer.demo@example.com"
    }:
        return 0
    shared = 0
    for email, (role, level) in DEMO_TEAM_ACCESS.items():
        target = db.scalar(select(User).where(User.email == email))
        if not target or target.id == owner.id or target.role != role or target.status != "active":
            continue
        existing = db.scalar(select(CaseAccess).where(CaseAccess.case_id == case.id, CaseAccess.user_id == target.id))
        if existing:
            continue
        db.add(CaseAccess(case_id=case.id, user_id=target.id, access_level=level, assigned_by=owner.id))
        shared += 1
    return shared


def require_roles(*allowed_roles: str):
    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.role}' is not authorized for this action. Required: {', '.join(allowed_roles)}",
            )
        return user
    return checker


def require_case_role(user: User = Depends(current_user)) -> User:
    if user.role not in CASE_ROLES:
        raise HTTPException(status_code=403, detail="Case access requires an authorized role")
    return user


def user_out(user: User, db: Session) -> dict:
    profile = db.get(UserProfile, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "status": getattr(user, "status", "active"),
        "can_approve_reports": bool(user.can_approve_reports),
        "permissions": effective_actions(user, db),
        "display_name": profile.display_name if profile else "",
        "created_at": user.created_at,
        **identity_out(user, db),
    }


def audit(db: Session, user_id: str, action: str, case_id: str | None = None):
    db.add(AuditEvent(user_id=user_id, action=action, case_id=case_id))


def notify_case(db: Session, case: Case, actor_id: str, kind: str, message: str,
                roles: set[str] | None = None) -> None:
    recipient_ids = {case.owner_id} | {entry.user_id for entry in case.access_list}
    for recipient_id in recipient_ids:
        if recipient_id == actor_id:
            continue
        recipient = db.get(User, recipient_id)
        if recipient and recipient.status == "active" and (roles is None or recipient.role in roles):
            db.add(Notification(user_id=recipient_id, case_id=case.id, kind=kind, message=message))


def report_out(report: ReportRevision) -> dict:
    return {"id": report.id, "version": report.version, "status": report.status,
            "created_by": report.created_by, "created_at": report.created_at,
            "approved_by": report.approved_by, "approved_at": report.approved_at}


def case_out(case: Case, db: Session | None = None, viewer: User | None = None) -> dict:
    latest_review = None
    reviews_list = []
    if hasattr(case, "reviews") and case.reviews:
        for r in sorted(case.reviews, key=lambda item: (
            item.created_at.replace(tzinfo=timezone.utc).timestamp()
            if item.created_at.tzinfo is None else item.created_at.timestamp(), item.id
        ), reverse=True):
            reviewer_name = ""
            if db:
                p = db.get(UserProfile, r.reviewer_id)
                reviewer_name = p.display_name if p else ""
            reviews_list.append({
                "id": r.id,
                "case_id": r.case_id,
                "reviewer_id": r.reviewer_id,
                "reviewer_name": reviewer_name,
                "decision": r.decision,
                "stenosis_severity": r.stenosis_severity,
                "notes": r.notes,
                "created_at": r.created_at,
            })
        if reviews_list:
            latest_review = reviews_list[0]

    latest_analyses: dict[str, str] = {}
    if db and case.images:
        events = db.scalars(
            select(AnalysisEvent).where(AnalysisEvent.image_id.in_([im.id for im in case.images]))
            .order_by(AnalysisEvent.created_at.desc(), AnalysisEvent.id.desc())
        ).all()
        for event in events:
            latest_analyses.setdefault(event.image_id, event.id)
    assignment = next((item for item in case.access_list if viewer and item.user_id == viewer.id), None) if viewer else None
    owner = bool(viewer and case.owner_id == viewer.id)
    assigned_editor = bool(assignment and assignment.access_level in {"edit", "admin"})
    assigned_reviewer = bool(assignment and assignment.access_level in {"review", "edit", "admin"})
    permissions = {
        "can_edit": bool(viewer and viewer.role in ROLE_CASE_CREATORS and (owner or assigned_editor)),
        "can_upload": bool(viewer and db and allowed_action(viewer, "case:upload", db) and (owner or assigned_editor)),
        "can_run_analysis": bool(viewer and db and supports_current_inference(case) and allowed_action(viewer, "analysis:run", db) and (owner or assigned_reviewer)),
        "can_review": bool(viewer and viewer.role in ROLE_CLINICAL_REVIEWERS and (case.owner_id == viewer.id or assigned_reviewer)),
        "can_export": bool(viewer and db and allowed_action(viewer, "analysis:export", db)),
        "can_assign": owner,
        "can_delete": owner,
        "can_submit_report": bool(viewer and viewer.role in ROLE_CLINICAL_REVIEWERS and
                                  (case.owner_id == viewer.id or assigned_reviewer)),
        "can_approve_report": bool(viewer and viewer.role in ROLE_CLINICAL_REVIEWERS and
                                   viewer.can_approve_reports and (case.owner_id == viewer.id or assigned_reviewer)),
    }
    return {
        "id": case.id,
        "owner_id": case.owner_id,
        "assigned_doctors": [
            {"id": doctor.id, "name": ((db.get(UserProfile, doctor.id).display_name if db and db.get(UserProfile, doctor.id) else "") or "Assigned clinician"), "role": doctor.role}
            for doctor in {person.id: person for person in
                           [case.owner, *[access.user for access in case.access_list
                                         if access.access_level in {"review", "edit", "admin"}]]
                           if person and person.role in {"doctor", "clinician"}}.values()
        ],
        "case_code": case.case_code,
        "patient_code": case.patient_code,
        "age_band": case.age_band,
        "gender": case.gender,
        "medical_history": json.loads(case.medical_history or "[]"),
        "risk_factors": json.loads(case.risk_factors or "[]"),
        "clinical_notes": case.clinical_notes,
        "scan_date": case.scan_date,
        "modality": case.modality,
        "modalities": case_modalities(case),
        "intended_tasks": case_tasks(case),
        "processing_routes": validate_case_routes(case_modalities(case), case.anatomy, case_tasks(case))[2],
        "anatomy": case.anatomy,
        "intended_task": case.intended_task,
        "source_dataset": case.source_dataset,
        "source_reference": case.source_reference,
        "clinical_metadata_enabled": case.clinical_metadata_enabled,
        "inference_compatible": supports_current_inference(case),
        "status": case.status,
        "workflow_status": case.workflow_status,
        "processing_status": case.processing_status,
        "report_status": case.report_status,
        "report_version": case.report_version,
        "report_approved_by": case.report_approved_by,
        "report_approved_at": case.report_approved_at,
        "permissions": permissions,
        "notes": case.notes,
        "created_at": case.created_at,
        "reviews": reviews_list,
        "latest_review": latest_review,
        "report_revisions": [report_out(item) for item in sorted(case.report_revisions, key=lambda item: item.version, reverse=True)],
        "comments": [{"id": item.id, "user_id": item.user_id, "body": item.body,
                      "category": item.category, "created_at": item.created_at}
                     for item in sorted(case.comments, key=lambda item: item.created_at, reverse=True)],
        "images": [
            {"id": im.id, "original_name": im.original_name, "width": im.width, "height": im.height,
             "modality": json.loads(im.preprocessing_config_json or "{}").get("modality", case.modality),
             "spacing_mm": im.spacing_mm, "processed_spacing_mm": im.processed_spacing_mm, "roi_box": im.roi_box,
             "frame_index": im.frame_index, "page_index": im.page_index,
             "latest_analysis_id": latest_analyses.get(im.id),
             "preprocessing": json.loads(im.preprocessing_json or "[]"),
             "processing_record": json.loads(im.preprocessing_config_json or "{}"),
             "preview_url": f"/api/images/{im.id}/preview",
             "source_url": f"/api/images/{im.id}/source"}
            for im in case.images
        ],
    }


def accessible_case(case_id: str, user: User, db: Session, required_action: str = "read") -> Case:
    case = db.get(Case, case_id)
    if not case or case.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.owner_id == user.id:
        return case
    assignment = db.scalar(
        select(CaseAccess).where(CaseAccess.case_id == case.id, CaseAccess.user_id == user.id)
    )
    if assignment:
        if required_action == "read":
            return case
        if required_action in {"edit", "upload"} and assignment.access_level in {"edit", "admin"}:
            return case
        if required_action == "review" and assignment.access_level in {"review", "edit", "admin"}:
            return case
        if required_action == "analyze" and assignment.access_level in {"review", "edit", "admin"}:
            return case
        raise HTTPException(status_code=403, detail="Insufficient case access level")
    raise HTTPException(status_code=404, detail="Case not found")


@app.get("/api/health")
def health():
    return {"status": "ok", "stage": "research-prototype", "models_ready": models_ready()}


@app.post("/api/auth/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    username = normalized_username(data.username)
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    if username and db.scalar(select(UserIdentity).where(UserIdentity.username == username)):
        raise HTTPException(status_code=409, detail="Username already in use")
    user = User(email=email, password_hash=hash_password(data.password), role="viewer", status="active")
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id, display_name=data.display_name.strip()))
    db.add(UserIdentity(user_id=user.id, username=username))
    audit(db, user.id, "registered")
    db.commit()
    db.refresh(user)
    return user_out(user, db)


@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    identifier = (data.identifier or data.email or "").strip()
    if not identifier:
        raise HTTPException(status_code=422, detail="Provide an email or username")
    user = resolve_user(identifier, db)
    guard = db.get(LoginThrottle, user.id) if user else None
    if guard and guard.blocked_until:
        blocked_until = guard.blocked_until.replace(tzinfo=timezone.utc) if guard.blocked_until.tzinfo is None else guard.blocked_until
        if blocked_until > now():
            raise HTTPException(status_code=429, detail="Too many attempts; try again later")
    if not user or not verify_password(data.password, user.password_hash):
        if user:
            if guard is None:
                guard = LoginThrottle(user_id=user.id, failed_attempts=0)
                db.add(guard)
            guard.failed_attempts += 1
            if guard.failed_attempts >= 5:
                guard.blocked_until = now() + timedelta(minutes=15)
                guard.failed_attempts = 0
            audit(db, user.id, "login_failed")
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if getattr(user, "status", "active") in {"suspended", "deactivated"}:
        audit(db, user.id, "login_blocked_suspended")
        db.commit()
        raise HTTPException(status_code=403, detail="Account is suspended or deactivated. Contact an administrator.")
    if guard:
        guard.failed_attempts = 0
        guard.blocked_until = None
    session = AuthSession(user_id=user.id, expires_at=session_expiry(data.remember))
    db.add(session)
    db.flush()
    audit(db, user.id, "login")
    db.commit()
    return {"access_token": create_token(user, session), "token_type": "bearer",
            "expires_at": session.expires_at}


@app.get("/api/auth/demo-accounts")
def list_demo_accounts(db: Session = Depends(get_db)):
    creds_path = BASE_DIR / "backend" / "demo-credentials.json"
    if not creds_path.is_file():
        creds_path = BASE_DIR / "demo-credentials.json"
    if not creds_path.is_file():
        return {"accounts": []}
    try:
        data = json.loads(creds_path.read_text())
        accounts = []
        for acc in data.get("accounts", []):
            user = db.scalar(select(User).where(User.email == acc["email"]))
            if user and user.status == "active":
                profile = db.get(UserProfile, user.id)
                session = AuthSession(user_id=user.id, expires_at=session_expiry(True))
                db.add(session)
                db.flush()
                token = create_token(user, session)
                accounts.append({
                    "id": user.id,
                    "name": (profile.display_name if profile and profile.display_name else "") or acc.get("role", user.email),
                    "email": user.email,
                    "role": user.role,
                    "label": acc.get("role", user.role),
                    "token": token,
                })
        db.commit()
        return {"accounts": accounts}
    except Exception:
        return {"accounts": []}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_out(user, db)


@app.patch("/api/auth/me")
def update_profile(
    data: ProfileIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if data.display_name is None and data.email is None:
        raise HTTPException(status_code=422, detail="Provide a profile field to update")
    profile = db.get(UserProfile, user.id)
    if not profile:
        profile = UserProfile(user_id=user.id, display_name="")
        db.add(profile)
    if data.display_name is not None:
        profile.display_name = data.display_name.strip()
    if data.email is not None and data.email.lower() != user.email:
        if not data.current_password or not verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=403, detail="Current password required to change email")
        if db.scalar(select(User).where(User.email == data.email.lower())):
            raise HTTPException(status_code=409, detail="Email already registered")
        user.email = data.email.lower()
    audit(db, user.id, "profile_updated")
    db.commit()
    return user_out(user, db)


@app.post("/api/auth/change-password")
def change_password(
    data: PasswordIn,
    auth: AuthContext = Depends(current_auth),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, auth.user.password_hash):
        raise HTTPException(status_code=403, detail="Current password is incorrect")
    if data.current_password == data.new_password:
        raise HTTPException(status_code=422, detail="Choose a different new password")
    auth.user.password_hash = hash_password(data.new_password)
    for session in db.scalars(
        select(AuthSession).where(AuthSession.user_id == auth.user.id, AuthSession.revoked_at.is_(None))
    ):
        session.revoked_at = now()
    audit(db, auth.user.id, "password_changed")
    db.commit()
    return {"detail": "Password changed; sign in again on all devices"}


@app.get("/api/auth/sessions")
def list_sessions(auth: AuthContext = Depends(current_auth), db: Session = Depends(get_db)):
    sessions = db.scalars(
        select(AuthSession).where(AuthSession.user_id == auth.user.id).order_by(AuthSession.created_at.desc())
    ).all()
    return [
        {"id": item.id, "created_at": item.created_at, "expires_at": item.expires_at,
         "active": item.revoked_at is None and
         (item.expires_at.replace(tzinfo=timezone.utc) if item.expires_at.tzinfo is None else item.expires_at) > now(),
         "current": item.id == auth.session.id}
        for item in sessions
    ]


@app.post("/api/auth/logout")
def logout(auth: AuthContext = Depends(current_auth), db: Session = Depends(get_db)):
    auth.session.revoked_at = now()
    audit(db, auth.user.id, "logout")
    db.commit()
    return {"detail": "Signed out"}


@app.post("/api/auth/logout-all")
def logout_all(auth: AuthContext = Depends(current_auth), db: Session = Depends(get_db)):
    for session in db.scalars(
        select(AuthSession).where(AuthSession.user_id == auth.user.id, AuthSession.revoked_at.is_(None))
    ):
        session.revoked_at = now()
    audit(db, auth.user.id, "logout_all")
    db.commit()
    return {"detail": "All sessions signed out"}


@app.get("/api/auth/audit")
def my_audit(user: User = Depends(current_user), db: Session = Depends(get_db)):
    events = db.scalars(
        select(AuditEvent).where(AuditEvent.user_id == user.id)
        .order_by(AuditEvent.created_at.desc()).limit(100)
    ).all()
    return [
        {"id": event.id, "action": event.action, "case_id": event.case_id,
         "created_at": event.created_at}
        for event in events
    ]


@app.post("/api/cases", status_code=201)
def create_case(data: CaseIn, user: User = Depends(require_roles(*ROLE_CASE_CREATORS)), db: Session = Depends(get_db)):
    if not allowed_action(user, "case:create", db):
        raise HTTPException(403, "Case creation needs a separate operational grant")
    # Legacy callers specifying only CTA get a preparation case, never XCA inference.
    if data.modality != "XCA" and "intended_task" not in data.model_fields_set:
        data.intended_task = "volume_preparation"
    modalities, tasks, routes = validate_case_routes(data.modalities if data.modalities is not None else [data.modality], data.anatomy,
                                                    data.intended_tasks if data.intended_tasks is not None else [data.intended_task])
    data.modality = "XCA" if "XCA" in modalities else modalities[0]
    data.intended_task = next(row["intended_task"] for row in routes if row["modality"] == data.modality)
    if not data.clinical_metadata_enabled and (data.medical_history or data.risk_factors or data.clinical_notes):
        raise HTTPException(422, "Enable permitted de-identified clinical metadata before entering history or notes")
    code = data.case_code.strip()
    if not code:
        raise HTTPException(status_code=422, detail="Case code cannot be blank")
    if db.scalar(select(Case).where(Case.owner_id == user.id, Case.case_code == code, Case.deleted_at.is_(None))):
        raise HTTPException(409, "This case reference already exists in your workspace; open that case instead")
    case = Case(owner_id=user.id, case_code=code, notes=data.notes,
                patient_code=data.patient_code, age_band=data.age_band, gender=data.gender,
                medical_history=json.dumps(data.medical_history), risk_factors=json.dumps(data.risk_factors),
                clinical_notes=data.clinical_notes,
                scan_date=data.scan_date.isoformat() if data.scan_date else None,
                modality=data.modality, anatomy=data.anatomy, intended_task=data.intended_task,
                modalities_json=json.dumps(modalities), intended_tasks_json=json.dumps(tasks),
                source_dataset=data.source_dataset, source_reference=data.source_reference,
                clinical_metadata_enabled=data.clinical_metadata_enabled)
    db.add(case)
    db.flush()
    if share_case_with_demo_team(case, user, db):
        audit(db, user.id, "demo_case_shared", case.id)
    db.flush()
    notify_case(db, case, user.id, "case_created", f"{case.case_code} is ready for intake")
    db.add(AuditEvent(user_id=user.id, action="case_created", case_id=case.id))
    db.commit()
    db.refresh(case)
    return case_out(case, db, user)


@app.get("/api/cases")
def list_cases(user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    assigned_case_ids = select(CaseAccess.case_id).where(CaseAccess.user_id == user.id)
    statement = select(Case).where(
        ((Case.owner_id == user.id) | (Case.id.in_(assigned_case_ids))),
        Case.deleted_at.is_(None),
    ).order_by(Case.created_at.desc())
    cases = db.scalars(statement).all()
    return [case_out(case, db, user) for case in cases]


@app.get("/api/tasks")
def my_tasks(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role not in CASE_ROLES:
        return []
    cases = list_cases(user, db)
    tasks = []
    for case in cases:
        stage = case["workflow_status"]
        permissions = case["permissions"]
        title, view = None, "cases"
        if stage in {"draft", "validation_failed", "changes_requested"} and permissions["can_upload"]:
            title = "Complete intake or correct the study"
        elif stage == "ready_for_analysis" and permissions["can_run_analysis"]:
            title, view = "Run AI analysis", "analysis"
        elif stage == "pending_review" and permissions["can_review"]:
            title, view = "Review AI findings", "cases"
        elif stage == "reviewed" and permissions["can_submit_report"]:
            title, view = "Submit the reviewed report", "reports"
        elif stage == "report_pending_approval" and permissions["can_approve_report"]:
            title, view = "Approve or return the report", "reports"
        if title:
            tasks.append({"case_id": case["id"], "case_code": case["case_code"],
                          "title": title, "view": view, "workflow_status": stage})
    return tasks


@app.get("/api/notifications")
def my_notifications(deleted: bool = False, user: User = Depends(current_user), db: Session = Depends(get_db)):
    dismissed = select(NotificationDismissal.notification_id).where(NotificationDismissal.user_id == user.id)
    items = db.scalars(select(Notification).where(Notification.user_id == user.id,
                       Notification.id.in_(dismissed) if deleted else Notification.id.not_in(dismissed))
                       .order_by(Notification.created_at.desc()).limit(100)).all()
    levels = {"model_stenosis_flag": "medium", "model_multiple_regions": "medium", "analysis_quality_review": "low",
              "model_uncertainty_review": "low",
              "validation_failed": "high", "analysis_failed": "high",
              "severe_stenosis_reviewed": "critical", "analysis_ready": "informational"}
    return [{"id": item.id, "case_id": item.case_id, "kind": item.kind,
             "alert_level": levels.get(item.kind, "informational"),
             "message": item.message, "created_at": item.created_at,
             "read_at": item.read_at} for item in items]


@app.get("/api/dashboard/analytics")
def dashboard_analytics(user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    """Aggregate only cases this user is authorized to read; model pixels are not diagnoses."""
    cases = list_cases(user, db)
    case_by_id = {item["id"]: item for item in cases}
    image_to_case = {image["id"]: item["id"] for item in cases for image in item["images"]}
    image_ids = list(image_to_case)
    events = db.scalars(select(AnalysisEvent).where(AnalysisEvent.image_id.in_(image_ids))
                        .order_by(AnalysisEvent.created_at.desc(), AnalysisEvent.id.desc())).all() if image_ids else []
    latest_by_case: dict[str, AnalysisEvent] = {}
    seen_images: set[str] = set()
    latest_by_image: dict[str, AnalysisEvent] = {}
    for event in events:
        case_id = image_to_case.get(event.image_id)
        if not case_id:
            continue
        if event.image_id not in seen_images:
            latest_by_image[event.image_id] = event
            seen_images.add(event.image_id)
        latest_by_case.setdefault(case_id, event)
    latest_reviews = [item.get("latest_review") for item in cases if item.get("latest_review")]
    severity = {key: sum(1 for review in latest_reviews if (review.get("stenosis_severity") or "unspecified") == key)
                for key in ("none", "mild", "moderate", "severe", "unspecified")}
    flagged = sum(1 for event in latest_by_case.values() if event.stenosis_pixels > 0)
    recent = []
    for event in events:
        case_id = image_to_case.get(event.image_id)
        if not case_id:
            continue
        case = case_by_id[case_id]
        image = next((value for value in case["images"] if value["id"] == event.image_id), None)
        try:
            event_details = json.loads(event.validation_json or "{}")
            vessel_details = event_details.get("vessel_analysis", {})
        except (TypeError, ValueError):
            vessel_details = {}
        recent.append({"id": event.id, "case_id": case_id, "case_code": case["case_code"],
                       "image_name": image["original_name"] if image else "Image",
                       "model_version": event.model_version, "created_at": event.created_at,
                       "stenosis_pixels": event.stenosis_pixels,
                       "model_flagged_region": event.stenosis_pixels > 0,
                       "stenosis_mask_components": vessel_details.get("stenosis_mask_components", 0)})
        if len(recent) == 8:
            break
    processing = {}
    for case in cases:
        key = case.get("processing_status", "unknown")
        processing[key] = processing.get(key, 0) + 1
    return {"total_cases": len(cases), "cases_analyzed": len(latest_by_case),
            "analysis_runs": len(events), "model_flagged_cases": flagged,
            "cases_without_model_flag": len(latest_by_case) - flagged,
            "clinician_severity_distribution": severity, "processing_status": processing,
            "validation_performance": validation_summary() if user.role in ROLE_MODEL_MANAGERS else {}, "recent_analyses": recent,
            "research_only": True}


class NotificationBulkIn(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=100)
    action: Literal["read", "delete", "restore"]


@app.post("/api/notifications/bulk")
def bulk_notifications(payload: NotificationBulkIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ids = set(payload.ids)
    items = db.scalars(select(Notification).where(Notification.id.in_(ids), Notification.user_id == user.id)).all()
    if len(items) != len(ids):
        raise HTTPException(404, "One or more notifications were not found")
    timestamp = now()
    for item in items:
        dismissal = db.get(NotificationDismissal, item.id)
        if payload.action == "read":
            item.read_at = item.read_at or timestamp
        elif payload.action == "delete" and dismissal is None:
            db.add(NotificationDismissal(notification_id=item.id, user_id=user.id, deleted_at=timestamp))
        elif payload.action == "restore" and dismissal is not None:
            db.delete(dismissal)
    audit(db, user.id, f"notifications_{payload.action}")
    db.commit()
    return {"action": payload.action, "ids": sorted(ids), "read_at": timestamp if payload.action == "read" else None}


@app.post("/api/notifications/{notification_id}/read")
def read_notification(notification_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Notification, notification_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.read_at = item.read_at or now()
    db.commit()
    return {"id": item.id, "read_at": item.read_at}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    return case_out(accessible_case(case_id, user, db, required_action="read"), db, user)


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    case = accessible_case(case_id, user, db, required_action="read")
    if user.role != "admin" and case.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the case owner or administrator can delete this case")
    case.deleted_at = now()
    audit(db, user.id, "case_deleted", case.id)
    notify_case(db, case, user.id, "case_deleted", f"{case.case_code} was removed from active cases")
    db.commit()
    return {"detail": "Case moved to administrator trash", "case_id": case.id}


@app.get("/api/admin/trash")
def list_deleted_cases(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    cases = db.scalars(select(Case).where(Case.deleted_at.is_not(None)).order_by(Case.deleted_at.desc())).all()
    return [{"id": case.id, "case_code": case.case_code, "deleted_at": case.deleted_at} for case in cases]


@app.post("/api/admin/trash/{case_id}/restore")
def restore_case(case_id: str, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case or case.deleted_at is None:
        raise HTTPException(status_code=404, detail="Deleted case not found")
    case.deleted_at = None
    audit(db, user.id, "case_restored", case.id)
    notify_case(db, case, user.id, "case_restored", f"{case.case_code} was restored")
    db.commit()
    return {"id": case.id, "case_code": case.case_code, "detail": "Case restored"}


@app.post("/api/cases/{case_id}/comments", status_code=201)
def add_case_comment(case_id: str, data: CaseCommentIn,
                     user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    case = accessible_case(case_id, user, db, required_action="read")
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot add case comments")
    comment = CaseComment(case_id=case.id, user_id=user.id, body=data.body.strip(), category=data.category)
    if not comment.body:
        raise HTTPException(status_code=422, detail="Comment cannot be blank")
    db.add(comment)
    audit(db, user.id, "case_comment_added", case.id)
    notify_case(db, case, user.id, "case_comment", f"New {data.category} note on {case.case_code}")
    db.commit()
    return {"id": comment.id, "case_id": case.id, "body": comment.body,
            "category": comment.category, "created_at": comment.created_at}


@app.patch("/api/cases/{case_id}")
def update_case(case_id: str, data: CasePatch, user: User = Depends(require_roles(*ROLE_CASE_CREATORS)), db: Session = Depends(get_db)):
    case = accessible_case(case_id, user, db, required_action="edit")
    fields = data.model_fields_set
    if not fields:
        raise HTTPException(status_code=422, detail="Provide at least one case field")
    proposed = {name: getattr(data, name) if name in fields else getattr(case, name)
                for name in ("modality", "anatomy", "intended_task")}
    multi = len(case_modalities(case)) > 1 or len(case_tasks(case)) > 1
    if multi and any(proposed[name] != getattr(case, name) for name in proposed):
        raise HTTPException(409, "Multi-modality case routes are fixed at creation; create a new case to change them")
    if "modality" in fields and "intended_task" not in fields and proposed["modality"] != case.modality:
        proposed["intended_task"] = "artery_and_stenosis" if proposed["modality"] == "XCA" else "volume_preparation"
        data.intended_task = proposed["intended_task"]
        fields = fields | {"intended_task"}
    validate_case_configuration(**proposed)
    if case.images and any(proposed[name] != getattr(case, name) for name in proposed):
        raise HTTPException(409, "Create a separate case to change modality, anatomy or task after images are uploaded")
    clinical_enabled = data.clinical_metadata_enabled if "clinical_metadata_enabled" in fields else case.clinical_metadata_enabled
    if clinical_enabled is None:
        raise HTTPException(422, "Clinical metadata setting cannot be null")
    if not clinical_enabled and any(getattr(data, name) for name in ("medical_history", "risk_factors", "clinical_notes") if name in fields):
        raise HTTPException(422, "Enable permitted de-identified clinical metadata before entering history or notes")
    for name in fields:
        value = getattr(data, name)
        if name in {"medical_history", "risk_factors"}:
            value = json.dumps(value or [])
        if name == "scan_date" and value is not None:
            value = value.isoformat()
        setattr(case, name, value)
    if not multi and fields & {"modality", "anatomy", "intended_task"}:
        case.modalities_json = json.dumps([case.modality])
        case.intended_tasks_json = json.dumps([case.intended_task])
    audit(db, user.id, "case_updated", case.id)
    notify_case(db, case, user.id, "case_updated", f"{case.case_code} details were updated")
    db.commit()
    return case_out(case, db, user)


@app.post("/api/cases/{case_id}/review", status_code=201)
def add_clinical_review(
    case_id: str,
    data: ClinicalReviewIn,
    user: User = Depends(require_roles(*ROLE_CLINICAL_REVIEWERS)),
    db: Session = Depends(get_db),
):
    case = accessible_case(case_id, user, db, required_action="review")
    review = ClinicalReview(
        case_id=case.id,
        reviewer_id=user.id,
        decision=data.decision,
        stenosis_severity=data.stenosis_severity,
        notes=data.notes.strip() if data.notes else None,
    )
    db.add(review)
    case.status = f"reviewed:{data.decision}"
    case.workflow_status = "changes_requested" if data.decision in {"needs_followup", "rejected"} else "reviewed"
    case.report_status = "draft"
    audit(db, user.id, f"clinical_review:{data.decision}", case.id)
    notify_case(db, case, user.id, "clinical_review", f"{case.case_code} clinical review: {data.decision}")
    if data.stenosis_severity == "severe":
        notify_case(db, case, user.id, "severe_stenosis_reviewed",
                    f"Clinician-assessed severe stenosis recorded for {case.case_code}")
    db.commit()
    db.refresh(case)
    return case_out(case, db, user)


@app.get("/api/cases/{case_id}/reviews")
def list_clinical_reviews(
    case_id: str,
    user: User = Depends(require_case_role),
    db: Session = Depends(get_db),
):
    case = accessible_case(case_id, user, db, required_action="read")
    return case_out(case, db, user).get("reviews", [])


@app.post("/api/cases/{case_id}/reports/submit", status_code=201)
def submit_report(case_id: str, user: User = Depends(require_roles(*ROLE_CLINICAL_REVIEWERS)),
                  db: Session = Depends(get_db)):
    case = accessible_case(case_id, user, db, required_action="review")
    if case.workflow_status != "reviewed":
        raise HTTPException(status_code=409, detail="Complete the clinical review before submitting a report")
    latest_review = max(case.reviews, key=lambda item: item.created_at.timestamp()) if case.reviews else None
    if not latest_review or latest_review.decision not in {"approved", "reviewed"}:
        raise HTTPException(status_code=409, detail="A completed clinical review is required")
    events = db.scalars(select(AnalysisEvent).join(Image, AnalysisEvent.image_id == Image.id)
                        .where(Image.case_id == case.id).order_by(AnalysisEvent.created_at.desc())).all()
    if not events:
        raise HTTPException(status_code=409, detail="Run AI analysis before submitting a report")
    if case.report_status == "pending_approval":
        raise HTTPException(status_code=409, detail="This report is already awaiting approval")
    version = (case.report_version or 0) + 1
    snapshot = {
        "case_code": case.case_code, "patient_code": case.patient_code,
        "modality": case.modality, "anatomy": case.anatomy, "scan_date": case.scan_date,
        "images": [{"id": image.id, "name": image.original_name} for image in case.images],
        "latest_analysis": event_out(events[0]),
        "clinical_review": {"id": latest_review.id, "decision": latest_review.decision,
                            "stenosis_severity": latest_review.stenosis_severity,
                            "notes": latest_review.notes, "reviewer_id": latest_review.reviewer_id},
        "limitations": "Research model outputs are not calibrated clinical measurements.",
    }
    revision = ReportRevision(case_id=case.id, version=version, snapshot_json=json.dumps(snapshot, default=str),
                              created_by=user.id)
    db.add(revision)
    case.report_version = version
    case.report_status = "pending_approval"
    case.workflow_status = "report_pending_approval"
    audit(db, user.id, f"report_submitted:v{version}", case.id)
    notify_case(db, case, user.id, "report_pending", f"Report v{version} for {case.case_code} awaits approval",
                ROLE_CLINICAL_REVIEWERS)
    db.commit()
    return report_out(revision)


@app.post("/api/cases/{case_id}/reports/{version}/decision")
def decide_report(case_id: str, version: int, data: ReportDecisionIn,
                  user: User = Depends(require_roles(*ROLE_CLINICAL_REVIEWERS)),
                  db: Session = Depends(get_db)):
    if not user.can_approve_reports:
        raise HTTPException(status_code=403, detail="Explicit report approval permission is required")
    case = accessible_case(case_id, user, db, required_action="review")
    revision = db.scalar(select(ReportRevision).where(ReportRevision.case_id == case.id,
                                                       ReportRevision.version == version))
    if not revision or case.report_version != version or revision.status != "pending_approval":
        raise HTTPException(status_code=409, detail="No pending report with this version")
    if revision.created_by == user.id:
        raise HTTPException(status_code=409, detail="The report submitter cannot approve their own report")
    revision.status = data.decision
    if data.decision == "approved":
        revision.approved_by = user.id
        revision.approved_at = now()
        case.report_approved_by = user.id
        case.report_approved_at = revision.approved_at
        case.report_status = "approved"
        case.workflow_status = "complete"
    else:
        case.report_status = "changes_requested"
        case.workflow_status = "changes_requested"
    if data.notes and data.notes.strip():
        db.add(CaseComment(case_id=case.id, user_id=user.id, body=data.notes.strip(), category="review"))
    audit(db, user.id, f"report_{data.decision}:v{version}", case.id)
    notify_case(db, case, user.id, "report_decision", f"Report v{version} for {case.case_code}: {data.decision}")
    db.commit()
    return report_out(revision)


@app.get("/api/cases/{case_id}/reports/{version}")
def get_report_version(case_id: str, version: int,
                       user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    case = accessible_case(case_id, user, db, required_action="read")
    revision = db.scalar(select(ReportRevision).where(ReportRevision.case_id == case.id,
                                                       ReportRevision.version == version))
    if not revision or (user.role == "viewer" and revision.status != "approved"):
        raise HTTPException(status_code=404, detail="Report version not available")
    return {**report_out(revision), "snapshot": json.loads(revision.snapshot_json)}


@app.post("/api/cases/{case_id}/access", status_code=201)
def grant_case_access(
    case_id: str,
    data: CaseAccessIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    case = db.get(Case, case_id)
    if not case or (case.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=403, detail="Only the case owner or administrator can assign access")
    target_user = resolve_user(data.user_email_or_id, db)
    if not target_user:
        target_user = db.get(User, data.user_email_or_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User to assign not found")
    existing = db.scalar(
        select(CaseAccess).where(CaseAccess.case_id == case.id, CaseAccess.user_id == target_user.id)
    )
    if existing:
        existing.access_level = data.access_level
    else:
        db.add(CaseAccess(
            case_id=case.id,
            user_id=target_user.id,
            access_level=data.access_level,
            assigned_by=user.id,
        ))
    audit(db, user.id, f"case_access_granted:{data.access_level}:{target_user.id}", case.id)
    db.add(Notification(user_id=target_user.id, case_id=case.id, kind="case_assigned",
                        message=f"You were assigned to {case.case_code} with {data.access_level} access"))
    db.commit()
    return {"detail": f"Access '{data.access_level}' granted to {target_user.email}"}


@app.get("/api/cases/{case_id}/export")
def export_case(
    case_id: str,
    user: User = Depends(require_roles(*ROLE_EXPORTERS)),
    db: Session = Depends(get_db),
):
    case = accessible_case(case_id, user, db, required_action="read")
    if not allowed_action(user, "analysis:export", db):
        raise HTTPException(403, "Export needs a separate operational grant")
    audit(db, user.id, "case_exported", case.id)
    db.commit()
    return {
        "export_metadata": {
            "exported_at": now().isoformat(),
            "exported_by": user.email,
            "role": user.role,
            "notice": "De-identified research export. Not for direct clinical diagnosis without certified review.",
        },
        "case": case_out(case, db, user),
    }


@app.post("/api/cases/{case_id}/images", status_code=201)
async def upload_image(
    case_id: str,
    file: UploadFile = File(...),
    modality: Literal["XCA", "CT", "CTA", "MRA"] | None = Form(default=None),
    roi: str | None = Form(default=None),
    frame_index: int | None = Form(default=None),
    page_index: int | None = Form(default=None),
    profile: Literal["standard", "research"] = Form(default="standard"),
    standard_pipeline: Literal["baseline", "denoise", "contrast", "balanced"] = Form(default="baseline"),
    denoise: bool = Form(default=False),
    enhance: bool = Form(default=False),
    user: User = Depends(require_roles(*ROLE_IMAGE_UPLOADERS)),
    db: Session = Depends(get_db),
):
    case = accessible_case(case_id, user, db, required_action="upload")
    selected_modalities = case_modalities(case)
    if modality is None and len(selected_modalities) > 1:
        raise HTTPException(422, "Specify the modality for each upload in a multi-modality case")
    upload_modality = modality or case.modality
    if upload_modality != "XCA" or upload_modality not in selected_modalities:
        raise HTTPException(422, "This endpoint accepts enabled XCA frames only; use volume preparation for CT/CTA/MRA")
    if not allowed_action(user, "case:upload", db):
        raise HTTPException(403, "Image upload needs a separate operational grant")
    if profile == "standard" and (denoise or enhance):
        raise HTTPException(status_code=422, detail="Choose the Research profile to enable optional image enhancement")
    if profile == "research" and user.role not in {"admin", "researcher"}:
        raise HTTPException(status_code=403, detail="Research preprocessing is restricted to researchers and administrators")
    if profile == "research" and standard_pipeline != "baseline":
        raise HTTPException(422, "Standard pipelines cannot be mixed with Research options")
    if profile == "standard":
        denoise, enhance = STANDARD_PIPELINES[standard_pipeline]
    def reject_upload(status_code: int, detail: str):
        case.workflow_status = "validation_failed"
        case.processing_status = "failed"
        audit(db, user.id, "image_validation_failed", case.id)
        notify_case(db, case, user.id, "validation_failed", f"Image validation failed for {case.case_code}",
                    {"technician", "doctor", "clinician", "admin"})
        db.commit()
        raise HTTPException(status_code=status_code, detail=detail)

    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        reject_upload(415, "Unsupported file type. Upload a supported image, DICOM, or scanned PDF")
    if filename.lower().endswith(".pdf") and page_index is None:
        page_index = 0
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        reject_upload(413, "File must be between 1 byte and 50 MB")
    source_sha256 = hashlib.sha256(raw).hexdigest()
    roi_box = None
    if roi:
        try:
            x, y, width, height = [int(value.strip()) for value in roi.split(",")]
            roi_box = (x, y, x + width, y + height)
        except (ValueError, TypeError):
            reject_upload(422, "ROI must be x,y,width,height in pixels")
    signature = {"profile": profile, "standard_pipeline": standard_pipeline,
                 "denoise": denoise, "enhance": enhance, "roi_box": list(roi_box) if roi_box else None,
                 "frame_index": frame_index, "page_index": page_index}
    for existing in db.scalars(select(Image).where(Image.case_id == case.id, Image.source_sha256 == source_sha256)):
        previous = json.loads(existing.preprocessing_config_json or "{}")
        prior_signature = previous.get("request_signature", {
            "profile": previous.get("profile", "standard"), "standard_pipeline": previous.get("standard_pipeline", "baseline"),
            "denoise": previous.get("options", {}).get("denoise", False),
            "enhance": previous.get("options", {}).get("contrast_enhancement", False),
            "roi_box": previous.get("roi_box_xyxy"), "frame_index": previous.get("frame_index"),
            "page_index": previous.get("page_index"),
        })
        if signature == prior_signature:
            raise HTTPException(409, "This exact file with the same pipeline and selection is already attached to this case")
    processing_steps = ["file_type_and_size_validation", "exact_duplicate_check"]
    try:
        preview, width, height, media_type, spacing = prepare_image(
            raw, filename, roi_box, frame_index, page_index, denoise=denoise, enhance=enhance,
            processing_steps=processing_steps)
    except InvalidImage as exc:
        reject_upload(422, str(exc))
    image_id = str(uuid4())
    ext = Path(filename).suffix.lower()
    source = STORAGE / "uploads" / f"{image_id}{ext}"
    processed = STORAGE / "preprocessed" / f"{image_id}.png"
    source.write_bytes(raw)
    processed.write_bytes(preview)
    processed_sha256 = hashlib.sha256(preview).hexdigest()
    steps = processing_steps
    if frame_index is not None:
        steps.insert(2, "dicom_frame_selection")
    if page_index is not None:
        steps.insert(2, "pdf_page_selection")
    warnings = []
    if denoise or enhance:
        warnings.append("enhanced_preprocessing_not_validated_for_current_model_compare_with_baseline")
    if spacing is None:
        warnings.append("physical_pixel_spacing_unavailable")
    config = {
        "modality": upload_modality,
        "modality_source": "operator_declared",
        "intended_tasks": [task for task in case_tasks(case) if task != "volume_preparation"],
        "pipeline_version": "2.2",
        "standard_pipeline": standard_pipeline if profile == "standard" else None,
        "request_signature": signature,
        "resize_geometry": content_geometry(width, height, roi_box),
        "profile": profile,
        "options": {"denoise": denoise, "contrast_enhancement": enhance},
        "source_format": media_type,
        "source_dimensions": {"width": width, "height": height},
        "target_size": TARGET_SIZE,
        "roi_box_xyxy": roi_box,
        "frame_index": frame_index,
        "page_index": page_index,
        "source_sha256": source_sha256,
        "processed_sha256": processed_sha256,
        "steps": steps,
        "warnings": warnings,
        "created_at": now().isoformat(),
    }
    image = Image(
        id=image_id, case_id=case.id, original_name=filename, original_path=str(source),
        preview_path=str(processed), content_type=media_type, width=width, height=height,
        spacing_mm=spacing, processed_spacing_mm=processed_spacing_mm(spacing, width, height, roi_box),
        roi_box=roi, frame_index=frame_index, page_index=page_index,
        preprocessing_json=json.dumps(steps),
        preprocessing_config_json=json.dumps(config),
        source_sha256=source_sha256, processed_sha256=processed_sha256,
    )
    case.status = "uploaded"
    case.workflow_status = "ready_for_analysis"
    case.processing_status = "completed"
    case.report_status = "draft"
    db.add(image)
    db.add(AuditEvent(user_id=user.id, action="image_uploaded", case_id=case.id))
    notify_case(db, case, user.id, "image_uploaded", f"New image uploaded to {case.case_code}")
    db.commit()
    return {"id": image.id, "case_id": case.id, "width": width, "height": height,
            "spacing_mm": spacing, "processed_spacing_mm": image.processed_spacing_mm,
            "roi_box": roi, "frame_index": frame_index, "page_index": page_index,
            "processing_record": config,
            "preview_url": f"/api/images/{image.id}/preview"}


@app.post("/api/cases/{case_id}/volumes/prepare")
def prepare_case_volume(
    case_id: str, file: UploadFile = File(...), mask: UploadFile | None = File(default=None),
    reference: UploadFile | None = File(default=None), spacing: str | None = Form(default=None),
    roi: str | None = Form(default=None), slice_axis: int = Form(default=2),
    slice_index: int | None = Form(default=None), denoise: bool = Form(default=False),
    enhance: bool = Form(default=False),
    modality: Literal["CT", "CTA", "MRA"] | None = Form(default=None),
    user: User = Depends(require_roles("researcher", "admin")), db: Session = Depends(get_db),
):
    """Separate 3D research export; never dispatch a volume to 2D inference."""
    from io import BytesIO
    from tempfile import TemporaryDirectory
    from zipfile import ZipFile, ZIP_DEFLATED
    from fastapi.responses import Response
    import numpy as np
    from nibabel.filebasedimages import ImageFileError
    from .volume_preprocessing import read_volume, prepare_volume
    import SimpleITK as sitk

    case = accessible_case(case_id, user, db, required_action="upload")
    if not allowed_action(user, "case:upload", db):
        raise HTTPException(403, "Volume preparation needs a separate operational grant")
    volume_modalities = [value for value in case_modalities(case) if value in {"CT", "CTA", "MRA"}]
    if modality is None and len(case_modalities(case)) > 1:
        raise HTTPException(422, "Specify the volume modality in a multi-modality case")
    volume_modality = modality or case.modality
    if volume_modality not in volume_modalities or "volume_preparation" not in case_tasks(case):
        raise HTTPException(422, "Select an enabled CT/CTA/MRA volume preparation route")
    with TemporaryDirectory(prefix="corovision-volume-") as temporary:
        folder = Path(temporary)
        sources = {}
        for key, upload in (("source", file), ("mask", mask), ("reference", reference)):
            if upload is None:
                continue
            if not (upload.filename or "").lower().endswith((".nii", ".nii.gz")):
                raise HTTPException(415, "Volume upload requires .nii or .nii.gz")
            raw = upload.file.read(MAX_UPLOAD_BYTES+1)
            if not raw or len(raw) > MAX_UPLOAD_BYTES:
                raise HTTPException(413, "Each NIfTI file must be between 1 byte and 50 MB; use offline preparation for larger data")
            path = folder / (key + (".nii.gz" if upload.filename.lower().endswith(".gz") else ".nii"))
            path.write_bytes(raw)
            sources[key] = path
        try:
            target_spacing = [float(v) for v in spacing.split(",")] if spacing else None
            roi_values = [int(v) for v in roi.split(",")] if roi else None
            image, labels, tensor, selected_slice, record, transform = prepare_volume(
                read_volume(sources["source"]), spacing=target_spacing, roi=roi_values,
                mask=read_volume(sources["mask"]) if mask else None,
                reference=read_volume(sources["reference"]) if reference else None,
                denoise=denoise, enhance=enhance, slice_axis=slice_axis, slice_index=slice_index)
        except (ValueError, RuntimeError, OverflowError, OSError, ImageFileError) as exc:
            raise HTTPException(422, f"Volume preparation rejected: {exc}") from exc
        sitk.WriteImage(image, str(folder / "prepared.nii.gz"))
        if labels is not None:
            sitk.WriteImage(labels, str(folder / "prepared_mask.nii.gz"))
        if transform is not None:
            sitk.WriteTransform(transform, str(folder / "registration.tfm"))
        np.save(folder / "model_input_czyx.npy", tensor, allow_pickle=False)
        np.save(folder / "selected_slice_chw.npy", selected_slice, allow_pickle=False)
        from PIL import Image as PILImage
        PILImage.fromarray(np.uint8(np.clip(selected_slice[0], 0, 1)*255)).save(folder / "slice_preview.png")
        record["source_sha256"] = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in sources.items()}
        record["case_id"] = case.id
        record["modality"] = volume_modality
        record["modality_source"] = "operator_declared"
        record["intended_task"] = "volume_preparation"
        (folder / "processing_record.json").write_text(json.dumps(record, indent=2))
        archive = BytesIO()
        with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
            for path in folder.iterdir():
                bundle.write(path, path.name)
        audit(db, user.id, "research_volume_prepared", case.id)
        db.commit()
        return Response(archive.getvalue(), media_type="application/zip",
                        headers={"Content-Disposition": 'attachment; filename="corovision_volume_prepared.zip"'})


@app.get("/api/images/{image_id}/preview")
def image_preview(image_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    return FileResponse(image.preview_path, media_type="image/png")


@app.get("/api/images/{image_id}/source")
def image_source(image_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    return FileResponse(image.original_path, media_type=image.content_type or "application/octet-stream",
                        headers={"X-Content-Type-Options": "nosniff"})


def analysis_out(run: AnalysisRun) -> dict:
    vessel_path = Path(run.overlay_path).with_suffix(".json")
    try:
        metadata = json.loads(vessel_path.read_text())
        vessel = metadata.get("vessel_analysis", {})
        model_scores = metadata.get("model_scores", {})
    except (OSError, ValueError):
        vessel, model_scores, metadata = {}, {}, {}
    return {"id": run.id, "image_id": run.image_id, "model_version": run.model_version,
            "artery_pixels": run.artery_pixels, "stenosis_pixels": run.stenosis_pixels,
            "overlay_url": f"/api/images/{run.image_id}/analysis/overlay",
            "attention_map_url": f"/api/images/{run.image_id}/analysis/map/attention",
            "stenosis_probability_url": f"/api/images/{run.image_id}/analysis/map/probability",
            "gradcam_url": f"/api/images/{run.image_id}/analysis/map/gradcam",
            "centerline_url": f"/api/images/{run.image_id}/analysis/map/centerline",
            "artery_probability_url": f"/api/images/{run.image_id}/analysis/map/artery_probability",
            "vessel_analysis": vessel,
            "model_scores": model_scores,
            "structured_result": metadata.get("structured_result"),
            "validation": validation_summary() if run.model_version == model_version() else {},
            "created_at": run.created_at,
            "research_only": True,
            "interpretation": "Pixel masks are uncalibrated research outputs; no clinical stenosis grade is inferred."}


def event_out(event: AnalysisEvent) -> dict:
    try:
        evaluation = json.loads(event.validation_json or "{}")
    except ValueError:
        evaluation = {}
    return {"id": event.id, "image_id": event.image_id,
            "model_version": event.model_version, "artery_pixels": event.artery_pixels,
            "stenosis_pixels": event.stenosis_pixels,
            "overlay_url": f"/api/images/{event.image_id}/analyses/{event.id}/overlay",
            "attention_map_url": f"/api/images/{event.image_id}/analyses/{event.id}/map/attention",
            "stenosis_probability_url": f"/api/images/{event.image_id}/analyses/{event.id}/map/probability",
            "gradcam_url": f"/api/images/{event.image_id}/analyses/{event.id}/map/gradcam",
            "centerline_url": f"/api/images/{event.image_id}/analyses/{event.id}/map/centerline",
            "artery_probability_url": f"/api/images/{event.image_id}/analyses/{event.id}/map/artery_probability",
            "validation": evaluation.get("models", evaluation),
            "vessel_analysis": evaluation.get("vessel_analysis", {}),
            "model_scores": evaluation.get("model_scores", {}),
            "structured_result": evaluation.get("structured_result"),
            "created_at": event.created_at, "research_only": True,
            "interpretation": "Pixel masks are uncalibrated research outputs; no clinical stenosis grade is inferred."}


@app.get("/api/analysis/status")
def analysis_status(user: User = Depends(current_user)):
    if user.role == "viewer":
        return {"models_ready": False, "research_only": True}
    if user.role not in ROLE_MODEL_MANAGERS:
        return {"models_ready": models_ready(), "model_version": model_version(), "research_only": True}
    comparison_path = BASE_DIR / "models" / "segmentation" / "comparison_report.json"
    selection_path = BASE_DIR / "models" / "segmentation" / "promoted_model.json"
    test_report_path = BASE_DIR / "models" / "segmentation" / "test_report.json"
    comparison, selection, test_report = {}, {}, {}
    try:
        comparison = json.loads(comparison_path.read_text())
    except (OSError, ValueError):
        pass
    try:
        selection = json.loads(selection_path.read_text())
    except (OSError, ValueError):
        pass
    try:
        test_report = json.loads(test_report_path.read_text())
    except (OSError, ValueError):
        pass
    instance_root = BASE_DIR / "models" / "arcade_instances"
    instance_status = {}
    for key, filename in (("comparison", "comparison_report.json"),
                          ("selection", "promoted_model.json"),
                          ("test_report", "test_report.json")):
        try:
            instance_status[key] = json.loads((instance_root / filename).read_text())
        except (OSError, ValueError):
            instance_status[key] = {}
    instance_arch = instance_status.get("selection", {}).get("architecture")
    instance_models_ready = bool(instance_arch in {"maskrcnn_resnet50_fpn", "maskrcnn_resnet50_fpn_v2"} and
                                 all((instance_root / task / instance_arch / "best.pt").is_file()
                                     for task in ("syntax", "stenosis")))
    return {"models_ready": models_ready(), "model_version": model_version(),
            "trained_release": trained_release.status(),
            "validation": validation_summary(), "comparison": comparison,
            "selection": selection, "test_report": test_report,
            "instance_aware": instance_status,
            "instance_models_ready": instance_models_ready,
            "research_only": True}


def _model_registry_data() -> tuple[dict, dict, list[dict]]:
    root = BASE_DIR / "models" / "segmentation"
    selection_path = root / "promoted_model.json"
    report_path = root / "comparison_report.json"
    registry_path = root / "model_registry.json"
    try:
        selection = json.loads(selection_path.read_text())
    except (OSError, ValueError):
        selection = {}
    try:
        comparison = json.loads(report_path.read_text())
    except (OSError, ValueError):
        comparison = {}
    try:
        registry = json.loads(registry_path.read_text())
    except (OSError, ValueError):
        registry = {"history": []}
    mean_dice = comparison.get("architecture_mean_validation_dice", {})
    registered = []
    for architecture in ("tiny_unet", "attention_unet"):
        checkpoint_paths = [root / task / f"{architecture}.pt" for task in ("syntax", "stenosis")]
        available = all(path.is_file() for path in checkpoint_paths)
        rows = [row for row in comparison.get("experiments", []) if row.get("architecture") == architecture]
        task_reports = []
        for task in ("syntax", "stenosis"):
            try:
                task_reports.append(json.loads((root / task / f"{architecture}_report.json").read_text()))
            except (OSError, ValueError):
                task_reports.append({})
        run_ids = {row.get("training_run_id") for row in task_reports if row.get("training_run_id")}
        version = (task_reports[0].get("model_version") if len(run_ids) == 1
                   and task_reports[0].get("model_version") else f"arcade-{architecture}-v1")
        registered.append({
            "architecture": architecture,
            "display_name": "Tiny U-Net" if architecture == "tiny_unet" else "Attention U-Net",
            "version": version,
            "input_size": next((int(report.get("input_size", 128)) for report in task_reports
                                 if report.get("input_size")), 128),
            "training_run_id": next(iter(run_ids)) if len(run_ids) == 1 else None,
            "available": available,
            "active": selection.get("architecture") == architecture,
            "mean_validation_dice": mean_dice.get(architecture),
            "mean_validation_image_f1": comparison.get("architecture_mean_validation_image_f1", {}).get(architecture),
            "mean_validation_composite_score": comparison.get("architecture_mean_validation_composite_score", {}).get(architecture),
            "tasks": [{"task": row.get("task"), "train_images": row.get("train_images"),
                       "validation_images": row.get("validation_images"),
                       "validation_dice": row.get("best_validation", {}).get("dice"),
                       "epochs": row.get("epochs_completed", row.get("epochs")), "seed": row.get("seed"),
                       "dataset": row.get("dataset"), "threshold": row.get("threshold"),
                       "training_run_id": row.get("training_run_id")}
                      for row in rows],
            "checkpoint_sha256": {task: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for task, path in zip(("syntax", "stenosis"), checkpoint_paths) if path.is_file()},
        })
    return selection, registry, registered


@app.get("/api/analysis/models")
def registered_models(user: User = Depends(require_roles(*ROLE_MODEL_MANAGERS))):
    if trained_release.configured():
        release = trained_release.status()
        return {"can_activate": False, "model_version": model_version(), "active_architecture": "preserved_mask_models",
                "models": [{"architecture": "preserved_mask_models", "display_name": "Verified preserved training models",
                            "version": model_version(), "input_size": 512, "available": release['ready'], "active": True,
                            "mean_validation_dice": None, "checkpoint_sha256": {x['task']: x['sha256'] for x in release['models']},
                            "tasks": release['models']}], "history": [], "research_only": True}
    selection, registry, models = _model_registry_data()
    history = registry.get("history", [])
    if not history and selection.get("architecture"):
        history = [{"architecture": selection["architecture"], "version": selection.get("version"),
                    "activated_at": None, "activated_by": "initial project selection", "event": "initial_selection"}]
    return {"models": models, "can_activate": user.role == "admin", "active_architecture": selection.get("architecture"),
            "model_version": selection.get("version", model_version()), "history": history,
            "research_only": True}


@app.post("/api/analysis/models/activate")
def activate_model(data: ModelActivationIn, user: User = Depends(require_roles("admin")),
                   db: Session = Depends(get_db)):
    if trained_release.configured():
        raise HTTPException(status_code=409, detail="Preserved release configured; choose the documented legacy provider before activating older models")
    selection, registry, models = _model_registry_data()
    candidate = next((item for item in models if item["architecture"] == data.architecture), None)
    if not candidate or not candidate["available"]:
        raise HTTPException(status_code=409, detail="Both task checkpoints must be present before activation")
    previous = selection.get("architecture")
    if previous == data.architecture:
        return {"detail": "This model is already active", "model_version": selection.get("version"),
                "architecture": data.architecture}
    root = BASE_DIR / "models" / "segmentation"
    comparison = json.loads((root / "comparison_report.json").read_text())
    thresholds = {}
    for row in comparison.get("experiments", []):
        if row.get("architecture") == data.architecture and row.get("task") in {"syntax", "stenosis"}:
            thresholds[row["task"]] = float(row.get("threshold", 0.5))
    activated = {"architecture": data.architecture, "version": candidate["version"],
                 "training_run_id": candidate.get("training_run_id"),
                 "input_size": candidate.get("input_size", 128),
                 "selection_metric": comparison.get("selection_metric", "validation pixel Dice"),
                 "validation_composite_score_by_architecture": comparison.get("architecture_mean_validation_composite_score", {}),
                 "validation_image_f1_by_architecture": comparison.get("architecture_mean_validation_image_f1", {}),
                 "validation_dice_by_architecture":
                 comparison.get("architecture_mean_validation_dice", {}), "thresholds": thresholds,
                 "test_split_used": False, "clinical_validation": False}
    history = registry.get("history", [])
    from datetime import datetime
    history.insert(0, {"event": "model_activated", "architecture": data.architecture,
                       "version": candidate["version"], "previous_architecture": previous,
                       "activated_by": user.id, "activated_at": datetime.now(timezone.utc).isoformat()})
    registry_path = root / "model_registry.json"
    selection_path = root / "promoted_model.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    temp_selection = selection_path.with_suffix(".json.tmp")
    temp_registry = registry_path.with_suffix(".json.tmp")
    temp_selection.write_text(json.dumps(activated, indent=2) + "\n")
    temp_registry.write_text(json.dumps({"history": history[:100]}, indent=2) + "\n")
    temp_selection.replace(selection_path)
    temp_registry.replace(registry_path)
    audit(db, user.id, f"model_activated:{data.architecture}")
    db.commit()
    return {"detail": "Model activated", "model_version": activated["version"],
            "architecture": data.architecture}


def analysis_input(image_id, user, db):
    if not user or user.role not in ROLE_ANALYSIS_RUNNERS or user.status != 'active':
        raise HTTPException(403, "Analysis permission unavailable")
    if not allowed_action(user, "analysis:run", db):
        raise HTTPException(403, "AI analysis needs a separate operational grant")
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="analyze")
    image_modality = json.loads(image.preprocessing_config_json or "{}").get("modality", db.get(Case, image.case_id).modality)
    if image_modality != "XCA":
        raise HTTPException(422, "Only XCA image assets can reach the current 2D models")
    if not supports_current_inference(db.get(Case, image.case_id)):
        raise HTTPException(status_code=422, detail="The current research models require X-ray coronary angiography")
    if not models_ready():
        raise HTTPException(status_code=503, detail="Verified research model artifacts or inference dependencies are unavailable")
    return image


def perform_analysis(image_id, user, db, job=None):
    image = analysis_input(image_id, user, db)
    if job and (model_version() != job.model_version or (image.processed_sha256 or '') != job.input_sha256):
        raise HTTPException(409, "Model version or input changed after submission")
    if image.processed_sha256 and hashlib.sha256(Path(image.preview_path).read_bytes()).hexdigest() != image.processed_sha256:
        raise HTTPException(409, "Saved input integrity check failed")
    try:
        spacing = None
        if image.processed_spacing_mm:
            try:
                spacing = tuple(float(value) for value in image.processed_spacing_mm.split(","))
                if len(spacing) != 2 or any(value <= 0 for value in spacing):
                    spacing = None
            except (TypeError, ValueError):
                spacing = None
        (overlay, artery_pixels, stenosis_pixels, vessel_analysis,
         attention_map, artery_probability_map, probability_map, gradcam_map,
         model_scores, centerline_map) = analyze(Path(image.preview_path), spacing)
    except (OSError, RuntimeError, ValueError) as exc:
        case = db.get(Case, image.case_id)
        case.processing_status = "failed"
        audit(db, user.id, "analysis_failed", case.id)
        notify_case(db, case, user.id, "analysis_failed",
                    f"AI analysis failed for {case.case_code}; check model availability and retry")
        db.commit()
        raise HTTPException(status_code=503, detail="Analysis unavailable; check model files") from exc
    event_id = str(uuid4())
    overlay_path = STORAGE / "analysis" / f"{event_id}.png"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.write_bytes(overlay)
    for map_name, map_content in (("attention", attention_map), ("artery_probability", artery_probability_map),
                                  ("probability", probability_map),
                                  ("gradcam", gradcam_map), ("centerline", centerline_map)):
        if map_content is not None:
            overlay_path.with_name(f"{overlay_path.stem}.{map_name}.png").write_bytes(map_content)
    artifacts = {"overlay": f"/api/images/{image.id}/analyses/{event_id}/overlay"}
    for kind, content in model_scores.pop('_artifacts', {}).items():
        if kind not in {"artery_mask", "stenosis_mask", "raw_scores"}:
            raise ValueError("Unsupported inference artifact")
        extension = 'npz' if kind == 'raw_scores' else 'png'
        overlay_path.with_name(f'{event_id}.{kind}.{extension}').write_bytes(content)
        artifacts[kind] = f'/api/images/{image.id}/analyses/{event_id}/artifacts/{kind}'
    structured = build_result(event_id=event_id, job_id=job.id if job else None, image=image,
                              case=db.get(Case, image.case_id), version=model_version(), scores=model_scores,
                              vessel=vessel_analysis, artery_pixels=artery_pixels, stenosis_pixels=stenosis_pixels,
                              evidence=validation_summary(), artifacts=artifacts, timestamp=now().isoformat())
    overlay_path.with_suffix(".json").write_text(json.dumps({"vessel_analysis": vessel_analysis,
                                                               "model_scores": model_scores,
                                                               "structured_result": structured}, allow_nan=False))
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.image_id == image.id))
    if run is None:
        run = AnalysisRun(image_id=image.id, model_version=model_version(),
                          artery_pixels=artery_pixels, stenosis_pixels=stenosis_pixels,
                          overlay_path=str(overlay_path))
        db.add(run)
    else:
        run.model_version = model_version()
        run.artery_pixels = artery_pixels
        run.stenosis_pixels = stenosis_pixels
        run.overlay_path = str(overlay_path)
        run.created_at = now()
    event = AnalysisEvent(id=event_id, image_id=image.id,
                          model_version=model_version(), artery_pixels=artery_pixels,
                          stenosis_pixels=stenosis_pixels, overlay_path=str(overlay_path),
                          validation_json=json.dumps({"models": validation_summary(),
                                                      "vessel_analysis": vessel_analysis,
                                                      "model_scores": model_scores,
                                                      "structured_result": structured}, allow_nan=False))
    db.add(event)
    case = db.get(Case, image.case_id)
    case.status = "analyzed"
    case.workflow_status = "pending_review"
    case.processing_status = "completed"
    case.report_status = "draft"
    audit(db, user.id, "image_analyzed", image.case_id)
    notify_case(db, case, user.id, "analysis_ready", f"AI results for {case.case_code} await clinical review",
                ROLE_CLINICAL_REVIEWERS)
    if stenosis_pixels > 0:
        notify_case(db, case, user.id, "model_stenosis_flag",
                    f"Model flagged a possible stenosis region in {case.case_code}; clinician review is required")
    if vessel_analysis.get("stenosis_mask_components", 0) > 1:
        notify_case(db, case, user.id, "model_multiple_regions",
                    f"Model produced multiple disconnected stenosis-mask regions in {case.case_code}; review the image and overlay")
    flags = vessel_analysis.get("quality_flags", [])
    uncertainty_codes = {"uncertain_pixels", "low_foreground_score", "threshold_sensitive_centerline"}
    if any(flag.get("severity") in {"warning", "review"} and flag.get("code") not in uncertainty_codes for flag in flags):
        notify_case(db, case, user.id, "analysis_quality_review",
                    f"Image or segmentation quality needs review for {case.case_code}")
    if any(flag.get("code") in {"uncertain_pixels", "low_foreground_score", "threshold_sensitive_centerline"}
           for flag in flags):
        notify_case(db, case, user.id, "model_uncertainty_review",
                    f"Model output is unstable or has a low uncalibrated score for {case.case_code}; inspect the probability map")
    if job:
        job.status, job.progress, job.result_event_id = 'completed', 100, event_id
        job.active_image_id = None
        job.completed_at = now()
        audit(db, user.id, 'analysis_job_completed', image.case_id)
    db.commit()
    db.refresh(run)
    return event_out(event) if job else analysis_out(run)


def execute_analysis_job(db, job):
    user = db.get(User, job.requested_by)
    perform_analysis(job.image_id, user, db, job)


class AnalysisJobIn(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=80, pattern=r'^[A-Za-z0-9_-]+$')


def job_out(job):
    return dict(id=job.id, image_id=job.image_id, case_id=job.case_id, status=job.status,
                model_version=job.model_version, progress=job.progress, created_at=job.created_at,
                started_at=job.started_at, completed_at=job.completed_at, result_event_id=job.result_event_id,
                error_code=job.error_code, error_detail=job.error_detail,
                status_url=f'/api/analysis/jobs/{job.id}',
                result_url=f'/api/analysis/jobs/{job.id}/result' if job.status == 'completed' else None)


@app.post('/api/images/{image_id}/analysis/jobs', status_code=202)
def create_analysis_job(image_id: str, data: AnalysisJobIn,
                        user: User = Depends(require_roles(*ROLE_ANALYSIS_RUNNERS)), db: Session = Depends(get_db)):
    image = analysis_input(image_id, user, db)
    existing = db.scalar(select(AnalysisJob).where(AnalysisJob.image_id == image.id,
                         AnalysisJob.requested_by == user.id, AnalysisJob.idempotency_key == data.idempotency_key))
    if existing:
        return job_out(existing)
    # Sequential admission per image; a new key cannot duplicate an active job.
    active = db.scalar(select(AnalysisJob).where(AnalysisJob.image_id == image.id,
                                               AnalysisJob.status.in_(['pending', 'processing'])))
    if active:
        return job_out(active)
    if db.scalar(select(func.count()).select_from(AnalysisJob).where(AnalysisJob.status.in_(['pending', 'processing']))) >= 32:
        raise HTTPException(429, 'Inference queue is full; retry later with the same key')
    job = AnalysisJob(image_id=image.id, case_id=image.case_id, requested_by=user.id,
                      idempotency_key=data.idempotency_key, model_version=model_version(),
                      input_sha256=image.processed_sha256 or '', active_image_id=image.id)
    db.add(job)
    db.get(Case, image.case_id).processing_status = 'pending'
    audit(db, user.id, 'analysis_job_requested', image.case_id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(AnalysisJob).where(AnalysisJob.image_id == image.id,
                             AnalysisJob.requested_by == user.id, AnalysisJob.idempotency_key == data.idempotency_key))
        if not existing:
            existing = db.scalar(select(AnalysisJob).where(AnalysisJob.active_image_id == image.id))
        if not existing:
            raise HTTPException(409, 'Conflicting analysis request; retry with the same key')
        return job_out(existing)
    return job_out(job)


@app.get('/api/analysis/jobs/{job_id}')
def get_analysis_job(job_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    job = db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(404, 'Job not found')
    accessible_case(job.case_id, user, db, required_action='read')
    return job_out(job)


@app.get('/api/analysis/jobs/{job_id}/result')
def get_analysis_job_result(job_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    job = db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(404, 'Job not found')
    accessible_case(job.case_id, user, db, required_action='read')
    if job.status != 'completed':
        raise HTTPException(409, 'Job has no completed result')
    event = db.get(AnalysisEvent, job.result_event_id)
    if not event or event.image_id != job.image_id:
        raise HTTPException(404, 'Saved result unavailable')
    return event_out(event)


@app.get('/api/images/{image_id}/analysis/jobs')
def image_analysis_jobs(image_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(404, 'Image not found')
    accessible_case(image.case_id, user, db, required_action='read')
    return [job_out(row) for row in db.scalars(select(AnalysisJob).where(AnalysisJob.image_id == image_id)
                                             .order_by(AnalysisJob.created_at.desc()).limit(50))]


@app.post("/api/images/{image_id}/analyze")
def analyze_image(image_id: str, user: User = Depends(require_roles(*ROLE_ANALYSIS_RUNNERS)), db: Session = Depends(get_db)):
    # Compatibility route; new frontend uses the persistent job API.
    analysis_input(image_id, user, db)
    if db.scalar(select(AnalysisJob).where(AnalysisJob.active_image_id == image_id)):
        raise HTTPException(409, 'An analysis job is already active for this image')
    return perform_analysis(image_id, user, db)


@app.get("/api/images/{image_id}/analyses")
def analysis_history(image_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    events = db.scalars(select(AnalysisEvent).where(AnalysisEvent.image_id == image_id)
                        .order_by(AnalysisEvent.created_at.desc())).all()
    return [event_out(event) for event in events]


@app.get("/api/cases/{case_id}/analyses")
def case_analysis_history(case_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    accessible_case(case_id, user, db, required_action="read")
    events = db.scalars(select(AnalysisEvent).join(Image, AnalysisEvent.image_id == Image.id)
                        .where(Image.case_id == case_id).order_by(AnalysisEvent.created_at.desc())).all()
    return [event_out(event) for event in events]


@app.get("/api/images/{image_id}/analyses/{event_id}/overlay")
def history_overlay(image_id: str, event_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    event = db.get(AnalysisEvent, event_id)
    if not event or event.image_id != image_id or not Path(event.overlay_path).is_file():
        raise HTTPException(status_code=404, detail="Analysis overlay not found")
    return FileResponse(event.overlay_path, media_type="image/png")


@app.get('/api/images/{image_id}/analyses/{event_id}/artifacts/{kind}')
def result_artifact(image_id: str, event_id: str, kind: str,
                    user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(404, 'Image not found')
    accessible_case(image.case_id, user, db, required_action='read')
    event = db.get(AnalysisEvent, event_id)
    if not event or event.image_id != image_id or kind not in {'artery_mask', 'stenosis_mask', 'raw_scores'}:
        raise HTTPException(404, 'Artifact not found')
    extension = 'npz' if kind == 'raw_scores' else 'png'
    path = Path(event.overlay_path).with_name(f'{event.id}.{kind}.{extension}')
    if not path.is_file():
        raise HTTPException(404, 'Artifact unavailable for this model')
    return FileResponse(path, media_type='application/octet-stream' if kind == 'raw_scores' else 'image/png',
                        headers={'X-Content-Type-Options': 'nosniff'})


def _explanation_file(base_path: str, kind: str) -> Path:
    if kind not in {"attention", "artery_probability", "probability", "gradcam", "centerline"}:
        raise HTTPException(status_code=404, detail="Explanation map not found")
    return Path(base_path).with_name(f"{Path(base_path).stem}.{kind}.png")


@app.get("/api/images/{image_id}/analyses/{event_id}/map/{kind}")
def history_explanation_map(image_id: str, event_id: str, kind: str,
                            user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    event = db.get(AnalysisEvent, event_id)
    if not event or event.image_id != image_id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    path = _explanation_file(event.overlay_path, kind)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Explanation map unavailable for this model")
    return FileResponse(path, media_type="image/png")


@app.get("/api/images/{image_id}/analysis/compare")
def compare_analyses(image_id: str, left_id: str, right_id: str,
                     user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    left, right = db.get(AnalysisEvent, left_id), db.get(AnalysisEvent, right_id)
    if not left or not right or left.image_id != image_id or right.image_id != image_id:
        raise HTTPException(status_code=404, detail="Analysis run not found for this image")
    return {"left": event_out(left), "right": event_out(right),
            "difference": {"artery_pixels": right.artery_pixels - left.artery_pixels,
                           "stenosis_pixels": right.stenosis_pixels - left.stenosis_pixels},
            "interpretation": "Pixel count differences are not a measure of clinical progression."}


@app.get("/api/images/{image_id}/analysis")
def get_analysis(image_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.image_id == image_id))
    if not run:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_out(run)


@app.get("/api/images/{image_id}/analysis/overlay")
def analysis_overlay(image_id: str, user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.image_id == image_id))
    if not run or not Path(run.overlay_path).is_file():
        raise HTTPException(status_code=404, detail="Analysis overlay not found")
    return FileResponse(run.overlay_path, media_type="image/png")


@app.get("/api/images/{image_id}/analysis/map/{kind}")
def current_explanation_map(image_id: str, kind: str,
                            user: User = Depends(require_case_role), db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    accessible_case(image.case_id, user, db, required_action="read")
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.image_id == image_id))
    if not run:
        raise HTTPException(status_code=404, detail="Analysis not found")
    path = _explanation_file(run.overlay_path, kind)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Explanation map unavailable for this model")
    return FileResponse(path, media_type="image/png")


@app.post("/api/admin/users/{user_id}/role")
def set_role(
    user_id: str,
    data: RoleIn,
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if data.role not in ALL_ROLES:
        raise HTTPException(status_code=422, detail="Invalid role")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == actor.id and data.role != "admin":
        raise HTTPException(status_code=409, detail="Administrator cannot remove their own role")
    if target.role != data.role:
        for grant in db.scalars(select(ActionGrant).where(ActionGrant.user_id == target.id)):
            grant.enabled = False
    target.role = data.role
    if data.role not in ROLE_CLINICAL_REVIEWERS:
        target.can_approve_reports = False
    audit(db, actor.id, f"role:{data.role}:{target.id}")
    db.commit()
    return user_out(target, db)


@app.post("/api/admin/users/{user_id}/status")
def set_user_status(
    user_id: str,
    data: StatusIn,
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == actor.id and data.status != "active":
        raise HTTPException(status_code=409, detail="Administrator cannot deactivate or suspend their own account")
    target.status = data.status
    if data.status in {"suspended", "deactivated"}:
        for s in db.scalars(select(AuthSession).where(AuthSession.user_id == target.id, AuthSession.revoked_at.is_(None))):
            s.revoked_at = now()
    audit(db, actor.id, f"status:{data.status}:{target.id}")
    db.commit()
    return user_out(target, db)


@app.post("/api/admin/users/{user_id}/report-approval")
def set_report_approval_permission(
    user_id: str, data: ReportApprovalPermissionIn,
    actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if data.enabled and target.role not in ROLE_CLINICAL_REVIEWERS:
        raise HTTPException(status_code=422, detail="Only a doctor, clinician or administrator can approve reports")
    target.can_approve_reports = data.enabled
    audit(db, actor.id, f"report_approval_permission:{data.enabled}:{target.id}")
    db.commit()
    return user_out(target, db)


class RoleRequestIn(BaseModel):
    requested_role: Literal["researcher", "clinician", "ml_engineer"]
    reason: str = Field(min_length=20, max_length=2000)


class RoleRequestDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=20, max_length=2000)


def role_request_out(item: RoleAccessRequest, db: Session) -> dict:
    person = db.get(User, item.user_id)
    return {"id": item.id, "user_id": item.user_id, "email": person.email if person else "",
            "requested_role": item.requested_role, "reason": item.reason, "status": item.status,
            "created_at": item.created_at, "decision_notes": item.decision_notes}


@app.post("/api/auth/access-requests", status_code=201)
def request_role(data: RoleRequestIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if len(data.reason.strip()) < 20:
        raise HTTPException(422, "Explain the research authorization or professional eligibility")
    if db.scalar(select(RoleAccessRequest).where(RoleAccessRequest.user_id == user.id,
                                               RoleAccessRequest.status == "pending")):
        raise HTTPException(409, "An access request is already pending")
    item = RoleAccessRequest(user_id=user.id, requested_role=data.requested_role, reason=data.reason.strip())
    db.add(item)
    audit(db, user.id, f"role_access_requested:{data.requested_role}")
    db.commit()
    return role_request_out(item, db)


@app.get("/api/auth/access-requests")
def own_role_requests(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [role_request_out(item, db) for item in db.scalars(select(RoleAccessRequest)
            .where(RoleAccessRequest.user_id == user.id).order_by(RoleAccessRequest.created_at.desc()))]


@app.get("/api/admin/access-requests")
def admin_role_requests(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return [role_request_out(item, db) for item in db.scalars(select(RoleAccessRequest)
            .order_by(RoleAccessRequest.created_at.desc()))]


@app.post("/api/admin/access-requests/{request_id}/decision")
def decide_role_request(request_id: str, data: RoleRequestDecision,
                        actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.get(RoleAccessRequest, request_id)
    if not item:
        raise HTTPException(404, "Access request not found")
    if item.user_id == actor.id:
        raise HTTPException(403, "You cannot decide your own access request")
    if item.status != "pending":
        raise HTTPException(409, "This request was already decided")
    if len(data.notes.strip()) < 20:
        raise HTTPException(422, "Record the eligibility verification or rejection reason")
    target = db.get(User, item.user_id)
    if not target or target.status != "active":
        raise HTTPException(409, "The target account must be active")
    if data.decision == "approved":
        if target.role == "admin":
            raise HTTPException(409, "Administrator roles must use the existing governance workflow")
        for grant in db.scalars(select(ActionGrant).where(ActionGrant.user_id == target.id)):
            grant.enabled = False
        target.role = item.requested_role
        target.can_approve_reports = False
    item.status = data.decision
    item.decided_by = actor.id
    item.decision_notes = data.notes.strip()
    audit(db, actor.id, f"role_request_{data.decision}:{target.id}:{item.requested_role}")
    db.commit()
    return role_request_out(item, db)


class OperationalGrantIn(BaseModel):
    permission: Literal["case:create", "case:upload", "analysis:run", "analysis:export"]
    enabled: bool
    reason: str = Field(min_length=20, max_length=1000)


@app.post("/api/admin/users/{user_id}/operational-grant")
def set_operational_grant(user_id: str, data: OperationalGrantIn,
                          actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if actor.id == user_id:
        raise HTTPException(403, "A different administrator must authorize your operational access")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    if data.permission not in CONDITIONAL_ACTIONS.get(target.role, set()):
        raise HTTPException(403, "This grant is outside the target role's permitted actions")
    if len(data.reason.strip()) < 20:
        raise HTTPException(422, "Record the operational authorization reason")
    grant = db.scalar(select(ActionGrant).where(ActionGrant.user_id == target.id,
                                               ActionGrant.permission == data.permission))
    if not grant:
        grant = ActionGrant(user_id=target.id, permission=data.permission, granted_by=actor.id, reason=data.reason.strip())
        db.add(grant)
    grant.enabled = data.enabled
    grant.granted_by = actor.id
    grant.reason = data.reason.strip()
    audit(db, actor.id, f"operational_grant:{target.id}:{data.permission}:{data.enabled}")
    db.commit()
    return user_out(target, db)


@app.get("/api/admin/users")
def list_users(actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return [user_out(item, db) for item in db.scalars(select(User).order_by(User.created_at.desc())).all()]


@app.get("/api/admin/audit")
def all_audit(actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200)).all()
    return [
        {"id": event.id, "user_id": event.user_id, "action": event.action,
         "case_id": event.case_id, "created_at": event.created_at}
        for event in events
    ]


frontend_dist = BASE_DIR / "frontend" / "dist"
if not frontend_dist.is_dir():
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if frontend_dist.is_dir():
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    for static_name in ["favicon.ico", "favicon-48.png", "corovision-heart-favicon-20261014.png", "apple-touch-icon.png", "auth-7.avif", "corovision-heart-mark.png", "corovision-heart.png"]:
        file_path = frontend_dist / static_name
        if file_path.is_file():
            def make_static_endpoint(fp: Path):
                return lambda: FileResponse(fp)
            app.get(f"/{static_name}")(make_static_endpoint(file_path))

    @app.get("/")
    def serve_frontend_index():
        index_file = frontend_dist / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        return {"status": "ok", "app": "CoroVision AI"}


