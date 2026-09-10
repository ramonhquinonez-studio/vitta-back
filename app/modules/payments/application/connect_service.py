"""Stripe Connect (Express) onboarding for nutritionists who want to
receive consultation payments. `fidelity_back` has no Connect precedent —
this is the marketplace piece.
"""

from __future__ import annotations

from typing import Any

from .errors import stripe_error_to_http
from ..domain.payment_entities import ConnectAccount
from ..infrastructure.stripe_client import as_dict


class ConnectService:
    def __init__(self, stripe: Any, repo: Any, *, country: str):
        self._stripe = stripe
        self._repo = repo
        self._country = country

    async def account_link(self, owner_id: str, *, email: str | None, refresh_url: str, return_url: str) -> str:
        account = await self._repo.get_connect_account(owner_id)
        try:
            if account is None:
                created = self._stripe.Account.create(
                    type="express",
                    country=self._country,
                    email=email or None,
                    capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
                    business_type="individual",
                    metadata={"owner_id": owner_id},
                )
                account = await self._repo.upsert_connect_account(
                    ConnectAccount(owner_id=owner_id, account_id=created.id)
                )
            link = self._stripe.AccountLink.create(
                account=account.account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding",
            )
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        return link.url

    async def status(self, owner_id: str) -> dict:
        account = await self._repo.get_connect_account(owner_id)
        if account is None:
            return {"connected": False, "charges_enabled": False, "payouts_enabled": False}
        # Refresh from Stripe so the client sees the current state after
        # returning from hosted onboarding, not just the last webhook.
        try:
            fresh = as_dict(self._stripe.Account.retrieve(account.account_id))
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        requirements = (fresh.get("requirements") or {})
        updated = await self._repo.upsert_connect_account(
            ConnectAccount(
                owner_id=owner_id,
                account_id=account.account_id,
                charges_enabled=bool(fresh.get("charges_enabled")),
                payouts_enabled=bool(fresh.get("payouts_enabled")),
                requirements_due=list(requirements.get("currently_due") or []),
                disabled_reason=requirements.get("disabled_reason"),
            )
        )
        return {
            "connected": True,
            "account_id": updated.account_id,
            "charges_enabled": updated.charges_enabled,
            "payouts_enabled": updated.payouts_enabled,
            "requirements_due": updated.requirements_due,
            "disabled_reason": updated.disabled_reason,
        }
