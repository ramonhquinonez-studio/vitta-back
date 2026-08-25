from typing import Protocol


class ExerciseLibraryRepository(Protocol):
    async def list_for_owner(self, owner_id: str) -> list[dict]:
        ...

    async def create_for_owner(self, owner_id: str, payload: dict) -> dict:
        ...

    async def delete_for_owner(self, owner_id: str, item_id: str) -> bool:
        ...
