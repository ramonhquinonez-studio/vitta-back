from ..domain.entities import RecipeCollection
from ..domain.repositories import RecipesRepository


class RecipesService:
    def __init__(self, repository: RecipesRepository):
        self._repository = repository

    async def list_my_collections(self, owner_id: str) -> list[RecipeCollection]:
        return await self._repository.list_for_owner(owner_id)

    async def create_collection(self, owner_id: str, payload: dict) -> RecipeCollection:
        if not payload.get("title"):
            raise ValueError("title is required")
        return await self._repository.create_collection(owner_id, payload)

    async def update_collection(
        self, owner_id: str, collection_id: str, payload: dict
    ) -> RecipeCollection:
        if not payload:
            raise ValueError("No fields to update")
        updated = await self._repository.update_collection(owner_id, collection_id, payload)
        if updated is None:
            raise LookupError("Recipe collection not found")
        return updated

    async def delete_collection(self, owner_id: str, collection_id: str) -> None:
        deleted = await self._repository.delete_collection(owner_id, collection_id)
        if not deleted:
            raise LookupError("Recipe collection not found")

    async def add_recipe(
        self, owner_id: str, collection_id: str, payload: dict
    ) -> RecipeCollection:
        if not payload.get("title"):
            raise ValueError("title is required")
        updated = await self._repository.add_recipe(owner_id, collection_id, payload)
        if updated is None:
            raise LookupError("Recipe collection not found")
        return updated

    async def update_recipe(
        self, owner_id: str, collection_id: str, recipe_id: str, payload: dict
    ) -> RecipeCollection:
        if not payload:
            raise ValueError("No fields to update")
        updated = await self._repository.update_recipe(owner_id, collection_id, recipe_id, payload)
        if updated is None:
            raise LookupError("Recipe collection or recipe not found")
        return updated

    async def delete_recipe(
        self, owner_id: str, collection_id: str, recipe_id: str
    ) -> RecipeCollection:
        updated = await self._repository.delete_recipe(owner_id, collection_id, recipe_id)
        if updated is None:
            raise LookupError("Recipe collection not found")
        return updated
