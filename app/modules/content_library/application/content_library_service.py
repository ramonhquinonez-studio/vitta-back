from ..domain.entities import Article
from ..domain.repositories import ContentLibraryRepository


class ContentLibraryService:
    def __init__(self, repository: ContentLibraryRepository):
        self._repository = repository

    async def list_articles(self) -> list[Article]:
        return await self._repository.list_articles()
