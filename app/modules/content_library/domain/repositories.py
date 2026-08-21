from typing import Protocol

from .entities import Article


class ContentLibraryRepository(Protocol):
    async def list_articles(self) -> list[Article]:
        ...
