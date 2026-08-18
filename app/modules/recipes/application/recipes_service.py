from ..domain.entities import RecipeCollection
from ..domain.repositories import RecipesRepository


class RecipesService:
    def __init__(self, repository: RecipesRepository):
        self._repository = repository

    async def list_my_collections(self, owner_id: str) -> list[RecipeCollection]:
        return await self._repository.list_for_owner(owner_id)
