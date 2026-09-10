from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List

from app.schemas.body_measurements import CIRCUMFERENCE_SITES


def _clean_circumference_goals(value: Optional[dict]) -> Optional[dict]:
    """Validate a `{site: cm}` goal map against the shared site vocabulary."""
    if value is None:
        return None
    cleaned: dict[str, float] = {}
    for site, cm in value.items():
        if site not in CIRCUMFERENCE_SITES:
            raise ValueError(f"unknown circumference site: {site}")
        if cm is None:
            continue
        if not (0 < float(cm) <= 300):
            raise ValueError(f"{site} goal must be between 0 and 300 cm")
        cleaned[site] = round(float(cm), 1)
    return cleaned


class PatientIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    height_cm: Optional[float] = Field(None, ge=30, le=250)
    allergies: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    tags: Optional[List[str]] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    height_cm: Optional[float] = Field(None, ge=30, le=250)
    allergies: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)
    daily_kcal_goal: Optional[float] = Field(None, ge=0, le=10000)
    daily_protein_g_goal: Optional[float] = Field(None, ge=0, le=1000)
    daily_carbs_g_goal: Optional[float] = Field(None, ge=0, le=2000)
    daily_fat_g_goal: Optional[float] = Field(None, ge=0, le=1000)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    tags: Optional[List[str]] = None
    # Nutritionist-only — stripped from the patient's own PATCH /me/profile (spec 083).
    progress_log_enabled: Optional[bool] = None
    # Nutritionist-only (spec 085) — per-site circumference targets (cm). An empty
    # dict clears every goal; omitting the key leaves them untouched. Also
    # stripped from PATCH /me/profile.
    circumference_goals: Optional[dict[str, float]] = None

    @field_validator("circumference_goals")
    @classmethod
    def _clean_goals(cls, value):
        return _clean_circumference_goals(value)

class PatientOut(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    allergies: Optional[List[str]] = None
    notes: Optional[str] = None
    # None means self-registered with no nutritionist yet.
    owner_id: Optional[str] = None
    user_id: Optional[str] = None
    daily_kcal_goal: Optional[float] = None
    daily_protein_g_goal: Optional[float] = None
    daily_carbs_g_goal: Optional[float] = None
    daily_fat_g_goal: Optional[float] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    archived_at: Optional[datetime] = None
    tags: List[str] = []
    progress_log_enabled: bool = True
    circumference_goals: dict[str, float] = {}

class ClaimPatientIn(BaseModel):
    code: str = Field(..., min_length=4, max_length=40)
