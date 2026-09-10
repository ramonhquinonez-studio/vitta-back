"""Stripe webhook handlers for the subscription lifecycle, registered with
the shared dispatcher (`stripe_webhooks`, spec 077). The dispatcher already
handles signature verification + idempotency; these just apply the state
change to the `subscriptions` collection.

The `apply_*` functions are pure (repo in, no I/O of their own) so they're
unit-testable; the registered `handle_*` wrappers just resolve the repo
from the request-scoped Mongo connection.

`handle_webhook` on `BillingService` (the redirect-era one) is left as-is
for the legacy `BILLING_PROVIDER=stripe` provider; this is the native path.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..domain.entities import Subscription

_ENTITLED = {"active", "trialing"}


def _period_end(ts) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        return None


async def _resolve_plan_id(repo, price_id: str | None) -> str | None:
    if not price_id:
        return None
    for plan in await repo.list_plans():
        if plan.stripe_price_id == price_id:
            return plan.id
    return None


async def _set_status(repo, customer_id: str | None, status: str) -> None:
    if not customer_id:
        return
    current = await repo.get_subscription_for_customer(customer_id)
    if current is None:
        return
    await repo.upsert_subscription(
        Subscription(
            owner_id=current.owner_id,
            plan_id=current.plan_id,
            status="active" if status in _ENTITLED else status,
            provider_customer_id=current.provider_customer_id,
            provider_subscription_id=current.provider_subscription_id,
            current_period_end=current.current_period_end,
        )
    )


# --- pure appliers -------------------------------------------------------

async def apply_invoice_paid(repo, invoice: dict) -> None:
    await _set_status(repo, invoice.get("customer"), "active")


async def apply_invoice_payment_failed(repo, invoice: dict) -> None:
    await _set_status(repo, invoice.get("customer"), "past_due")


async def apply_subscription_deleted(repo, sub: dict) -> None:
    await _set_status(repo, sub.get("customer"), "canceled")


async def apply_subscription_updated(repo, sub: dict) -> None:
    customer_id = sub.get("customer")
    if not customer_id:
        return
    current = await repo.get_subscription_for_customer(customer_id)
    if current is None:
        return

    status = (sub.get("status") or current.status).lower()
    items = ((sub.get("items") or {}).get("data")) or [{}]
    price_id = ((items[0].get("price") or {}).get("id"))
    plan_id = await _resolve_plan_id(repo, price_id) or current.plan_id
    period_end = _period_end(
        sub.get("current_period_end") or items[0].get("current_period_end")
    ) or current.current_period_end

    await repo.upsert_subscription(
        Subscription(
            owner_id=current.owner_id,
            plan_id=plan_id,
            status="active" if status in _ENTITLED else status,
            provider_customer_id=current.provider_customer_id,
            provider_subscription_id=sub.get("id") or current.provider_subscription_id,
            current_period_end=period_end,
        )
    )


# --- dispatcher wiring --------------------------------------------------

def _repo():
    from app.db.mongo import get_db
    from ..infrastructure.mongo_billing_repository import MongoBillingRepository

    return MongoBillingRepository(get_db())


async def handle_invoice_paid(invoice: dict) -> None:
    await apply_invoice_paid(_repo(), invoice)


async def handle_invoice_payment_failed(invoice: dict) -> None:
    await apply_invoice_payment_failed(_repo(), invoice)


async def handle_subscription_updated(sub: dict) -> None:
    await apply_subscription_updated(_repo(), sub)


async def handle_subscription_deleted(sub: dict) -> None:
    await apply_subscription_deleted(_repo(), sub)


def register() -> None:
    from app.modules.stripe_webhooks.application.webhook_dispatcher import register_handler

    register_handler("invoice.paid", handle_invoice_paid)
    register_handler("invoice.payment_failed", handle_invoice_payment_failed)
    register_handler("customer.subscription.updated", handle_subscription_updated)
    register_handler("customer.subscription.deleted", handle_subscription_deleted)
