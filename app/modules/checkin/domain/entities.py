from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class FormField:
    id: str
    type: str  # "text" | "number" | "single_choice" | "multi_choice" | "scale"
    label: str
    required: bool = False
    options: list[str] = field(default_factory=list)  # single_choice/multi_choice
    scale_min: int | None = None
    scale_max: int | None = None


@dataclass(frozen=True)
class FormTemplate:
    id: str
    owner_id: str
    title: str
    description: str | None
    fields: list[FormField]
    archived: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FormAnswer:
    field_id: str
    values: list[str]


@dataclass(frozen=True)
class FormResponse:
    id: str
    owner_id: str
    patient_id: str
    template_id: str
    appointment_id: str | None
    answers: list[FormAnswer]
    submitted_at: datetime
