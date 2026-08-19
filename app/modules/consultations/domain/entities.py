from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EvaluationSnapshot:
    weight_kg: float | None = None
    height_cm: float | None = None
    body_fat_pct: float | None = None
    waist_cm: float | None = None
    hip_cm: float | None = None
    arm_cm: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class Consultation:
    id: str
    owner_id: str
    patient_id: str
    appointment_id: str | None
    status: str  # "draft" | "completed"
    current_step: int
    visit_type: str | None = None  # "first_time" | "follow_up"
    evaluation: EvaluationSnapshot | None = None
    private_notes: str | None = None
    next_appointment_id: str | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
