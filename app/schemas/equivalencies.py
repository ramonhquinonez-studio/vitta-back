from typing import Optional

from pydantic import BaseModel, Field


class EquivalencyGroupOut(BaseModel):
    id: str
    name: str
    kcal: float
    carbs_g: float
    protein_g: float
    fat_g: float


class EquivalencyFoodOut(BaseModel):
    id: str
    group_id: str
    name: str
    portion_description: str
    owner_id: Optional[str] = None


class EquivalencyFoodCreate(BaseModel):
    group_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=120)
    portion_description: Optional[str] = Field(None, max_length=80)
