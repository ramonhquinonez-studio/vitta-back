from typing import Protocol


class ExerciseLibraryRepository(Protocol):
    async def list_for_owner(self, owner_id: str) -> list[dict]:
        ...

    async def list_platform_items(self) -> list[dict]:
        ...

    async def get_platform_item(self, item_id: str) -> dict | None:
        ...

    async def update_platform_item_video_url(self, item_id: str, video_url: str) -> None:
        ...

    async def create_for_owner(self, owner_id: str, payload: dict) -> dict:
        ...

    async def delete_for_owner(self, owner_id: str, item_id: str) -> bool:
        ...
