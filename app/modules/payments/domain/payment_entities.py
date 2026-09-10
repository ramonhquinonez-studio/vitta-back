from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Payment:
    id: str
    kind: str  # "consultation"
    consultation_id: str | None
    appointment_id: str | None
    patient_id: str
    nutritionist_id: str
    amount_cents: int
    fee_cents: int
    currency: str
    status: str  # "pending" | "paid" | "failed" | "refunded"
    payment_intent_id: str
    refunded_cents: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ConnectAccount:
    owner_id: str
    account_id: str
    charges_enabled: bool = False
    payouts_enabled: bool = False
    requirements_due: list[str] | None = None
    disabled_reason: str | None = None
