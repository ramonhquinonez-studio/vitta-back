from dataclasses import dataclass, field


@dataclass(frozen=True)
class Patient:
    id: str
    owner_id: str
    name: str
    age: int | None = None
    sex: str | None = None
    height_cm: float | None = None
    allergies: list[str] = field(default_factory=list)
    notes: str | None = None
    # Set once this chart is linked to a real login-capable account (either
    # via a patient-scoped invite code, or historically via the unscoped
    # invite flow's own patient creation). None means it's chart-only — the
    # nutritionist created it directly and no one can log in as this patient
    # yet.
    user_id: str | None = None
