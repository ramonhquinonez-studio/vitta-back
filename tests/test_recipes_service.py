import unittest

from app.modules.recipes.application.recipes_service import RecipesService
from app.modules.recipes.domain.entities import Recipe, RecipeCollection


class _FakeRecipesRepository:
    def __init__(self):
        self.collections: dict[str, list[RecipeCollection]] = {}
        self.sequence = 1

    async def list_for_owner(self, owner_id):
        return self.collections.get(owner_id, [])

    def _find(self, owner_id, collection_id):
        for collection in self.collections.get(owner_id, []):
            if collection.id == collection_id:
                return collection
        return None

    async def create_collection(self, owner_id, payload):
        collection = RecipeCollection(
            id=f"col-{self.sequence}",
            owner_id=owner_id,
            title=payload["title"],
            description=payload.get("description"),
        )
        self.sequence += 1
        self.collections.setdefault(owner_id, []).append(collection)
        return collection

    async def update_collection(self, owner_id, collection_id, payload):
        current = self._find(owner_id, collection_id)
        if current is None:
            return None
        updated = RecipeCollection(
            id=current.id,
            owner_id=current.owner_id,
            title=payload.get("title", current.title),
            description=payload.get("description", current.description),
            recipes=current.recipes,
        )
        self.collections[owner_id] = [
            updated if c.id == collection_id else c for c in self.collections[owner_id]
        ]
        return updated

    async def delete_collection(self, owner_id, collection_id):
        current = self._find(owner_id, collection_id)
        if current is None:
            return False
        self.collections[owner_id] = [
            c for c in self.collections[owner_id] if c.id != collection_id
        ]
        return True

    async def add_recipe(self, owner_id, collection_id, payload):
        current = self._find(owner_id, collection_id)
        if current is None:
            return None
        recipe = Recipe(id=f"recipe-{self.sequence}", title=payload["title"])
        self.sequence += 1
        updated = RecipeCollection(
            id=current.id,
            owner_id=current.owner_id,
            title=current.title,
            description=current.description,
            recipes=[*current.recipes, recipe],
        )
        self.collections[owner_id] = [
            updated if c.id == collection_id else c for c in self.collections[owner_id]
        ]
        return updated

    async def update_recipe(self, owner_id, collection_id, recipe_id, payload):
        current = self._find(owner_id, collection_id)
        if current is None:
            return None
        new_recipes = [
            Recipe(id=r.id, title=payload.get("title", r.title)) if r.id == recipe_id else r
            for r in current.recipes
        ]
        updated = RecipeCollection(
            id=current.id,
            owner_id=current.owner_id,
            title=current.title,
            description=current.description,
            recipes=new_recipes,
        )
        self.collections[owner_id] = [
            updated if c.id == collection_id else c for c in self.collections[owner_id]
        ]
        return updated

    async def delete_recipe(self, owner_id, collection_id, recipe_id):
        current = self._find(owner_id, collection_id)
        if current is None:
            return None
        updated = RecipeCollection(
            id=current.id,
            owner_id=current.owner_id,
            title=current.title,
            description=current.description,
            recipes=[r for r in current.recipes if r.id != recipe_id],
        )
        self.collections[owner_id] = [
            updated if c.id == collection_id else c for c in self.collections[owner_id]
        ]
        return updated


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

    async def test_create_collection_requires_a_title(self):
        repository = _FakeRecipesRepository()
        service = RecipesService(repository)

        with self.assertRaises(ValueError):
            await service.create_collection("owner-1", {})

    async def test_create_then_update_collection_round_trips(self):
        repository = _FakeRecipesRepository()
        service = RecipesService(repository)
        created = await service.create_collection("owner-1", {"title": "Desayunos"})

        updated = await service.update_collection(
            "owner-1", created.id, {"title": "Desayunos saludables"}
        )

        self.assertEqual(updated.title, "Desayunos saludables")

    async def test_update_collection_rejects_a_collection_not_owned(self):
        repository = _FakeRecipesRepository()
        service = RecipesService(repository)
        created = await service.create_collection("owner-1", {"title": "Desayunos"})

        with self.assertRaises(LookupError):
            await service.update_collection("owner-2", created.id, {"title": "x"})

    async def test_delete_collection_removes_it(self):
        repository = _FakeRecipesRepository()
        service = RecipesService(repository)
        created = await service.create_collection("owner-1", {"title": "Desayunos"})

        await service.delete_collection("owner-1", created.id)

        self.assertEqual(await service.list_my_collections("owner-1"), [])

    async def test_add_recipe_requires_a_title(self):
        repository = _FakeRecipesRepository()
        service = RecipesService(repository)
        created = await service.create_collection("owner-1", {"title": "Desayunos"})

        with self.assertRaises(ValueError):
            await service.add_recipe("owner-1", created.id, {})

    async def test_add_then_update_then_delete_recipe(self):
        repository = _FakeRecipesRepository()
        service = RecipesService(repository)
        collection = await service.create_collection("owner-1", {"title": "Desayunos"})

        after_add = await service.add_recipe("owner-1", collection.id, {"title": "Avena"})
        self.assertEqual(len(after_add.recipes), 1)
        recipe_id = after_add.recipes[0].id

        after_update = await service.update_recipe(
            "owner-1", collection.id, recipe_id, {"title": "Avena con fruta"}
        )
        self.assertEqual(after_update.recipes[0].title, "Avena con fruta")

        after_delete = await service.delete_recipe("owner-1", collection.id, recipe_id)
        self.assertEqual(after_delete.recipes, [])


if __name__ == "__main__":
    unittest.main()
