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
class RequirementInput:
    wrist_cm: float | None = None
    activity_factor: float | None = None
    calorie_adjustment: float | None = None


@dataclass(frozen=True)
class DistributionInput:
    target_kcal: float | None = None
    carbs_pct: float | None = None
    protein_pct: float | None = None
    fat_pct: float | None = None


@dataclass(frozen=True)
class MenuAllocationItem:
    group_id: str
    units: float


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
    requirement: RequirementInput | None = None
    distribution: DistributionInput | None = None
    menu_allocations: list[MenuAllocationItem] | None = None
    private_notes: str | None = None
    next_appointment_id: str | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
