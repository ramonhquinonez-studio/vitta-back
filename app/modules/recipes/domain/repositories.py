from typing import Protocol

from .entities import RecipeCollection


class RecipesRepository(Protocol):
    async def list_for_owner(self, owner_id: str) -> list[RecipeCollection]:
        ...
