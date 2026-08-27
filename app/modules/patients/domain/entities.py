from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Patient:
    id: str
    name: str
    # None means self-registered with no nutritionist yet (see
    # `030-back-patient-self-registration`) — the patient shares their own
    # connection code for a nutritionist to claim them later.
    owner_id: str | None = None
    age: int | None = None
    sex: str | None = None
    height_cm: float | None = None
    allergies: list[str] = field(default_factory=list)
    notes: str | None = None
    # Free-text, coach-defined labels for grouping/filtering the roster
    # (e.g. "VIP", "Pérdida de peso") — no separate tag entity/collection.
    tags: list[str] = field(default_factory=list)
    # Set once this chart is linked to a real login-capable account (either
    # via a patient-scoped invite code, or historically via the unscoped
    # invite flow's own patient creation). None means it's chart-only — the
    # nutritionist created it directly and no one can log in as this patient
    # yet.
    user_id: str | None = None
    # None for patients created before `048-back-practice-dashboard` — not
    # backfilled, so "new this month" undercounts pre-existing charts.
    created_at: datetime | None = None
    daily_kcal_goal: float | None = None
    daily_protein_g_goal: float | None = None
    daily_carbs_g_goal: float | None = None
    daily_fat_g_goal: float | None = None
    email: str | None = None
    phone: str | None = None
    # Set when the nutritionist archives this chart instead of deleting it —
    # excluded from the default roster/dashboard but still fetchable by id.
    archived_at: datetime | None = None
