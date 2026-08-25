from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class PlanMealItem(BaseModel):
    name: str
    qty: float
    unit: str
    recipe_id: Optional[str] = None
    equivalency_group_id: Optional[str] = None
    equivalency_food_id: Optional[str] = None
    equivalents: Optional[float] = None
    kcal: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    # Whether `qty` was measured raw or already cooked (e.g. "150 g" of
    # chicken breast could mean either) — `equivalent_qty` is the *other*
    # state's weight, in the same `unit`, so a patient shopping/prepping
    # sees both without needing to know a conversion ratio themselves.
    cooking_state: Optional[Literal['raw', 'cooked']] = None
    equivalent_qty: Optional[float] = None
    # Grams represented by one `unit` of this specific item (e.g. "1 taza"
    # of cooked rice vs. rolled oats vs. milk are very different weights) —
    # sourced from a real USDA portion when the nutritionist picks one,
    # never a generic per-unit constant. Null when `unit` is already a
    # weight unit, or when no USDA portion was available/picked.
    unit_gram_weight: Optional[float] = None

class EatingOutOption(BaseModel):
    restaurant: str
    dish: str
    kcal: Optional[float] = None
    protein: Optional[float] = None

class PlanMeal(BaseModel):
    title: str
    dish_name: Optional[str] = None
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
