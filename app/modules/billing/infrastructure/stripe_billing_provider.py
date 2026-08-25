from app.core.config import settings

from ..domain.entities import SubscriptionPlan


class StripeBillingProvider:
    """Real Stripe Checkout + Customer Portal integration. Requires
    `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` to be set — selected via
    `Settings.BILLING_PROVIDER = "stripe"`. Not live-verified as part of
    Phase 0 (no Stripe account/test keys set up yet); wired and ready for
    when they are.
    """

    def __init__(self) -> None:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._stripe = stripe

    async def create_checkout_session(
        self, *, owner_id: str, owner_email: str, plan: SubscriptionPlan
    ) -> str:
        session = self._stripe.checkout.Session.create(
            mode="subscription",
            customer_email=owner_email,
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            success_url=f"{settings.APP_OAUTH_SUCCESS_REDIRECT}?billing=success",
            cancel_url=f"{settings.APP_OAUTH_SUCCESS_REDIRECT}?billing=cancel",
            client_reference_id=owner_id,
        )
        return session.url

    async def create_portal_session(self, *, provider_customer_id: str) -> str:
        session = self._stripe.billing_portal.Session.create(customer=provider_customer_id)
        return session.url

    def parse_webhook_event(self, *, payload: bytes, signature: str | None) -> dict:
        event = self._stripe.Webhook.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )
        data = event["data"]["object"]
        return {
            "type": event["type"],
            "customer_id": data.get("customer"),
            "subscription_id": data.get("id") if event["type"].startswith("customer.subscription") else data.get("subscription"),
            "status": data.get("status"),
            "owner_id": data.get("client_reference_id"),
        }
