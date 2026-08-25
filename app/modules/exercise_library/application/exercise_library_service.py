from ..domain.repositories import ExerciseLibraryRepository


class ExerciseLibraryService:
    def __init__(self, repository: ExerciseLibraryRepository):
        self._repository = repository

    async def list_items(self, owner_id: str) -> list[dict]:
        return await self._repository.list_for_owner(owner_id)

    async def create_item(self, owner_id: str, payload: dict) -> dict:
        if not payload.get("name"):
            raise ValueError("name is required")
        return await self._repository.create_for_owner(owner_id, payload)

    async def delete_item(self, owner_id: str, item_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, item_id)
        if not deleted:
            raise LookupError("Exercise not found")
