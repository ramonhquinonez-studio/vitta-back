from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

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

class ClaimPatientIn(BaseModel):
    code: str = Field(..., min_length=4, max_length=40)
