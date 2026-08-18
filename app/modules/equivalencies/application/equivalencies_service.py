from ..domain.entities import EquivalencyFood, EquivalencyGroup
from ..domain.repositories import EquivalenciesRepository


class EquivalenciesService:
    def __init__(self, repository: EquivalenciesRepository):
        self._repository = repository

    async def list_groups(self) -> list[EquivalencyGroup]:
        return await self._repository.list_groups()

    async def list_foods(
        self, owner_id: str, *, group_id: str | None = None
    ) -> list[EquivalencyFood]:
        return await self._repository.list_foods(owner_id, group_id=group_id)

    async def create_food(self, owner_id: str, payload: dict) -> EquivalencyFood:
        if not payload.get("name"):
            raise ValueError("name is required")
        if not payload.get("group_id"):
            raise ValueError("group_id is required")
        return await self._repository.create_food(owner_id, payload)

    async def delete_food(self, owner_id: str, food_id: str) -> None:
        deleted = await self._repository.delete_food(owner_id, food_id)
        if not deleted:
            raise LookupError("Food not found")
