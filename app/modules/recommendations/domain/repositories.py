from typing import Protocol

from .entities import Recommendation


class RecommendationsRepository(Protocol):
    async def list_for_owner(
        self, owner_id: str, *, kind: str | None = None
    ) -> list[Recommendation]:
        ...

    async def create_for_owner(self, owner_id: str, payload: dict) -> Recommendation:
        ...

    async def update_for_owner(
        self, owner_id: str, recommendation_id: str, payload: dict
    ) -> Recommendation | None:
        ...

    async def delete_for_owner(self, owner_id: str, recommendation_id: str) -> bool:
        ...

    async def list_platform_recommendations(
        self, *, kind: str | None = None
    ) -> list[Recommendation]:
        ...

    async def assign_to_patients(
        self, owner_id: str, recommendation_id: str, patient_ids: list[str]
    ) -> int:
        ...

    async def unassign_from_patient(
        self, owner_id: str, recommendation_id: str, patient_id: str
    ) -> bool:
        ...

    async def list_assigned_patient_ids(
        self, owner_id: str, recommendation_id: str
    ) -> list[str]:
        ...
