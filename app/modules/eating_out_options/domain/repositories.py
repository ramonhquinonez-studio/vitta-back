from typing import Protocol

from .entities import EatingOutOption


class EatingOutOptionsRepository(Protocol):
    async def list_for_owner(self, owner_id: str) -> list[EatingOutOption]:
        ...

    async def create_for_owner(self, owner_id: str, payload: dict) -> EatingOutOption:
        ...

    async def update_for_owner(
        self, owner_id: str, option_id: str, payload: dict
    ) -> EatingOutOption | None:
        ...

    async def delete_for_owner(self, owner_id: str, option_id: str) -> bool:
        ...
