from datetime import timezone

from bson import ObjectId
from google.auth.transport.requests import Request as GRequest
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.integrations.google_calendar import build_creds, calendar_service, event_payload

from ..domain.entities import Appointment


class GoogleCalendarGateway:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def create_event(self, owner_id: str, appointment: Appointment) -> str | None:
        svc = await self._calendar_service(owner_id)
        if svc is None:
            return None
        created_event = svc.events().insert(
            calendarId="primary",
            body=self._event_payload(appointment),
            conferenceDataVersion=1 if appointment.mode == "online" else 0,
        ).execute()
        return created_event.get("id")

    async def update_event(self, owner_id: str, appointment: Appointment) -> str | None:
        if not appointment.google_event_id:
            return None
        svc = await self._calendar_service(owner_id)
        if svc is None:
            return None
        svc.events().patch(
            calendarId="primary",
            eventId=appointment.google_event_id,
            body=self._event_payload(appointment),
            conferenceDataVersion=1 if appointment.mode == "online" else 0,
        ).execute()
        return appointment.google_event_id

    async def delete_event(self, owner_id: str, google_event_id: str) -> None:
        svc = await self._calendar_service(owner_id)
        if svc is None:
            return
        try:
            svc.events().delete(calendarId="primary", eventId=google_event_id).execute()
        except Exception:
            pass

    async def _calendar_service(self, owner_id: str):
        if not ObjectId.is_valid(owner_id):
            return None
        tokens = await self._db.google_tokens.find_one({"user_id": ObjectId(owner_id)})
        if tokens is None:
            return None

        creds = build_creds(tokens)
        if creds.expired and creds.refresh_token:
            creds.refresh(GRequest())
        return calendar_service(creds)

    def _event_payload(self, appointment: Appointment) -> dict:
        patient_name = appointment.patient.name if appointment.patient else None
        title = f"Cita - {patient_name or 'Paciente'}"
        start = appointment.start
        end = appointment.end or appointment.start
        return event_payload(
            summary=title,
            description=(appointment.note or "")[:1024],
            start=start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start,
            end=end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end,
            online=(appointment.mode == "online"),
        )
