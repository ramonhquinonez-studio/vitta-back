from dataclasses import dataclass


@dataclass(frozen=True)
class NutritionMatch:
    fdc_id: int
    description: str
    kcal_per_100g: float | None
    protein_per_100g: float | None
    carbs_per_100g: float | None
    fat_per_100g: float | None


@dataclass(frozen=True)
class FoodPortion:
    """A real, measured household-portion weight for one specific USDA
    food — e.g. "0.5 cup, chopped" = 78g for cooked broccoli. Never a
    generic per-unit constant; always specific to the food it came from.
    """

    description: str
    gram_weight: float
