from ..domain.entities import FoodPortion, NutritionMatch
from ..domain.repositories import NutritionLookupRepository


class NutritionLookupService:
    def __init__(self, repository: NutritionLookupRepository):
        self._repository = repository

    async def search(self, query: str) -> list[NutritionMatch]:
        query = query.strip()
        if not query:
            raise ValueError("query is required")
        return await self._repository.search(query)

    async def get_portions(self, fdc_id: int) -> list[FoodPortion]:
        return await self._repository.get_portions(fdc_id)
