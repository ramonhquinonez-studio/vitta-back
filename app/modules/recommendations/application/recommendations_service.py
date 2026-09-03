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
        self._validate(payload)
        return await self._repository.create_for_owner(owner_id, payload)

    async def create_bulk(self, owner_id: str, items: list[dict]) -> list[Recommendation]:
        # Validate every item before creating any of them, so a bad row
        # partway through a long pasted list doesn't leave the catalog
        # half-imported.
        for payload in items:
            self._validate(payload)
        return [await self._repository.create_for_owner(owner_id, payload) for payload in items]

    def _validate(self, payload: dict) -> None:
        if not payload.get("title"):
            raise ValueError("title is required")
        if payload.get("kind") not in _VALID_KINDS:
            raise ValueError("kind must be 'supplement' or 'brand'")

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

    async def list_platform_recommendations(
        self, *, kind: str | None = None
    ) -> list[Recommendation]:
        return await self._repository.list_platform_recommendations(kind=kind)

    async def assign_to_patients(
        self, owner_id: str, recommendation_id: str, patient_ids: list[str]
    ) -> int:
        if not patient_ids:
            raise ValueError("patient_ids is required")
        count = await self._repository.assign_to_patients(owner_id, recommendation_id, patient_ids)
        if count == 0:
            raise LookupError("Recommendation not found")
        return count

    async def unassign_from_patient(
        self, owner_id: str, recommendation_id: str, patient_id: str
    ) -> None:
        removed = await self._repository.unassign_from_patient(owner_id, recommendation_id, patient_id)
        if not removed:
            raise LookupError("Assignment not found")

    async def list_assignments(self, owner_id: str, recommendation_id: str) -> list[str]:
        return await self._repository.list_assigned_patient_ids(owner_id, recommendation_id)
