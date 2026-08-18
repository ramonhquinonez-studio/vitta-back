from pydantic import BaseModel, Field
from typing import List, Optional


class SocialLinkIn(BaseModel):
    platform: str = Field(..., min_length=1, max_length=30)
    handle: str = Field(..., min_length=1, max_length=120)


class NutritionistProfileUpdate(BaseModel):
    role_label: Optional[str] = Field(None, max_length=80)
    bio: Optional[str] = Field(None, max_length=1000)
    years_experience: Optional[int] = Field(None, ge=0, le=80)
    session_price: Optional[float] = Field(None, ge=0)
    session_price_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    social_links: Optional[List[SocialLinkIn]] = None


class SocialLinkOut(BaseModel):
    platform: str
    handle: str


class NutritionistProfileOut(BaseModel):
    role_label: Optional[str] = None
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    session_price: Optional[float] = None
    session_price_currency: str = "MXN"
    social_links: List[SocialLinkOut] = []
    patient_count: int = 0
