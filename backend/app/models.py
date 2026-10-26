from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def uid() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class ActionGrant(Base):
    __tablename__ = "action_grants"
    __table_args__ = (UniqueConstraint("user_id", "permission"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    permission: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    granted_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)


class RoleAccessRequest(Base):
    __tablename__ = "role_access_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    requested_role: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    decided_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class VolumeAnalysis(Base):
    __tablename__ = 'volume_analyses'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id'), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(20), default='queued')
    source_sha256: Mapped[str] = mapped_column(String(64))
    model_key: Mapped[str] = mapped_column(String(64),default='imagecas')
    input_kind: Mapped[str] = mapped_column(String(32), default='unspecified')
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TaskInferenceRun(Base):
    __tablename__='task_inference_runs'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    case_id: Mapped[str]=mapped_column(ForeignKey('cases.id'),index=True)
    image_id: Mapped[str]=mapped_column(ForeignKey('images.id'),index=True)
    created_by: Mapped[str]=mapped_column(ForeignKey('users.id'))
    task_id: Mapped[str]=mapped_column(String(64))
    input_sha256: Mapped[str]=mapped_column(String(64))
    status: Mapped[str]=mapped_column(String(20),default='queued')
    result_json: Mapped[str|None]=mapped_column(Text,nullable=True)
    error: Mapped[str|None]=mapped_column(String(300),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="viewer")
    status: Mapped[str] = mapped_column(String(20), default="active")
    can_approve_reports: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    cases: Mapped[list["Case"]] = relationship(back_populates="owner")
    case_accesses: Mapped[list["CaseAccess"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    clinical_reviews: Mapped[list["ClinicalReview"]] = relationship(back_populates="reviewer")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class UserIdentity(Base):
    __tablename__ = "user_identities"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    username: Mapped[str | None] = mapped_column(String(40), unique=True, index=True, nullable=True)
    # Retained for compatibility with local databases created before phone auth was removed.
    # These fields are not used by the active API or UI.
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class SocialAccount(Base):
    __tablename__ = "social_accounts"
    __table_args__ = (UniqueConstraint("provider", "subject"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    subject: Mapped[str] = mapped_column(String(255))


class OneTimeCode(Base):
    __tablename__ = "one_time_codes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(32))
    destination: Mapped[str] = mapped_column(String(255))
    digest: Mapped[str] = mapped_column(String(64))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OAuthTicket(Base):
    __tablename__ = "oauth_tickets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OAuthIntent(Base):
    __tablename__ = "oauth_intents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LoginThrottle(Base):
    __tablename__ = "login_throttles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    case_code: Mapped[str] = mapped_column(String(80), index=True)
    patient_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    age_band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_factors: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scan_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    modality: Mapped[str] = mapped_column(String(32), default="XCA")
    anatomy: Mapped[str] = mapped_column(String(80), default="coronary")
    intended_task: Mapped[str] = mapped_column(String(40), default="artery_and_stenosis")
    modalities_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    intended_tasks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_dataset: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    clinical_metadata_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    workflow_status: Mapped[str] = mapped_column(String(32), default="draft")
    processing_status: Mapped[str] = mapped_column(String(32), default="not_started")
    report_status: Mapped[str] = mapped_column(String(32), default="draft")
    report_version: Mapped[int] = mapped_column(Integer, default=0)
    report_approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    report_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    owner: Mapped[User] = relationship(back_populates="cases")
    images: Mapped[list["Image"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    access_list: Mapped[list["CaseAccess"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    reviews: Mapped[list["ClinicalReview"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    report_revisions: Mapped[list["ReportRevision"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    comments: Mapped[list["CaseComment"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseAccess(Base):
    __tablename__ = "case_access"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    access_level: Mapped[str] = mapped_column(String(20), default="read")  # read, review, edit, admin
    assigned_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    case: Mapped[Case] = relationship(back_populates="access_list")
    user: Mapped[User] = relationship(back_populates="case_accesses")


class ClinicalReview(Base):
    __tablename__ = "clinical_reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    analysis_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    image_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decision: Mapped[str] = mapped_column(String(32))  # approved, needs_followup, rejected, reviewed
    stenosis_severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    case: Mapped[Case] = relationship(back_populates="reviews")
    reviewer: Mapped[User] = relationship(back_populates="clinical_reviews")


class ResearchReport(Base):
    __tablename__ = "research_reports"
    __table_args__ = (UniqueConstraint("case_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id"))
    analysis_event_id: Mapped[str] = mapped_column(ForeignKey("analysis_events.id"))
    version: Mapped[int] = mapped_column(Integer)
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ReportRevision(Base):
    __tablename__ = "report_revisions"
    __table_args__ = (UniqueConstraint("case_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="pending_approval")
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    case: Mapped[Case] = relationship(back_populates="report_revisions")


class CaseComment(Base):
    __tablename__ = "case_comments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(24), default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    case: Mapped[Case] = relationship(back_populates="comments")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    case_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    message: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationDismissal(Base):
    """Recoverable inbox deletion without removing the original notification."""
    __tablename__ = "notification_dismissals"
    notification_id: Mapped[str] = mapped_column(ForeignKey("notifications.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Image(Base):
    __tablename__ = "images"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    original_path: Mapped[str] = mapped_column(Text)
    preview_path: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(80))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    spacing_mm: Mapped[str | None] = mapped_column(String(80), nullable=True)
    processed_spacing_mm: Mapped[str | None] = mapped_column(String(80), nullable=True)
    roi_box: Mapped[str | None] = mapped_column(String(80), nullable=True)
    frame_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preprocessing_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    preprocessing_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    processed_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    case: Mapped[Case] = relationship(back_populates="images")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (UniqueConstraint("requested_by", "image_id", "idempotency_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(80))
    input_sha256: Mapped[str] = mapped_column(String(64))
    active_image_id: Mapped[str | None] = mapped_column(String(36), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    result_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(48), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id"), unique=True, index=True)
    model_version: Mapped[str] = mapped_column(String(80))
    artery_pixels: Mapped[int] = mapped_column(Integer)
    stenosis_pixels: Mapped[int] = mapped_column(Integer)
    overlay_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AnalysisEvent(Base):
    __tablename__ = "analysis_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id"), index=True)
    model_version: Mapped[str] = mapped_column(String(80))
    artery_pixels: Mapped[int] = mapped_column(Integer)
    stenosis_pixels: Mapped[int] = mapped_column(Integer)
    overlay_path: Mapped[str] = mapped_column(Text)
    validation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(80))
    case_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EvaluationExperiment(Base):
    __tablename__ = "evaluation_experiments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="experimental")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EvaluationDecision(Base):
    __tablename__ = "evaluation_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("evaluation_experiments.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EvaluationPolicy(Base):
    __tablename__ = "evaluation_policies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EvaluationSampleReview(Base):
    __tablename__ = "evaluation_sample_reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("evaluation_experiments.id"), index=True)
    sample_id: Mapped[str] = mapped_column(String(100))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
