"""Pure cancellation / reschedule / no-show rules (spec 080 Phase 3).

Every function here takes the appointment's immutable `policy_snapshot` (the
resolved policy captured at booking, spec 080 Phase 1) plus timestamps, and
returns a plain dict describing the outcome. No I/O, no Stripe — the caller
applies the status change and, when `refund_cents > 0`, the refund.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ..domain.entities import NONE, UNLIMITED

# who initiated the action
BY_PATIENT = "patient"
BY_NUTRITIONIST = "nutritionist"

# cancellation outcomes
REFUND = "refund"  # money is returned (100%)
FORFEIT = "forfeit"  # money is kept
NO_CHARGE = "no_charge"  # nothing was paid


def _amount_paid_cents(snapshot: dict[str, Any] | None) -> int:
    if not snapshot:
        return 0
    # Phase 2 stamps `amount_paid_cents`; before that fall back to the
    # resolved `amount_due_cents` so the preview is still meaningful.
    return int(
        snapshot.get("amount_paid_cents")
        or snapshot.get("amount_due_cents")
        or 0
    )


def evaluate_cancellation(
    snapshot: dict[str, Any] | None,
    *,
    start: datetime,
    now: datetime,
    by: str,
    is_no_show: bool = False,
) -> dict[str, Any]:
    """Outcome of cancelling (or marking no-show) an appointment.

    Returns `{outcome, refund_cents, status, reason}`.
    """
    paid = _amount_paid_cents(snapshot)
    cutoff_hours = int((snapshot or {}).get("cancellation_cutoff_hours") or 0)
    cutoff_at = start - timedelta(hours=cutoff_hours)

    if is_no_show:
        return {
            "outcome": NO_CHARGE if paid == 0 else FORFEIT,
            "refund_cents": 0,
            "status": "no_show",
            "reason": "El paciente no asistió a la cita.",
        }

    if by == BY_NUTRITIONIST:
        # The nutritionist cancelling always returns the money in full.
        return {
            "outcome": NO_CHARGE if paid == 0 else REFUND,
            "refund_cents": paid,
            "status": "canceled",
            "reason": "El nutriólogo canceló la cita; se reembolsa el 100%.",
        }

    if paid == 0:
        return {
            "outcome": NO_CHARGE,
            "refund_cents": 0,
            "status": "canceled",
            "reason": "La cita no requería pago.",
        }

    if now <= cutoff_at:
        return {
            "outcome": REFUND,
            "refund_cents": paid,
            "status": "canceled",
            "reason": (
                f"Cancelación con más de {cutoff_hours} h de anticipación; "
                "se reembolsa el 100%."
            ),
        }

    return {
        "outcome": FORFEIT,
        "refund_cents": 0,
        "status": "canceled",
        "reason": (
            f"Cancelación con menos de {cutoff_hours} h de anticipación; "
            "se pierde el pago."
        ),
    }


def evaluate_reschedule(
    snapshot: dict[str, Any] | None,
    *,
    start: datetime,
    now: datetime,
    reschedule_count: int,
    by: str,
) -> dict[str, Any]:
    """Whether a reschedule is allowed. Returns `{allowed, reason}`."""
    if by == BY_NUTRITIONIST:
        return {"allowed": True, "reason": ""}

    snap = snapshot or {}
    limit = int(snap.get("reschedule_limit", 1))
    notice_hours = int(snap.get("reschedule_notice_hours") or 0)

    if limit == 0:
        return {
            "allowed": False,
            "reason": "Esta cita no permite reprogramación; solo cancelación.",
        }
    if limit != UNLIMITED and reschedule_count >= limit:
        return {
            "allowed": False,
            "reason": (
                "Ya alcanzaste el número de reprogramaciones permitidas "
                f"({limit})."
            ),
        }
    if now > start - timedelta(hours=notice_hours):
        return {
            "allowed": False,
            "reason": (
                f"Debes reprogramar con al menos {notice_hours} h de "
                "anticipación."
            ),
        }
    return {"allowed": True, "reason": ""}


def snapshot_needs_payment(snapshot: dict[str, Any] | None) -> bool:
    snap = snapshot or {}
    return snap.get("payment_mode", NONE) != NONE and int(
        snap.get("amount_due_cents") or 0
    ) > 0
