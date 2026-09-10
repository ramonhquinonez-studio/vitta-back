from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.mongo import get_db

from ..application.errors import stripe_error_to_http
from ..application.stripe_customers import StripeCustomers
from ..infrastructure.mongo_stripe_customers_repository import (
    MongoStripeCustomersRepository,
)
from ..infrastructure.stripe_client import get_stripe

# Shares the `/billing` prefix with the existing billing router — this is
# the native-SDK companion to the hosted-checkout endpoints.
router = APIRouter(prefix="/billing", tags=["billing"])


class SetupIntentOut(BaseModel):
    client_secret: str
    ephemeral_key_secret: str
    customer_id: str
    publishable_key: str


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _require_native() -> None:
    if not settings.stripe_native_enabled:
        raise HTTPException(status_code=503, detail="Pagos con tarjeta no disponibles todavía.")


def get_stripe_customers(db: AsyncIOMotorDatabase = Depends(get_db)) -> StripeCustomers:
    return StripeCustomers(get_stripe(), MongoStripeCustomersRepository(db))


@router.post("/setup-intent", response_model=SetupIntentOut)
async def create_setup_intent(
    current=Depends(get_current_user),
    customers: StripeCustomers = Depends(get_stripe_customers),
):
    """Everything a client needs to add a card with no payment: a
    SetupIntent client secret + the ephemeral key for the Customer."""
    _require_native()
    stripe = get_stripe()
    user_id = _owner_id(current)
    customer_id = await customers.ensure_customer(user_id, email=current.get("email"))
    try:
        intent = stripe.SetupIntent.create(
            customer=customer_id,
            usage="off_session",
            payment_method_types=["card"],
        )
    except stripe.error.StripeError as exc:  # type: ignore[attr-defined]
        raise stripe_error_to_http(exc) from exc
    return SetupIntentOut(
        client_secret=intent.client_secret,
        ephemeral_key_secret=customers.ephemeral_key_secret(customer_id),
        customer_id=customer_id,
        publishable_key=settings.STRIPE_PUBLISHABLE_KEY,
    )
