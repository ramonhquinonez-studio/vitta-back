from ..domain.entities import EatingOutOption
from ..domain.repositories import EatingOutOptionsRepository


class EatingOutOptionsService:
    def __init__(self, repository: EatingOutOptionsRepository):
        self._repository = repository

    async def list_my_options(self, owner_id: str) -> list[EatingOutOption]:
        return await self._repository.list_for_owner(owner_id)

    async def create_option(self, owner_id: str, payload: dict) -> EatingOutOption:
        self._validate(payload)
        return await self._repository.create_for_owner(owner_id, payload)

    def _validate(self, payload: dict) -> None:
        if not payload.get("restaurant"):
            raise ValueError("restaurant is required")
        if not payload.get("dish"):
            raise ValueError("dish is required")

    async def update_option(self, owner_id: str, option_id: str, payload: dict) -> EatingOutOption:
        if not payload:
            raise ValueError("No fields to update")
        updated = await self._repository.update_for_owner(owner_id, option_id, payload)
        if updated is None:
            raise LookupError("Eating-out option not found")
        return updated

    async def delete_option(self, owner_id: str, option_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, option_id)
        if not deleted:
            raise LookupError("Eating-out option not found")
