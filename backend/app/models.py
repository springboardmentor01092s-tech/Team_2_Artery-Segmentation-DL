from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="clinician")


class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    medical_history = Column(Text)
    risk_factors = Column(Text)
    clinical_notes = Column(Text)
    imaging_modality = Column(String, default="Coronary angiography")
    scan_date = Column(String)
    anatomical_region = Column(String)
    image_path = Column(String)
    analysis_status = Column(String, default="Pending")
    model_version = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String)
    role = Column(String)
    action = Column(String, nullable=False)
    detail = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SegmentationResult(Base):
    __tablename__ = "segmentation_results"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    task = Column(String, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))