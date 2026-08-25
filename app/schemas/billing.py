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
