import json
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from app.modules.appointments.application.appointments_service import (
    AppointmentsService,
    OverlapError,
)
from app.modules.appointments.domain.entities import Appointment, AppointmentPatient


class _FakeAppointmentsRepository:
    def __init__(self):
        self.appointments: dict[str, Appointment] = {}
        self.next_id = 1
        self.patient_exists = True

    async def list_for_owner(self, owner_id, *, status, from_dt, to_dt, query, patient_id=None):
        return [
            a
            for a in self.appointments.values()
            if a.owner_id == owner_id and (patient_id is None or a.patient_id == patient_id)
        ]

    async def get_for_owner(self, owner_id, appointment_id):
        appointment = self.appointments.get(appointment_id)
        if appointment and appointment.owner_id == owner_id:
            return appointment
        return None

    async def create_for_owner(
        self,
        owner_id,
        *,
        patient_id,
        start,
        end,
        mode,
        status,
        note,
        plan_id,
        body_composition_id,
        no_sync,
    ):
        appointment = Appointment(
            id=str(self.next_id),
            owner_id=owner_id,
            patient_id=patient_id,
            start=start,
            end=end,
            mode=mode,
            status=status,
            note=note,
            plan_id=plan_id,
            body_composition_id=body_composition_id,
            no_sync=no_sync,
            patient=AppointmentPatient(id=patient_id, name="Maria"),
        )
        self.appointments[appointment.id] = appointment
        self.next_id += 1
        return appointment

    async def update_for_owner(self, owner_id, appointment_id, updates):
        current = await self.get_for_owner(owner_id, appointment_id)
        if current is None:
            return None
        updated = replace(
            current,
            patient_id=updates.get("patient_id", current.patient_id),
            start=updates.get("start", current.start),
            end=updates.get("end", current.end),
            mode=updates.get("mode", current.mode),
            status=updates.get("status", current.status),
            note=updates.get("note", current.note),
            plan_id=updates.get("plan_id", current.plan_id),
            body_composition_id=updates.get(
                "body_composition_id", current.body_composition_id
            ),
            no_sync=updates.get("no_sync", current.no_sync),
        )
        self.appointments[appointment_id] = updated
        return updated

    async def delete_for_owner(self, owner_id, appointment_id):
        current = await self.get_for_owner(owner_id, appointment_id)
        if current is None:
            return None
        del self.appointments[appointment_id]
        return current

    async def find_overlap(self, owner_id, *, start, end, exclude_appointment_id=None):
        for appointment in self.appointments.values():
            if appointment.owner_id != owner_id:
                continue
            if exclude_appointment_id and appointment.id == exclude_appointment_id:
                continue
            appointment_end = appointment.end or appointment.start
            if appointment.start < end and appointment_end > start:
                return appointment
        return None

    async def patient_exists_for_owner(self, owner_id, patient_id):
        return self.patient_exists

    async def set_google_event_id(self, appointment_id, google_event_id):
        current = self.appointments.get(appointment_id)
        if current is None:
            return None
        updated = replace(current, google_event_id=google_event_id)
        self.appointments[appointment_id] = updated
        return updated


class _FakeCalendarGateway:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []

    async def create_event(self, owner_id, appointment):
        self.created.append((owner_id, appointment.id))
        return f"google-{appointment.id}"

    async def update_event(self, owner_id, appointment):
        self.updated.append((owner_id, appointment.id))
        return appointment.google_event_id

    async def delete_event(self, owner_id, google_event_id):
        self.deleted.append((owner_id, google_event_id))


class AppointmentsServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_appointment_rejects_overlap(self):
        repository = _FakeAppointmentsRepository()
        calendar = _FakeCalendarGateway()
        service = AppointmentsService(repository, calendar)

        start = datetime.now(UTC)
        await repository.create_for_owner(
            "owner-1",
            patient_id="patient-1",
            start=start,
            end=start + timedelta(minutes=30),
            mode="online",
            status="pending",
            note=None,
            plan_id=None,
            body_composition_id=None,
            no_sync=False,
        )

        with self.assertRaises(OverlapError):
            await service.create_appointment(
                "owner-1",
                patient_id="patient-2",
                start=start + timedelta(minutes=10),
                end=start + timedelta(minutes=40),
                mode="online",
                status="pending",
                note=None,
                plan_id=None,
                body_composition_id=None,
                no_sync=False,
            )

    async def test_conflict_detail_is_json_serializable(self):
        # Regression test: HTTPException's `detail` is rendered by
        # Starlette's plain json.dumps, not FastAPI's Pydantic machinery, so
        # conflict_detail() must never return raw datetime objects — doing
        # so previously turned a 409 overlap response into a 500 (confirmed
        # live: PATCH-ing an appointment onto an occupied slot 500'd with
        # "Object of type datetime is not JSON serializable").
        repository = _FakeAppointmentsRepository()
        calendar = _FakeCalendarGateway()
        service = AppointmentsService(repository, calendar)

        start = datetime.now(UTC)
        await repository.create_for_owner(
            "owner-1",
            patient_id="patient-1",
            start=start,
            end=start + timedelta(minutes=30),
            mode="online",
            status="pending",
            note=None,
            plan_id=None,
            body_composition_id=None,
            no_sync=False,
        )

        try:
            await service.create_appointment(
                "owner-1",
                patient_id="patient-2",
                start=start + timedelta(minutes=10),
                end=start + timedelta(minutes=40),
                mode="online",
                status="pending",
                note=None,
                plan_id=None,
                body_composition_id=None,
                no_sync=False,
            )
            self.fail("Expected OverlapError")
        except OverlapError as exc:
            detail = service.conflict_detail(exc)
            json.dumps(detail)  # raises TypeError if any value isn't serializable
            self.assertIsInstance(detail["conflict_start"], str)

    async def test_create_appointment_sets_google_event_id_when_sync_enabled(self):
        repository = _FakeAppointmentsRepository()
        calendar = _FakeCalendarGateway()
        service = AppointmentsService(repository, calendar)

        start = datetime.now(UTC)
        appointment = await service.create_appointment(
            "owner-1",
            patient_id="patient-1",
            start=start,
            end=None,
            mode="online",
            status="pending",
            note="Consulta inicial",
            plan_id=None,
            body_composition_id=None,
            no_sync=False,
        )

        self.assertEqual(appointment.google_event_id, "google-1")
        self.assertEqual(calendar.created, [("owner-1", "1")])

    async def test_list_appointments_filters_by_patient_id(self):
        repository = _FakeAppointmentsRepository()
        calendar = _FakeCalendarGateway()
        service = AppointmentsService(repository, calendar)
        start = datetime.now(UTC)

        await repository.create_for_owner(
            "owner-1",
            patient_id="patient-1",
            start=start,
            end=start + timedelta(minutes=30),
            mode="online",
            status="confirmed",
            note=None,
            plan_id=None,
            body_composition_id=None,
            no_sync=False,
        )
        await repository.create_for_owner(
            "owner-1",
            patient_id="patient-2",
            start=start + timedelta(hours=1),
            end=start + timedelta(hours=1, minutes=30),
            mode="online",
            status="confirmed",
            note=None,
            plan_id=None,
            body_composition_id=None,
            no_sync=False,
        )

        result = await service.list_appointments("owner-1", patient_id="patient-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].patient_id, "patient-1")
