import unittest

from app.modules.eating_out_options.application.eating_out_options_service import (
    EatingOutOptionsService,
)
from app.modules.eating_out_options.domain.entities import EatingOutOption


class _FakeEatingOutOptionsRepository:
    def __init__(self):
        self.items: dict[str, list[EatingOutOption]] = {}
        self.sequence = 1

    async def list_for_owner(self, owner_id):
        return self.items.get(owner_id, [])

    async def create_for_owner(self, owner_id, payload):
        option = EatingOutOption(
            id=f"option-{self.sequence}",
            owner_id=owner_id,
            restaurant=payload["restaurant"],
            dish=payload["dish"],
            kcal=payload.get("kcal"),
            protein=payload.get("protein"),
            carbs=payload.get("carbs"),
            fat=payload.get("fat"),
        )
        self.sequence += 1
        self.items.setdefault(owner_id, []).append(option)
        return option

    def _find(self, owner_id, option_id):
        for option in self.items.get(owner_id, []):
            if option.id == option_id:
                return option
        return None

    async def update_for_owner(self, owner_id, option_id, payload):
        current = self._find(owner_id, option_id)
        if current is None:
            return None
        updated = EatingOutOption(
            id=current.id,
            owner_id=current.owner_id,
            restaurant=payload.get("restaurant", current.restaurant),
            dish=payload.get("dish", current.dish),
            kcal=payload.get("kcal", current.kcal),
            protein=payload.get("protein", current.protein),
            carbs=payload.get("carbs", current.carbs),
            fat=payload.get("fat", current.fat),
        )
        self.items[owner_id] = [
            updated if o.id == option_id else o for o in self.items[owner_id]
        ]
        return updated

    async def delete_for_owner(self, owner_id, option_id):
        current = self._find(owner_id, option_id)
        if current is None:
            return False
        self.items[owner_id] = [o for o in self.items[owner_id] if o.id != option_id]
        return True


class EatingOutOptionsServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_option_requires_a_restaurant(self):
        repository = _FakeEatingOutOptionsRepository()
        service = EatingOutOptionsService(repository)

        with self.assertRaises(ValueError):
            await service.create_option("owner-1", {"dish": "Tacos al pastor"})

    async def test_create_option_requires_a_dish(self):
        repository = _FakeEatingOutOptionsRepository()
        service = EatingOutOptionsService(repository)

        with self.assertRaises(ValueError):
            await service.create_option("owner-1", {"restaurant": "El Fogoncito"})

    async def test_create_then_list_returns_the_owners_options(self):
        repository = _FakeEatingOutOptionsRepository()
        service = EatingOutOptionsService(repository)

        await service.create_option(
            "owner-1", {"restaurant": "El Fogoncito", "dish": "Tacos al pastor", "kcal": 450}
        )

        options = await service.list_my_options("owner-1")

        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].restaurant, "El Fogoncito")
        self.assertEqual(options[0].dish, "Tacos al pastor")
        self.assertEqual(options[0].kcal, 450)

    async def test_update_then_delete_option(self):
        repository = _FakeEatingOutOptionsRepository()
        service = EatingOutOptionsService(repository)
        created = await service.create_option(
            "owner-1", {"restaurant": "El Fogoncito", "dish": "Tacos al pastor"}
        )

        updated = await service.update_option("owner-1", created.id, {"kcal": 500})
        self.assertEqual(updated.kcal, 500)

        await service.delete_option("owner-1", created.id)
        self.assertEqual(await service.list_my_options("owner-1"), [])

    async def test_update_rejects_an_option_not_owned(self):
        repository = _FakeEatingOutOptionsRepository()
        service = EatingOutOptionsService(repository)
        created = await service.create_option(
            "owner-1", {"restaurant": "El Fogoncito", "dish": "Tacos al pastor"}
        )

        with self.assertRaises(LookupError):
            await service.update_option("owner-2", created.id, {"kcal": 500})

    async def test_delete_rejects_an_option_not_owned(self):
        repository = _FakeEatingOutOptionsRepository()
        service = EatingOutOptionsService(repository)
        created = await service.create_option(
            "owner-1", {"restaurant": "El Fogoncito", "dish": "Tacos al pastor"}
        )

        with self.assertRaises(LookupError):
            await service.delete_option("owner-2", created.id)


if __name__ == "__main__":
    unittest.main()
