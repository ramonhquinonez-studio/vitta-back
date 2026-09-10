"""Webhook handlers for consultation payments + Connect account state,
registered with the shared dispatcher (spec 077). `apply_*` are pure
(repo in) for unit testing; `handle_*` wrappers resolve the repo from the
request-scoped Mongo connection.
"""

from __future__ import annotations

from ..domain.payment_entities import ConnectAccount


async def apply_payment_intent_succeeded(repo, pi: dict) -> None:
    payment = await repo.get_payment_by_intent(pi.get("id"))
    if payment is None or payment.status == "refunded":
        return
    await repo.update_payment(payment.id, {"status": "paid"})


async def apply_payment_intent_failed(repo, pi: dict) -> None:
    payment = await repo.get_payment_by_intent(pi.get("id"))
    if payment is None or payment.status in ("paid", "refunded"):
        return
    await repo.update_payment(payment.id, {"status": "failed"})


async def apply_charge_refunded(repo, charge: dict) -> None:
    payment = await repo.get_payment_by_intent(charge.get("payment_intent"))
    if payment is None:
        return
    refunded = int(charge.get("amount_refunded") or 0)  # cumulative — assign, don't add
    amount = int(charge.get("amount") or payment.amount_cents)
    full = amount > 0 and refunded >= amount
    await repo.update_payment(
        payment.id,
        {"refunded_cents": refunded, "status": "refunded" if full else payment.status},
    )


async def apply_account_updated(repo, account: dict) -> None:
    existing = await repo.get_connect_account_by_id(account.get("id"))
    if existing is None:
        return
    requirements = account.get("requirements") or {}
    await repo.upsert_connect_account(
        ConnectAccount(
            owner_id=existing.owner_id,
            account_id=existing.account_id,
            charges_enabled=bool(account.get("charges_enabled")),
            payouts_enabled=bool(account.get("payouts_enabled")),
            requirements_due=list(requirements.get("currently_due") or []),
            disabled_reason=requirements.get("disabled_reason"),
        )
    )


# --- dispatcher wiring -------------------------------------------------

def _repo():
    from app.db.mongo import get_db
    from ..infrastructure.mongo_payments_repository import MongoPaymentsRepository

    return MongoPaymentsRepository(get_db())


async def handle_payment_intent_succeeded(pi: dict) -> None:
    await apply_payment_intent_succeeded(_repo(), pi)


async def handle_payment_intent_failed(pi: dict) -> None:
    await apply_payment_intent_failed(_repo(), pi)


async def handle_charge_refunded(charge: dict) -> None:
    await apply_charge_refunded(_repo(), charge)


async def handle_account_updated(account: dict) -> None:
    await apply_account_updated(_repo(), account)


def register() -> None:
    from app.modules.stripe_webhooks.application.webhook_dispatcher import register_handler

    register_handler("payment_intent.succeeded", handle_payment_intent_succeeded)
    register_handler("payment_intent.payment_failed", handle_payment_intent_failed)
    register_handler("charge.refunded", handle_charge_refunded)
    register_handler("account.updated", handle_account_updated)
