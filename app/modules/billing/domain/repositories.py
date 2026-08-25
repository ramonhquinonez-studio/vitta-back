from typing import Protocol

from .entities import Subscription, SubscriptionPlan


class BillingRepository(Protocol):
    async def list_plans(self) -> list[SubscriptionPlan]:
        ...

    async def get_plan(self, plan_id: str) -> SubscriptionPlan | None:
        ...

    async def get_default_plan(self) -> SubscriptionPlan | None:
        ...

    async def get_subscription_for_owner(self, owner_id: str) -> Subscription | None:
        ...

    async def upsert_subscription(self, subscription: Subscription) -> Subscription:
        ...

    async def get_subscription_for_customer(self, provider_customer_id: str) -> Subscription | None:
        ...


class BillingProviderRepository(Protocol):
    """The swappable piece — a mock provider for local dev (no external
    account needed) and a real Stripe provider for production, selected by
    `Settings.BILLING_PROVIDER`.
    """

    async def create_checkout_session(
        self, *, owner_id: str, owner_email: str, plan: SubscriptionPlan
    ) -> str:
        """Returns a URL the client opens to complete checkout."""
        ...

    async def create_portal_session(self, *, provider_customer_id: str) -> str:
        """Returns a URL the client opens to self-manage the subscription."""
        ...

    def parse_webhook_event(self, *, payload: bytes, signature: str | None) -> dict:
        """Verifies (where applicable) and normalizes a provider webhook
        payload into a dict with at least: `type`, `customer_id`,
        `subscription_id`, `status`, `plan_id` (any of these may be None
        depending on the event type)."""
        ...
