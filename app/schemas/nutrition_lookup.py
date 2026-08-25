from pydantic import BaseModel


class NutritionMatchOut(BaseModel):
    fdc_id: int
    description: str
    kcal_per_100g: float | None
    protein_per_100g: float | None
    carbs_per_100g: float | None
    fat_per_100g: float | None


class FoodPortionOut(BaseModel):
    description: str
    gram_weight: float
