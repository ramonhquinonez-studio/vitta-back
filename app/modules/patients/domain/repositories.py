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

    async def add_body_composition(self, owner_id: str, patient_id: str, payload: dict) -> dict | None:
        ...

    async def list_body_compositions(self, owner_id: str, patient_id: str) -> list[dict] | None:
        ...

    async def list_food_diary_entries(self, owner_id: str, patient_id: str) -> list[dict] | None:
        ...

    async def list_plan_assignments(self, owner_id: str, patient_id: str) -> list[dict] | None:
        ...

    async def list_measurements(self, owner_id: str, patient_id: str) -> list[dict] | None:
        ...

    async def list_checkin_responses(self, owner_id: str, patient_id: str) -> list[dict] | None:
        ...

    async def list_workout_plan_assignments(self, owner_id: str, patient_id: str) -> list[dict] | None:
        ...

    async def list_workout_logs(self, owner_id: str, patient_id: str) -> list[dict] | None:
        ...

    async def create_invite_code(self, owner_id: str, patient_id: str | None = None) -> dict:
        ...

    async def claim_patient(self, owner_id: str, code: str) -> Patient | None:
        ...

    async def count_for_owner(self, owner_id: str) -> int:
        ...


class PatientQuotaChecker(Protocol):
    """Dependency-inversion seam so `patients` can enforce a nutritionist's
    subscription limit without importing anything from `billing`. The
    presentation layer wires a concrete adapter satisfying this shape."""

    async def check(self, owner_id: str) -> None:
        """Raise PermissionError when the owner is at/over their plan's
        patient limit."""
        ...
