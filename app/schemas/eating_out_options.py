from pydantic import BaseModel, Field
from typing import Optional


class EatingOutOptionOut(BaseModel):
    id: str
    restaurant: str
    dish: str
    kcal: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


class EatingOutOptionCreate(BaseModel):
    restaurant: str = Field(..., min_length=1, max_length=120)
    dish: str = Field(..., min_length=1, max_length=120)
    kcal: Optional[float] = Field(None, ge=0, le=10000)
    protein: Optional[float] = Field(None, ge=0, le=1000)
    carbs: Optional[float] = Field(None, ge=0, le=1000)
    fat: Optional[float] = Field(None, ge=0, le=1000)


class EatingOutOptionUpdate(BaseModel):
    restaurant: Optional[str] = Field(None, min_length=1, max_length=120)
    dish: Optional[str] = Field(None, min_length=1, max_length=120)
    kcal: Optional[float] = Field(None, ge=0, le=10000)
    protein: Optional[float] = Field(None, ge=0, le=1000)
    carbs: Optional[float] = Field(None, ge=0, le=1000)
    fat: Optional[float] = Field(None, ge=0, le=1000)
