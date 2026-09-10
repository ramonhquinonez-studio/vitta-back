from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

# `payment_mode`
NONE = "none"
DEPOSIT = "deposit"
FULL = "full"
PAYMENT_MODES = (NONE, DEPOSIT, FULL)

# `deposit_type`
PERCENTAGE = "percentage"
FIXED = "fixed"
DEPOSIT_TYPES = (PERCENTAGE, FIXED)

# `reschedule_limit` sentinel
UNLIMITED = -1


@dataclass(frozen=True)
class BookingPolicy:
    """Per-nutritionist booking-protection policy (spec 080). One document
    per `owner_id`; `DEFAULT_POLICY` is returned when none is saved."""

    owner_id: str
    payment_mode: str = NONE
    deposit_type: str = PERCENTAGE
    deposit_value: float = 30.0
    requires_approval: bool = False
    reschedule_limit: int = 1
    reschedule_notice_hours: int = 24
    cancellation_cutoff_hours: int = 24
    slot_hold_minutes: int = 15
    policy_text: str | None = None
    updated_at: datetime | None = None

    @property
    def needs_consent(self) -> bool:
        """Whether a patient must accept this policy before booking."""
        return self.payment_mode != NONE or self.requires_approval

    def with_owner(self, owner_id: str) -> "BookingPolicy":
        return replace(self, owner_id=owner_id)


def default_policy(owner_id: str) -> BookingPolicy:
    return BookingPolicy(owner_id=owner_id)
