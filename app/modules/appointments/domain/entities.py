from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AppointmentPatient:
    id: str | None = None
    name: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class Appointment:
    id: str
    owner_id: str
    patient_id: str | None
    start: datetime
    end: datetime | None
    mode: str
    status: str
    note: str | None = None
    plan_id: str | None = None
    no_sync: bool = False
    google_event_id: str | None = None
    patient: AppointmentPatient | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
