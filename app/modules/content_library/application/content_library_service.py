from ..domain.entities import Article
from ..domain.repositories import ContentLibraryRepository


class ContentLibraryService:
    def __init__(self, repository: ContentLibraryRepository):
        self._repository = repository

    async def list_articles(self) -> list[Article]:
        return await self._repository.list_articles()

    async def list_my_articles(self, owner_id: str) -> list[Article]:
        return await self._repository.list_for_owner(owner_id)

    async def create(self, owner_id: str, payload: dict) -> Article:
        self._validate(payload)
        return await self._repository.create_for_owner(owner_id, payload)

    async def update(self, owner_id: str, article_id: str, payload: dict) -> Article:
        if not payload:
            raise ValueError("No fields to update")
        updated = await self._repository.update_for_owner(owner_id, article_id, payload)
        if updated is None:
            raise LookupError("Article not found")
        return updated

    async def delete(self, owner_id: str, article_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, article_id)
        if not deleted:
            raise LookupError("Article not found")

    def _validate(self, payload: dict) -> None:
        if not payload.get("title"):
            raise ValueError("title is required")
        has_body = any((section.get("text") or "").strip() for section in payload.get("sections") or [])
        if not has_body and not payload.get("video_url"):
            raise ValueError("Provide either body text or a video URL")
