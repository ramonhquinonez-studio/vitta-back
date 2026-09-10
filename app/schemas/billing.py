from datetime import datetime

from pydantic import BaseModel


class SubscriptionPlanOut(BaseModel):
    id: str
    name: str
    client_limit: int | None
    is_default: bool


class SubscriptionOut(BaseModel):
    plan_id: str
    status: str
    current_period_end: datetime | None


class CheckoutSessionOut(BaseModel):
    url: str


class CheckoutIn(BaseModel):
    plan_id: str


class SubscriptionSheetIn(BaseModel):
    plan_id: str


class SubscriptionSheetOut(BaseModel):
    subscription_id: str
    plan_id: str
    payment_intent_client_secret: str
    ephemeral_key_secret: str
    customer_id: str
    publishable_key: str
    status: str
    requires_action: bool


class SubscriptionVerifyIn(BaseModel):
    subscription_id: str


class SubscriptionVerifyOut(BaseModel):
    plan_id: str
    status: str
    current_period_end: datetime | None = None
