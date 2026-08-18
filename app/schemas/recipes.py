from pydantic import BaseModel, Field
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


class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    meal_type: Optional[str] = Field(None, max_length=40)
    minutes: Optional[int] = Field(None, ge=0, le=600)
    portions: Optional[int] = Field(None, ge=1, le=50)
    kcal: Optional[int] = Field(None, ge=0, le=5000)
    ingredients: Optional[List[dict[str, Any]]] = None
    steps: Optional[List[str]] = None
    url: Optional[str] = None
