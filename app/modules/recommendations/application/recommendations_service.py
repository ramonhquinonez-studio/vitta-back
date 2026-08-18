from ..domain.entities import Recommendation
from ..domain.repositories import RecommendationsRepository

_VALID_KINDS = {"supplement", "brand"}


class RecommendationsService:
    def __init__(self, repository: RecommendationsRepository):
        self._repository = repository

    async def list_my_recommendations(
        self, owner_id: str, *, kind: str | None = None
    ) -> list[Recommendation]:
        return await self._repository.list_for_owner(owner_id, kind=kind)

    async def create_recommendation(self, owner_id: str, payload: dict) -> Recommendation:
        if not payload.get("title"):
            raise ValueError("title is required")
        if payload.get("kind") not in _VALID_KINDS:
            raise ValueError("kind must be 'supplement' or 'brand'")
        return await self._repository.create_for_owner(owner_id, payload)

    async def update_recommendation(
        self, owner_id: str, recommendation_id: str, payload: dict
    ) -> Recommendation:
        if not payload:
            raise ValueError("No fields to update")
        updated = await self._repository.update_for_owner(owner_id, recommendation_id, payload)
        if updated is None:
            raise LookupError("Recommendation not found")
        return updated

    async def delete_recommendation(self, owner_id: str, recommendation_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, recommendation_id)
        if not deleted:
            raise LookupError("Recommendation not found")
