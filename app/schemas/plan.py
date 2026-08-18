from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class PlanMealItem(BaseModel):
    name: str
    qty: float
    unit: str
    recipe_id: Optional[str] = None

class EatingOutOption(BaseModel):
    restaurant: str
    dish: str
    kcal: Optional[float] = None
    protein: Optional[float] = None

class PlanMeal(BaseModel):
    title: str
    time: Optional[str] = None
    items: List[PlanMealItem] = Field(default_factory=list)
    eating_out_options: List[EatingOutOption] = Field(default_factory=list)

class PlanCreate(BaseModel):
    name: str
    goal: Literal['weight_loss','muscle_gain','maintenance','custom'] = 'custom'
    # acepta camelCase desde el front
    duration_days: int = Field(validation_alias='durationDays')
    meals: List[PlanMeal] = Field(default_factory=list)
    model_config = ConfigDict(populate_by_name=True)

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[Literal['weight_loss','muscle_gain','maintenance','custom']] = None
    duration_days: Optional[int] = Field(default=None, validation_alias='durationDays')
    meals: Optional[List[PlanMeal]] = None
    model_config = ConfigDict(populate_by_name=True)

class PlanOut(BaseModel):
    id: str
    name: str
    goal: str
    duration_days: int
    meals: List[PlanMeal]
    created_at: datetime
    updated_at: datetime
    attachment_url: Optional[str] = None
    attachment_type: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)
