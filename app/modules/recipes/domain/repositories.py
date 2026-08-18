from typing import Protocol

from .entities import RecipeCollection


class RecipesRepository(Protocol):
    async def list_for_owner(self, owner_id: str) -> list[RecipeCollection]:
        ...

    async def create_collection(self, owner_id: str, payload: dict) -> RecipeCollection:
        ...

    async def update_collection(
        self, owner_id: str, collection_id: str, payload: dict
    ) -> RecipeCollection | None:
        ...

    async def delete_collection(self, owner_id: str, collection_id: str) -> bool:
        ...

    async def add_recipe(
        self, owner_id: str, collection_id: str, payload: dict
    ) -> RecipeCollection | None:
        ...

    async def update_recipe(
        self, owner_id: str, collection_id: str, recipe_id: str, payload: dict
    ) -> RecipeCollection | None:
        ...

    async def delete_recipe(
        self, owner_id: str, collection_id: str, recipe_id: str
    ) -> RecipeCollection | None:
        ...
