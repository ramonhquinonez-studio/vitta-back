from datetime import datetime, timedelta

from ..domain.entities import Appointment
from ..domain.repositories import AppointmentsCalendarGateway, AppointmentsRepository


class OverlapError(Exception):
    def __init__(self, conflict: Appointment):
        super().__init__("Ya existe una cita en ese horario.")
        self.conflict = conflict


class AppointmentsService:
    def __init__(
        self,
        repository: AppointmentsRepository,
        calendar_gateway: AppointmentsCalendarGateway,
    ):
        self._repository = repository
        self._calendar_gateway = calendar_gateway

    async def list_appointments(
        self,
        owner_id: str,
        *,
        status: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        query: str | None = None,
        patient_id: str | None = None,
    ) -> list[Appointment]:
        return await self._repository.list_for_owner(
            owner_id,
            status=status,
            from_dt=from_dt,
            to_dt=to_dt,
            query=query,
            patient_id=patient_id,
        )

    async def create_appointment(
        self,
        owner_id: str,
        *,
        patient_id: str,
        start: datetime,
        end: datetime | None,
        mode: str,
        status: str,
        note: str | None,
        plan_id: str | None,
        body_composition_id: str | None,
        no_sync: bool,
    ) -> Appointment:
        resolved_end = end or (start + timedelta(minutes=30))
        await self._ensure_patient_if_needed(owner_id, patient_id)
        await self._ensure_no_overlap(owner_id, start, resolved_end)

        appointment = await self._repository.create_for_owner(
            owner_id,
            patient_id=patient_id,
            start=start,
            end=resolved_end,
            mode=mode,
            status=status,
            note=note,
            plan_id=plan_id,
            body_composition_id=body_composition_id,
            no_sync=no_sync,
        )

        if no_sync:
            return appointment

        try:
            google_event_id = await self._calendar_gateway.create_event(owner_id, appointment)
            if google_event_id:
                updated = await self._repository.set_google_event_id(
                    appointment.id,
                    google_event_id,
                )
                if updated is not None:
                    return updated
        except Exception:
            pass

        return appointment

    async def get_appointment(self, owner_id: str, appointment_id: str) -> Appointment:
        appointment = await self._repository.get_for_owner(owner_id, appointment_id)
        if appointment is None:
            raise LookupError("Appointment not found")
        return appointment

    async def update_appointment(
        self,
        owner_id: str,
        appointment_id: str,
        *,
        patient_id: str | None,
        start: datetime | None,
        end: datetime | None,
        mode: str | None,
        status: str | None,
        note: str | None,
        plan_id: str | None,
        body_composition_id: str | None,
        no_sync: bool | None,
    ) -> Appointment:
        current = await self._repository.get_for_owner(owner_id, appointment_id)
        if current is None:
            raise LookupError("Appointment not found")

        updates: dict = {}
        if patient_id is not None:
            await self._ensure_patient_if_needed(owner_id, patient_id)
            updates["patient_id"] = patient_id
        if start is not None:
            updates["start"] = start
        if end is not None:
            updates["end"] = end
        if mode is not None:
            updates["mode"] = mode
        if status is not None:
            updates["status"] = status
        if note is not None:
            updates["note"] = note
        if plan_id is not None:
            updates["plan_id"] = plan_id
        if body_composition_id is not None:
            updates["body_composition_id"] = body_composition_id
        if no_sync is not None:
            updates["no_sync"] = no_sync

        if not updates:
            raise ValueError("No fields to update")

        new_start = updates.get("start", current.start)
        new_end = updates.get("end", current.end or (current.start + timedelta(minutes=30)))
        await self._ensure_no_overlap(
            owner_id,
            new_start,
            new_end,
            exclude_appointment_id=appointment_id,
        )

        updated = await self._repository.update_for_owner(owner_id, appointment_id, updates)
        if updated is None:
            raise LookupError("Appointment not found")

        if updated.no_sync:
            return updated

        try:
            if updated.google_event_id:
                await self._calendar_gateway.update_event(owner_id, updated)
                return updated

            google_event_id = await self._calendar_gateway.create_event(owner_id, updated)
            if google_event_id:
                curr = await self._repository.set_google_event_id(updated.id, google_event_id)
                if curr is not None:
                    return curr
        except Exception:
            pass

        return updated

    async def delete_appointment(self, owner_id: str, appointment_id: str) -> None:
        current = await self._repository.get_for_owner(owner_id, appointment_id)
        if current is None:
            raise LookupError("Appointment not found")

        try:
            if current.google_event_id:
                await self._calendar_gateway.delete_event(owner_id, current.google_event_id)
        except Exception:
            pass

        deleted = await self._repository.delete_for_owner(owner_id, appointment_id)
        if deleted is None:
            raise LookupError("Appointment not found")

    async def _ensure_patient_if_needed(self, owner_id: str, patient_id: str) -> None:
        if patient_id and await self._repository.patient_exists_for_owner(owner_id, patient_id) is False:
            raise LookupError("Patient not found")

    async def _ensure_no_overlap(
        self,
        owner_id: str,
        start: datetime,
        end: datetime,
        exclude_appointment_id: str | None = None,
    ) -> None:
        overlap = await self._repository.find_overlap(
            owner_id,
            start=start,
            end=end,
            exclude_appointment_id=exclude_appointment_id,
        )
        if overlap is not None:
            raise OverlapError(overlap)

    def conflict_detail(self, error: OverlapError) -> dict:
        return {
            "code": "OVERLAP",
            "message": str(error),
            "conflict_id": error.conflict.id,
            "conflict_start": error.conflict.start,
            "conflict_end": error.conflict.end,
        }
