from typing import Protocol

from .entities import Recommendation


class RecommendationsRepository(Protocol):
    async def list_for_owner(
        self, owner_id: str, *, kind: str | None = None
    ) -> list[Recommendation]:
        ...

    async def create_for_owner(self, owner_id: str, payload: dict) -> Recommendation:
        ...

    async def update_for_owner(
        self, owner_id: str, recommendation_id: str, payload: dict
    ) -> Recommendation | None:
        ...

    async def delete_for_owner(self, owner_id: str, recommendation_id: str) -> bool:
        ...
