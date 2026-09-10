"""Recurring-subscription payment collected via the native card sheet
(nutri_pro `109`). Extends `billing` with `fidelity_back`'s
`init_payment_sheet` shape: create the Stripe Subscription `incomplete`,
hand the client the first invoice's PaymentIntent client secret, let the
SDK confirm it, then reconcile via `verify` / webhook.

Deliberately a *separate* service from `BillingService` (which the redirect
path and every existing test construct) so its constructor can take the
`stripe` SDK + the `StripeCustomers` helper without disturbing them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.modules.payments.application.errors import stripe_error_to_http
from app.modules.payments.application.stripe_customers import StripeCustomers
from app.modules.payments.infrastructure.stripe_client import as_dict

from ..domain.entities import Subscription
from ..domain.repositories import BillingRepository

_ENTITLED = {"active", "trialing"}


def _period_end(sub: Any) -> datetime | None:
    ts = sub.get("current_period_end")
    if not ts:
        # Newer API versions moved it onto the subscription item.
        items = ((sub.get("items") or {}).get("data")) or []
        if items:
            ts = items[0].get("current_period_end")
    if not ts:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


class StripeSubscriptionsService:
    def __init__(self, repository: BillingRepository, stripe: Any, customers: StripeCustomers):
        self._repo = repository
        self._stripe = stripe
        self._customers = customers

    async def start_subscription_sheet(
        self, owner_id: str, owner_email: str | None, plan_id: str
    ) -> dict:
        plan = await self._repo.get_plan(plan_id)
        if plan is None:
            raise LookupError("Plan not found")

        # Free / default plan → no Stripe call, just enroll.
        if plan.is_default or not plan.stripe_price_id:
            await self._repo.upsert_subscription(
                Subscription(owner_id=owner_id, plan_id=plan.id, status="active")
            )
            return {
                "subscription_id": "",
                "plan_id": plan.id,
                "payment_intent_client_secret": "",
                "ephemeral_key_secret": "",
                "customer_id": "",
                "publishable_key": self._publishable_key(),
                "status": "active",
                "requires_action": False,
            }

        customer_id = await self._customers.ensure_customer(owner_id, email=owner_email)
        current = await self._repo.get_subscription_for_owner(owner_id)

        try:
            if (
                current is not None
                and current.provider_subscription_id
                and current.status in _ENTITLED
                and current.plan_id != plan.id
            ):
                stripe_sub = self._modify_subscription(
                    current.provider_subscription_id, plan.stripe_price_id
                )
            else:
                stripe_sub = self._stripe.Subscription.create(
                    customer=customer_id,
                    items=[{"price": plan.stripe_price_id}],
                    payment_behavior="default_incomplete",
                    payment_settings={"save_default_payment_method": "on_subscription"},
                    # `confirmation_secret` — current API (2025+). Also keep the
                    # legacy `payment_intent` expand for older API accounts.
                    expand=[
                        "latest_invoice.confirmation_secret",
                        "latest_invoice.payment_intent",
                    ],
                    metadata={"owner_id": owner_id, "plan_id": plan.id},
                )
        except self._stripe.error.CardError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc

        stripe_sub = as_dict(stripe_sub)
        status = (stripe_sub.get("status") or "incomplete").lower()
        invoice = stripe_sub.get("latest_invoice") or {}
        pi = invoice.get("payment_intent") or {}
        # Current API: the client secret to confirm sits on the invoice's
        # confirmation_secret; older accounts still expose payment_intent.
        confirmation_secret = invoice.get("confirmation_secret") or {}
        client_secret = confirmation_secret.get("client_secret") or pi.get("client_secret") or ""
        pi_status = (pi.get("status") or "").lower()

        await self._repo.upsert_subscription(
            Subscription(
                owner_id=owner_id,
                plan_id=plan.id,
                status="active" if status in _ENTITLED else status,
                provider_customer_id=customer_id,
                provider_subscription_id=stripe_sub.get("id"),
                current_period_end=_period_end(stripe_sub),
            )
        )

        return {
            "subscription_id": stripe_sub.get("id") or "",
            "plan_id": plan.id,
            "payment_intent_client_secret": client_secret,
            "ephemeral_key_secret": self._customers.ephemeral_key_secret(customer_id),
            "customer_id": customer_id,
            "publishable_key": self._publishable_key(),
            "status": status,
            "requires_action": pi_status == "requires_action",
        }

    async def verify_subscription(self, owner_id: str, subscription_id: str) -> dict:
        current = await self._repo.get_subscription_for_owner(owner_id)
        if current is None or current.provider_subscription_id != subscription_id:
            raise LookupError("Subscription not found")
        try:
            stripe_sub = self._stripe.Subscription.retrieve(
                subscription_id, expand=["latest_invoice.payment_intent"]
            )
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc

        stripe_sub = as_dict(stripe_sub)
        status = (stripe_sub.get("status") or current.status).lower()
        updated = await self._repo.upsert_subscription(
            Subscription(
                owner_id=owner_id,
                plan_id=current.plan_id,
                status="active" if status in _ENTITLED else status,
                provider_customer_id=current.provider_customer_id,
                provider_subscription_id=subscription_id,
                current_period_end=_period_end(stripe_sub) or current.current_period_end,
            )
        )
        return {
            "plan_id": updated.plan_id,
            "status": updated.status,
            "current_period_end": updated.current_period_end,
        }

    # --- internals ----------------------------------------------------

    def _modify_subscription(self, subscription_id: str, new_price_id: str) -> Any:
        sub = as_dict(self._stripe.Subscription.retrieve(subscription_id))
        item_id = (((sub.get("items") or {}).get("data")) or [{}])[0].get("id")
        return self._stripe.Subscription.modify(
            subscription_id,
            items=[{"id": item_id, "price": new_price_id}],
            proration_behavior="create_prorations",
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )

    def _publishable_key(self) -> str:
        from app.core.config import settings

        return settings.STRIPE_PUBLISHABLE_KEY
