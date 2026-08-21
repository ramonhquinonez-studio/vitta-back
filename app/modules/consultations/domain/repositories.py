from typing import Protocol

from .entities import Consultation


class ConsultationsRepository(Protocol):
    async def find_open_draft(self, owner_id: str, patient_id: str) -> Consultation | None:
        ...

    async def create_draft(
        self,
        owner_id: str,
        *,
        patient_id: str,
        appointment_id: str | None,
    ) -> Consultation:
        ...

    async def get_for_owner(self, owner_id: str, consultation_id: str) -> Consultation | None:
        ...

    async def update_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        ...

    async def update_evaluation_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        ...

    async def update_requirement_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        ...

    async def update_distribution_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        ...

    async def update_menu_for_owner(
        self, owner_id: str, consultation_id: str, allocations: list[dict]
    ) -> Consultation | None:
        ...

    async def update_close_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        ...

    async def complete_for_owner(self, owner_id: str, consultation_id: str) -> Consultation | None:
        ...

    async def reopen_for_owner(self, owner_id: str, consultation_id: str) -> Consultation | None:
        ...
