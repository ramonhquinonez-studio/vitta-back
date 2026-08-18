from pydantic import BaseModel
from typing import Any, List, Optional


class RecipeOut(BaseModel):
    id: str
    title: str
    meal_type: Optional[str] = None
    minutes: Optional[int] = None
    portions: Optional[int] = None
    kcal: Optional[int] = None
    ingredients: List[dict[str, Any]] = []
    steps: List[str] = []
    url: Optional[str] = None


class RecipeCollectionOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    recipes: List[RecipeOut] = []
