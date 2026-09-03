from pydantic import BaseModel, Field
from typing import Any, List, Optional


class RecipeEatingOutOption(BaseModel):
    """An eating-out alternative for this recipe's meal slot — mirrors
    `app.schemas.plan.EatingOutOption`'s exact shape, since a recipe's
    linked option gets copied into a `PlanMeal.eating_out_options` entry
    verbatim when the recipe is used in a plan (`nutri_pro`'s
    `linkRecipe`/`useFullRecipe`)."""

    restaurant: str
    dish: str
    kcal: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


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
    eating_out_option: Optional[RecipeEatingOutOption] = None


class RecipeCollectionOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    recipes: List[RecipeOut] = []


class RecipeCollectionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)


class RecipeCollectionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)


class RecipeIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    meal_type: Optional[str] = Field(None, max_length=40)
    minutes: Optional[int] = Field(None, ge=0, le=600)
    portions: Optional[int] = Field(None, ge=1, le=50)
    kcal: Optional[int] = Field(None, ge=0, le=5000)
    ingredients: List[dict[str, Any]] = []
    steps: List[str] = []
    url: Optional[str] = None
    eating_out_option: Optional[RecipeEatingOutOption] = None


class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    meal_type: Optional[str] = Field(None, max_length=40)
    minutes: Optional[int] = Field(None, ge=0, le=600)
    portions: Optional[int] = Field(None, ge=1, le=50)
    kcal: Optional[int] = Field(None, ge=0, le=5000)
    ingredients: Optional[List[dict[str, Any]]] = None
    steps: Optional[List[str]] = None
    url: Optional[str] = None
    eating_out_option: Optional[RecipeEatingOutOption] = None
