from datetime import datetime
from typing import Protocol

from .entities import Appointment


class AppointmentsRepository(Protocol):
    async def list_for_owner(
        self,
        owner_id: str,
        *,
        status: str | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
        query: str | None,
    ) -> list[Appointment]:
        ...

    async def get_for_owner(self, owner_id: str, appointment_id: str) -> Appointment | None:
        ...

    async def create_for_owner(
        self,
        owner_id: str,
        *,
        patient_id: str,
        start: datetime,
        end: datetime,
        mode: str,
        status: str,
        note: str | None,
        plan_id: str | None,
        no_sync: bool,
    ) -> Appointment:
        ...

    async def update_for_owner(
        self,
        owner_id: str,
        appointment_id: str,
        updates: dict,
    ) -> Appointment | None:
        ...

    async def delete_for_owner(self, owner_id: str, appointment_id: str) -> Appointment | None:
        ...

    async def find_overlap(
        self,
        owner_id: str,
        *,
        start: datetime,
        end: datetime,
        exclude_appointment_id: str | None = None,
    ) -> Appointment | None:
        ...

    async def patient_exists_for_owner(self, owner_id: str, patient_id: str) -> bool:
        ...

    async def set_google_event_id(self, appointment_id: str, google_event_id: str) -> Appointment | None:
        ...


class AppointmentsCalendarGateway(Protocol):
    async def create_event(self, owner_id: str, appointment: Appointment) -> str | None:
        ...

    async def update_event(self, owner_id: str, appointment: Appointment) -> str | None:
        ...

    async def delete_event(self, owner_id: str, google_event_id: str) -> None:
        ...
