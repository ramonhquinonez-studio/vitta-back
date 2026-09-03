from dataclasses import dataclass


@dataclass(frozen=True)
class EatingOutOption:
    id: str
    owner_id: str
    restaurant: str
    dish: str
    kcal: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
