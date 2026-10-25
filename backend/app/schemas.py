from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "clinician"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


class CaseCreate(BaseModel):
    patient_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[str] = None
    risk_factors: Optional[str] = None
    clinical_notes: Optional[str] = None
    imaging_modality: Optional[str] = "Coronary angiography"
    scan_date: Optional[str] = None
    anatomical_region: Optional[str] = None


class CaseOut(CaseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_path: Optional[str] = None
    analysis_status: str
    model_version: Optional[str] = None
    created_at: datetime