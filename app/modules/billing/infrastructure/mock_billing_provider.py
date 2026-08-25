import uuid

from ..domain.entities import SubscriptionPlan


class MockBillingProvider:
    """Local-dev stand-in for Stripe — every call succeeds instantly with no
    external account needed. `create_checkout_session` returns a URL to this
    same backend's own confirm endpoint, which immediately activates the
    subscription when hit, simulating what a real checkout would do after
    payment. This lets the whole feature (data model, quota enforcement,
    nutritionist-facing UI) be built and verified end-to-end today; swapping
    in `StripeBillingProvider` later is a config change, not a rewrite.
    """

    async def create_checkout_session(
        self, *, owner_id: str, owner_email: str, plan: SubscriptionPlan
    ) -> str:
        return f"/billing/mock-confirm?owner_id={owner_id}&plan_id={plan.id}&token={uuid.uuid4().hex}"

    async def create_portal_session(self, *, provider_customer_id: str) -> str:
        return f"/billing/mock-portal?customer_id={provider_customer_id}"

    def parse_webhook_event(self, *, payload: bytes, signature: str | None) -> dict:
        raise NotImplementedError("The mock provider has no webhook — see mock-confirm instead.")
