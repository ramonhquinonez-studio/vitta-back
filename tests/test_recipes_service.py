import unittest

from app.modules.recipes.application.recipes_service import RecipesService
from app.modules.recipes.domain.entities import Recipe, RecipeCollection


class _FakeRecipesRepository:
    def __init__(self):
        self.collections: dict[str, list[RecipeCollection]] = {}

    async def list_for_owner(self, owner_id):
        return self.collections.get(owner_id, [])


class RecipesServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_list_my_collections_returns_the_owners_collections(self):
        repository = _FakeRecipesRepository()
        repository.collections["owner-1"] = [
            RecipeCollection(
                id="col-1",
                owner_id="owner-1",
                title="Desayunos",
                recipes=[Recipe(id="r-1", title="Avena con fruta")],
            )
        ]
        service = RecipesService(repository)

        result = await service.list_my_collections("owner-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Desayunos")
        self.assertEqual(result[0].recipes[0].title, "Avena con fruta")

    async def test_list_my_collections_returns_empty_for_owner_with_none(self):
        repository = _FakeRecipesRepository()
        service = RecipesService(repository)

        result = await service.list_my_collections("owner-without-recipes")

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
