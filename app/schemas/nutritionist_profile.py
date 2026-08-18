from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class SocialLinkIn(BaseModel):
    platform: str = Field(..., min_length=1, max_length=30)
    handle: str = Field(..., min_length=1, max_length=120)


class MacroSplitIn(BaseModel):
    protein_pct: float = Field(..., ge=0, le=100)
    carbs_pct: float = Field(..., ge=0, le=100)
    fat_pct: float = Field(..., ge=0, le=100)


class NutritionistProfileUpdate(BaseModel):
    role_label: Optional[str] = Field(None, max_length=80)
    bio: Optional[str] = Field(None, max_length=1000)
    years_experience: Optional[int] = Field(None, ge=0, le=80)
    session_price: Optional[float] = Field(None, ge=0)
    session_price_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    social_links: Optional[List[SocialLinkIn]] = None
    # Professional profile
    cedula: Optional[str] = Field(None, max_length=40)
    practice_name: Optional[str] = Field(None, max_length=120)
    logo_url: Optional[str] = None
    brand_color: Optional[str] = Field(None, max_length=9)
    city: Optional[str] = Field(None, max_length=80)
    # Specialization
    specializations: Optional[List[str]] = None
    # Workflow defaults
    energy_equation: Optional[Literal["mifflin", "harris_benedict", "fao_oms"]] = None
    portions_mode: Optional[Literal["equivalentes", "gramos", "ambos"]] = None
    macro_split: Optional[MacroSplitIn] = None
    units: Optional[Literal["metric", "imperial"]] = None
    meals_per_day: Optional[int] = Field(None, ge=1, le=10)


class SocialLinkOut(BaseModel):
    platform: str
    handle: str


class MacroSplitOut(BaseModel):
    protein_pct: float
    carbs_pct: float
    fat_pct: float


class NutritionistProfileOut(BaseModel):
    role_label: Optional[str] = None
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    session_price: Optional[float] = None
    session_price_currency: str = "MXN"
    social_links: List[SocialLinkOut] = []
    cedula: Optional[str] = None
    practice_name: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    city: Optional[str] = None
    specializations: List[str] = []
    energy_equation: Optional[str] = None
    portions_mode: Optional[str] = None
    macro_split: Optional[MacroSplitOut] = None
    units: Optional[str] = None
    meals_per_day: Optional[int] = None
    onboarding_completed_at: Optional[datetime] = None
    patient_count: int = 0
