from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class ConsultationStartIn(BaseModel):
    patient_id: str = Field(validation_alias="patientId")
    appointment_id: str | None = Field(default=None, validation_alias="appointmentId")
    model_config = ConfigDict(populate_by_name=True)


class ConsultationUpdateIn(BaseModel):
    visit_type: Literal["first_time", "follow_up"] | None = Field(
        default=None, validation_alias="visitType"
    )
    current_step: int | None = Field(default=None, validation_alias="currentStep")
    model_config = ConfigDict(populate_by_name=True)


class ConsultationEvaluationIn(BaseModel):
    weight_kg: float | None = Field(default=None, validation_alias="weightKg")
    height_cm: float | None = Field(default=None, validation_alias="heightCm")
    body_fat_pct: float | None = Field(default=None, validation_alias="bodyFatPct")
    waist_cm: float | None = Field(default=None, validation_alias="waistCm")
    hip_cm: float | None = Field(default=None, validation_alias="hipCm")
    arm_cm: float | None = Field(default=None, validation_alias="armCm")
    notes: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class ConsultationRequirementIn(BaseModel):
    wrist_cm: float | None = Field(default=None, validation_alias="wristCm")
    activity_factor: float | None = Field(default=None, validation_alias="activityFactor")
    calorie_adjustment: float | None = Field(default=None, validation_alias="calorieAdjustment")
    model_config = ConfigDict(populate_by_name=True)


class ConsultationDistributionIn(BaseModel):
    target_kcal: float | None = Field(default=None, validation_alias="targetKcal")
    carbs_pct: float | None = Field(default=None, validation_alias="carbsPct")
    protein_pct: float | None = Field(default=None, validation_alias="proteinPct")
    fat_pct: float | None = Field(default=None, validation_alias="fatPct")
    model_config = ConfigDict(populate_by_name=True)


class MenuAllocationItemIn(BaseModel):
    group_id: str = Field(validation_alias="groupId")
    units: float
    model_config = ConfigDict(populate_by_name=True)


class ConsultationMenuIn(BaseModel):
    allocations: List[MenuAllocationItemIn] = Field(default_factory=list)
    model_config = ConfigDict(populate_by_name=True)


class ConsultationCloseIn(BaseModel):
    private_notes: str | None = Field(default=None, validation_alias="privateNotes")
    next_appointment_id: str | None = Field(default=None, validation_alias="nextAppointmentId")
    model_config = ConfigDict(populate_by_name=True)


class EvaluationSnapshotOut(BaseModel):
    weight_kg: float | None = None
    height_cm: float | None = None
    body_fat_pct: float | None = None
    waist_cm: float | None = None
    hip_cm: float | None = None
    arm_cm: float | None = None
    notes: str | None = None


class RequirementInputOut(BaseModel):
    wrist_cm: float | None = None
    activity_factor: float | None = None
    calorie_adjustment: float | None = None


class DistributionInputOut(BaseModel):
    target_kcal: float | None = None
    carbs_pct: float | None = None
    protein_pct: float | None = None
    fat_pct: float | None = None


class MenuAllocationItemOut(BaseModel):
    group_id: str
    units: float


class ConsultationOut(BaseModel):
    id: str
    patient_id: str
    appointment_id: str | None = None
    status: str
    current_step: int
    visit_type: str | None = None
    evaluation: EvaluationSnapshotOut | None = None
    requirement: RequirementInputOut | None = None
    distribution: DistributionInputOut | None = None
    menu_allocations: List[MenuAllocationItemOut] | None = None
    private_notes: str | None = None
    next_appointment_id: str | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
