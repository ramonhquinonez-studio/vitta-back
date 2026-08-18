import unittest

from app.modules.equivalencies.application.equivalencies_service import EquivalenciesService
from app.modules.equivalencies.domain.entities import EquivalencyFood, EquivalencyGroup


class _FakeEquivalenciesRepository:
    def __init__(self):
        self.groups = [
            EquivalencyGroup(
                id="cereales_sin_grasa", name="Cereales sin grasa",
                kcal=70, carbs_g=15, protein_g=2, fat_g=0,
            ),
            EquivalencyGroup(
                id="frutas", name="Frutas", kcal=60, carbs_g=15, protein_g=0, fat_g=0,
            ),
        ]
        self.foods: list[EquivalencyFood] = [
            EquivalencyFood(
                id="food-1", group_id="cereales_sin_grasa", name="Tortilla de maíz",
                portion_description="1 pieza", owner_id=None,
            ),
        ]
        self.sequence = 2

    async def list_groups(self):
        return self.groups

    async def list_foods(self, owner_id, *, group_id=None):
        items = [f for f in self.foods if f.owner_id is None or f.owner_id == owner_id]
        if group_id:
            items = [f for f in items if f.group_id == group_id]
        return items

    async def create_food(self, owner_id, payload):
        food = EquivalencyFood(
            id=f"food-{self.sequence}",
            group_id=payload["group_id"],
            name=payload["name"],
            portion_description=payload.get("portion_description") or "",
            owner_id=owner_id,
        )
        self.sequence += 1
        self.foods.append(food)
        return food

    async def delete_food(self, owner_id, food_id):
        for food in self.foods:
            if food.id == food_id and food.owner_id == owner_id:
                self.foods.remove(food)
                return True
        return False


class EquivalenciesServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_list_groups_returns_the_full_catalog(self):
        repository = _FakeEquivalenciesRepository()
        service = EquivalenciesService(repository)

        groups = await service.list_groups()

        self.assertEqual(len(groups), 2)

    async def test_list_foods_includes_global_and_owned_foods(self):
        repository = _FakeEquivalenciesRepository()
        service = EquivalenciesService(repository)
        await repository.create_food("owner-1", {"group_id": "frutas", "name": "Mango"})

        foods_for_owner = await service.list_foods("owner-1")
        foods_for_other = await service.list_foods("owner-2")

        self.assertEqual({f.name for f in foods_for_owner}, {"Tortilla de maíz", "Mango"})
        self.assertEqual({f.name for f in foods_for_other}, {"Tortilla de maíz"})

    async def test_list_foods_filters_by_group(self):
        repository = _FakeEquivalenciesRepository()
        service = EquivalenciesService(repository)

        foods = await service.list_foods("owner-1", group_id="frutas")

        self.assertEqual(foods, [])

    async def test_create_food_requires_a_name(self):
        repository = _FakeEquivalenciesRepository()
        service = EquivalenciesService(repository)

        with self.assertRaises(ValueError):
            await service.create_food("owner-1", {"group_id": "frutas"})

    async def test_create_food_requires_a_group_id(self):
        repository = _FakeEquivalenciesRepository()
        service = EquivalenciesService(repository)

        with self.assertRaises(ValueError):
            await service.create_food("owner-1", {"name": "Mango"})

    async def test_delete_food_rejects_a_food_not_owned(self):
        repository = _FakeEquivalenciesRepository()
        service = EquivalenciesService(repository)
        created = await service.create_food("owner-1", {"group_id": "frutas", "name": "Mango"})

        with self.assertRaises(LookupError):
            await service.delete_food("owner-2", created.id)

    async def test_delete_food_removes_an_owned_food(self):
        repository = _FakeEquivalenciesRepository()
        service = EquivalenciesService(repository)
        created = await service.create_food("owner-1", {"group_id": "frutas", "name": "Mango"})

        await service.delete_food("owner-1", created.id)

        remaining = await service.list_foods("owner-1", group_id="frutas")
        self.assertEqual(remaining, [])


if __name__ == "__main__":
    unittest.main()
