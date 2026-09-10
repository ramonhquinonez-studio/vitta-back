from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SavedCard:
    id: str  # Stripe PaymentMethod id (pm_...)
    brand: str | None
    last4: str | None
    exp_month: int | None
    exp_year: int | None
    is_default: bool = False
