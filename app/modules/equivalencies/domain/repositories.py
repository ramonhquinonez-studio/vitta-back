from typing import Protocol

from .entities import EquivalencyFood, EquivalencyGroup


class EquivalenciesRepository(Protocol):
    async def list_groups(self) -> list[EquivalencyGroup]:
        ...

    async def list_foods(
        self, owner_id: str, *, group_id: str | None = None
    ) -> list[EquivalencyFood]:
        ...

    async def create_food(self, owner_id: str, payload: dict) -> EquivalencyFood:
        ...

    async def delete_food(self, owner_id: str, food_id: str) -> bool:
        ...
