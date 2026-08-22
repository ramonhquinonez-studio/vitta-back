from typing import Protocol

from .entities import Article


class ContentLibraryRepository(Protocol):
    async def list_articles(self) -> list[Article]:
        ...

    async def list_for_owner(self, owner_id: str) -> list[Article]:
        ...

    async def create_for_owner(self, owner_id: str, payload: dict) -> Article:
        ...

    async def update_for_owner(
        self, owner_id: str, article_id: str, payload: dict
    ) -> Article | None:
        ...

    async def delete_for_owner(self, owner_id: str, article_id: str) -> bool:
        ...
