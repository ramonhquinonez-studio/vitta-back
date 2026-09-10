"""Saved cards, Stripe as the single source of truth. Mirrors
`fidelity_back`'s `/v1/payment-methods` (list / add / set-default / delete)
minus the local-mirror fallback — the client (`nutri_pro`/`nutri_app`)
keeps its own offline copy.
"""

from __future__ import annotations

from typing import Any

from app.modules.payments.application.errors import stripe_error_to_http
from app.modules.payments.application.stripe_customers import StripeCustomers
from app.modules.payments.infrastructure.stripe_client import as_dict

from ..domain.entities import SavedCard


class PaymentMethodsService:
    def __init__(self, stripe: Any, customers: StripeCustomers):
        self._stripe = stripe
        self._customers = customers

    async def list_cards(self, user_id: str, *, email: str | None = None) -> list[SavedCard]:
        customer_id = await self._customers.ensure_customer(user_id, email=email)
        try:
            pms = as_dict(self._stripe.PaymentMethod.list(customer=customer_id, type="card"))
            customer = as_dict(self._stripe.Customer.retrieve(customer_id))
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        default_id = ((customer.get("invoice_settings") or {}).get("default_payment_method")) or ""
        return [self._to_card(pm, default_id) for pm in (pms.get("data") or [])]

    async def add_card(
        self, user_id: str, payment_method_id: str, *, email: str | None = None
    ) -> SavedCard:
        customer_id = await self._customers.ensure_customer(user_id, email=email)
        try:
            self._stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            existing = as_dict(self._stripe.PaymentMethod.list(customer=customer_id, type="card"))
            if len((existing.get("data") or [])) == 1:
                self._set_default(customer_id, payment_method_id)
            pm = as_dict(self._stripe.PaymentMethod.retrieve(payment_method_id))
            customer = as_dict(self._stripe.Customer.retrieve(customer_id))
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        default_id = ((customer.get("invoice_settings") or {}).get("default_payment_method")) or ""
        return self._to_card(pm, default_id)

    async def set_default(self, user_id: str, payment_method_id: str) -> None:
        customer_id = await self._customers.ensure_customer(user_id)
        self._assert_owned(customer_id, payment_method_id)
        self._set_default(customer_id, payment_method_id)

    async def delete_card(self, user_id: str, payment_method_id: str) -> None:
        customer_id = await self._customers.ensure_customer(user_id)
        self._assert_owned(customer_id, payment_method_id)
        try:
            self._stripe.PaymentMethod.detach(payment_method_id)
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc

    # --- internals -------------------------------------------------------

    def _set_default(self, customer_id: str, payment_method_id: str) -> None:
        try:
            self._stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc

    def _assert_owned(self, customer_id: str, payment_method_id: str) -> None:
        try:
            pm = as_dict(self._stripe.PaymentMethod.retrieve(payment_method_id))
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        if pm.get("customer") != customer_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Tarjeta no encontrada")

    @staticmethod
    def _to_card(pm: Any, default_id: str) -> SavedCard:
        card = pm.get("card") or {}
        return SavedCard(
            id=pm.get("id"),
            brand=card.get("brand"),
            last4=card.get("last4"),
            exp_month=card.get("exp_month"),
            exp_year=card.get("exp_year"),
            is_default=pm.get("id") == default_id,
        )
