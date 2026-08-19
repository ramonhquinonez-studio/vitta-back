from pydantic import BaseModel, Field
from typing import Optional, List

class PatientIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    height_cm: Optional[float] = Field(None, ge=30, le=250)
    allergies: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)

class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    height_cm: Optional[float] = Field(None, ge=30, le=250)
    allergies: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)

class PatientOut(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    allergies: Optional[List[str]] = None
    notes: Optional[str] = None
    owner_id: str
    user_id: Optional[str] = None
