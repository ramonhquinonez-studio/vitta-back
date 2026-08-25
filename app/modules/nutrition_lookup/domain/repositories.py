from typing import Protocol

from .entities import FoodPortion, NutritionMatch


class NutritionLookupRepository(Protocol):
    async def search(self, query: str, limit: int = 10) -> list[NutritionMatch]:
        ...

    async def get_portions(self, fdc_id: int) -> list[FoodPortion]:
        ...
