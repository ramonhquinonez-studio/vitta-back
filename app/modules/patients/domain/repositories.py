from typing import Protocol

from .entities import Patient


class PatientsRepository(Protocol):
    async def list_for_owner(
        self,
        owner_id: str,
        *,
        page: int,
        limit: int,
        query: str | None = None,
    ) -> tuple[list[Patient], int]:
        ...

    async def create_for_owner(self, owner_id: str, payload: dict) -> Patient:
        ...

    async def get_for_owner(self, owner_id: str, patient_id: str) -> Patient | None:
        ...

    async def update_for_owner(self, owner_id: str, patient_id: str, payload: dict) -> Patient | None:
        ...

    async def delete_for_owner(self, owner_id: str, patient_id: str) -> bool:
        ...
