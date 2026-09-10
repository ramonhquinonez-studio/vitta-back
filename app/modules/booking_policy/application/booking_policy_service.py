from __future__ import annotations

from datetime import datetime
from typing import Any

from ..domain.entities import (
    DEPOSIT,
    DEPOSIT_TYPES,
    FIXED,
    FULL,
    NONE,
    PAYMENT_MODES,
    PERCENTAGE,
    UNLIMITED,
    BookingPolicy,
    default_policy,
)
from ..domain.repositories import BookingPolicyRepository


class BookingPolicyService:
    """Reads/writes a nutritionist's `BookingPolicy` and resolves it into the
    patient-facing shape (amount due + a Spanish disclosure summary). Pure of
    Stripe — Phase 1 moves no money."""

    def __init__(self, repository: BookingPolicyRepository):
        self._repo = repository

    async def get_for_owner(self, owner_id: str) -> BookingPolicy:
        return await self._repo.get_for_owner(owner_id) or default_policy(owner_id)

    async def upsert_for_owner(self, owner_id: str, payload: dict[str, Any]) -> BookingPolicy:
        current = await self.get_for_owner(owner_id)
        merged = _merge(current, payload)
        _validate(merged)
        merged = BookingPolicy(**{**merged.__dict__, "updated_at": datetime.utcnow()})
        return await self._repo.upsert_for_owner(merged)

    def resolve_for_patient(
        self,
        policy: BookingPolicy,
        *,
        session_price: float | None,
        currency: str,
    ) -> dict[str, Any]:
        amount_due_cents = _amount_due_cents(policy, session_price)
        resolved = {
            "payment_mode": policy.payment_mode,
            "deposit_type": policy.deposit_type,
            "deposit_value": policy.deposit_value,
            "requires_approval": policy.requires_approval,
            "reschedule_limit": policy.reschedule_limit,
            "reschedule_notice_hours": policy.reschedule_notice_hours,
            "cancellation_cutoff_hours": policy.cancellation_cutoff_hours,
            "slot_hold_minutes": policy.slot_hold_minutes,
            "amount_due_cents": amount_due_cents,
            "currency": currency,
            "needs_consent": policy.needs_consent,
        }
        resolved["policy_text"] = policy.policy_text or _auto_policy_text(resolved)
        return resolved

    async def resolve_for_owner(
        self, owner_id: str, *, session_price: float | None, currency: str
    ) -> dict[str, Any]:
        policy = await self.get_for_owner(owner_id)
        return self.resolve_for_patient(policy, session_price=session_price, currency=currency)


def _merge(current: BookingPolicy, payload: dict[str, Any]) -> BookingPolicy:
    fields = {
        "payment_mode",
        "deposit_type",
        "deposit_value",
        "requires_approval",
        "reschedule_limit",
        "reschedule_notice_hours",
        "cancellation_cutoff_hours",
        "slot_hold_minutes",
        "policy_text",
    }
    updates = {k: payload[k] for k in fields if k in payload}
    return BookingPolicy(**{**current.__dict__, **updates})


def _validate(p: BookingPolicy) -> None:
    if p.payment_mode not in PAYMENT_MODES:
        raise ValueError(f"payment_mode must be one of {PAYMENT_MODES}")
    if p.deposit_type not in DEPOSIT_TYPES:
        raise ValueError(f"deposit_type must be one of {DEPOSIT_TYPES}")
    if p.deposit_type == PERCENTAGE and not (0 <= p.deposit_value <= 100):
        raise ValueError("deposit_value (percentage) must be between 0 and 100")
    if p.deposit_type == FIXED and p.deposit_value <= 0:
        raise ValueError("deposit_value (fixed) must be greater than 0")
    if p.reschedule_limit < UNLIMITED:
        raise ValueError("reschedule_limit must be >= -1")
    for name in ("reschedule_notice_hours", "cancellation_cutoff_hours"):
        if getattr(p, name) < 0:
            raise ValueError(f"{name} must be >= 0")
    if not (5 <= p.slot_hold_minutes <= 120):
        raise ValueError("slot_hold_minutes must be between 5 and 120")


def _amount_due_cents(policy: BookingPolicy, session_price: float | None) -> int:
    if policy.payment_mode == NONE or not session_price or session_price <= 0:
        return 0
    if policy.payment_mode == FULL:
        return round(session_price * 100)
    # deposit
    if policy.deposit_type == FIXED:
        return round(min(policy.deposit_value, session_price) * 100)
    return round(session_price * policy.deposit_value / 100 * 100)


def _money(cents: int, currency: str) -> str:
    return f"{cents / 100:.2f} {currency}"


def _auto_policy_text(resolved: dict[str, Any]) -> str:
    parts: list[str] = []
    mode = resolved["payment_mode"]
    amount = resolved["amount_due_cents"]
    currency = resolved["currency"]

    if mode == FULL and amount:
        parts.append(f"Se cobra el total de la consulta ({_money(amount, currency)}) al reservar.")
    elif mode == DEPOSIT and amount:
        parts.append(f"Se cobra un depósito de {_money(amount, currency)} al reservar.")
    elif mode == DEPOSIT:
        parts.append("Se cobra un depósito al reservar.")
    else:
        parts.append("La reserva no requiere pago por adelantado.")

    if resolved["requires_approval"]:
        parts.append("La cita queda pendiente hasta que el nutriólogo la confirme.")

    limit = resolved["reschedule_limit"]
    notice = resolved["reschedule_notice_hours"]
    if limit == UNLIMITED:
        parts.append(f"Puedes reprogramar con al menos {notice} h de anticipación.")
    elif limit == 0:
        parts.append("No se permite reprogramar; solo cancelar.")
    elif limit == 1:
        parts.append(f"Puedes reprogramar una vez, con al menos {notice} h de anticipación.")
    else:
        parts.append(
            f"Puedes reprogramar hasta {limit} veces, con al menos {notice} h de anticipación."
        )

    cutoff = resolved["cancellation_cutoff_hours"]
    if mode == NONE:
        parts.append(f"Cancela con al menos {cutoff} h de anticipación.")
    else:
        parts.append(
            f"Si cancelas con al menos {cutoff} h de anticipación, se reembolsa el 100%. "
            f"Si cancelas después o no asistes, se pierde el pago."
        )
    return " ".join(parts)
