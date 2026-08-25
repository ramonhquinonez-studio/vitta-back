from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SubscriptionPlan:
    id: str
    name: str
    client_limit: int | None  # None = unlimited
    stripe_price_id: str | None
    is_default: bool


@dataclass(frozen=True)
class Subscription:
    owner_id: str
    plan_id: str
    status: str  # "active" | "trialing" | "past_due" | "canceled"
    provider_customer_id: str | None = None
    provider_subscription_id: str | None = None
    current_period_end: datetime | None = None
