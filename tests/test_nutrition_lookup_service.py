import unittest

from app.modules.nutrition_lookup.application.nutrition_lookup_service import (
    NutritionLookupService,
)
from app.modules.nutrition_lookup.domain.entities import FoodPortion, NutritionMatch


class _FakeNutritionLookupRepository:
    def __init__(self):
        self.last_query = None
        self.last_fdc_id = None

    async def search(self, query: str, limit: int = 10):
        self.last_query = query
        return [
            NutritionMatch(
                fdc_id=171477,
                description="Chicken, broilers or fryers, breast, meat only, cooked, roasted",
                kcal_per_100g=165.0,
                protein_per_100g=31.0,
                carbs_per_100g=0.0,
                fat_per_100g=3.57,
            )
        ]

    async def get_portions(self, fdc_id: int):
        self.last_fdc_id = fdc_id
        return [FoodPortion(description="0.5 cup, chopped", gram_weight=78.0)]


class NutritionLookupServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_search_delegates_to_repository(self):
        repo = _FakeNutritionLookupRepository()
        service = NutritionLookupService(repo)

        matches = await service.search("  chicken breast  ")

        self.assertEqual(repo.last_query, "chicken breast")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].fdc_id, 171477)
        self.assertEqual(matches[0].protein_per_100g, 31.0)

    async def test_search_rejects_blank_query(self):
        service = NutritionLookupService(_FakeNutritionLookupRepository())

        with self.assertRaises(ValueError):
            await service.search("   ")

    async def test_get_portions_delegates_to_repository(self):
        repo = _FakeNutritionLookupRepository()
        service = NutritionLookupService(repo)

        portions = await service.get_portions(169967)

        self.assertEqual(repo.last_fdc_id, 169967)
        self.assertEqual(len(portions), 1)
        self.assertEqual(portions[0].gram_weight, 78.0)


if __name__ == "__main__":
    unittest.main()
