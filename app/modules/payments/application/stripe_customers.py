"""One Stripe Customer per app user (nutritionist *or* patient), created
once and reused. Persisted in the `stripe_customers` collection keyed by
the bare user id. Mirrors `fidelity_back`'s `_ensure_stripe_customer`.
"""

from __future__ import annotations

from typing import Any

from .errors import stripe_error_to_http
from ..domain.repositories import StripeCustomersRepository


class StripeCustomers:
    def __init__(self, stripe: Any, repository: StripeCustomersRepository):
        self._stripe = stripe
        self._repo = repository

    async def ensure_customer(self, user_id: str, *, email: str | None = None) -> str:
        existing = await self._repo.get_customer_id(user_id)
        if existing:
            return existing
        try:
            customer = self._stripe.Customer.create(
                email=email or None,
                metadata={"userId": user_id},
            )
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        await self._repo.set_customer_id(user_id, customer.id)
        return customer.id

    def ephemeral_key_secret(self, customer_id: str) -> str:
        try:
            key = self._stripe.EphemeralKey.create(
                customer=customer_id,
                stripe_version="2024-06-20",
            )
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        return key.secret
