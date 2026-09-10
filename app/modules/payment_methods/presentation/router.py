from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.modules.payments.application.stripe_customers import StripeCustomers
from app.modules.payments.infrastructure.mongo_stripe_customers_repository import (
    MongoStripeCustomersRepository,
)
from app.modules.payments.infrastructure.stripe_client import get_stripe

from ..application.payment_methods_service import PaymentMethodsService
from ..domain.entities import SavedCard

router = APIRouter(prefix="/billing/payment-methods", tags=["billing"])


class SavedCardOut(BaseModel):
    id: str
    brand: str | None = None
    last4: str | None = None
    exp_month: int | None = None
    exp_year: int | None = None
    is_default: bool = False


class SavedCardsListOut(BaseModel):
    cards: list[SavedCardOut]


class AddCardIn(BaseModel):
    payment_method_id: str


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _require_native() -> None:
    if not settings.stripe_native_enabled:
        raise HTTPException(status_code=503, detail="Pagos con tarjeta no disponibles todavía.")


def get_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> PaymentMethodsService:
    stripe = get_stripe()
    customers = StripeCustomers(stripe, MongoStripeCustomersRepository(db))
    return PaymentMethodsService(stripe, customers)


def _serialize(card: SavedCard) -> SavedCardOut:
    return SavedCardOut(
        id=card.id,
        brand=card.brand,
        last4=card.last4,
        exp_month=card.exp_month,
        exp_year=card.exp_year,
        is_default=card.is_default,
    )


@router.get("", response_model=SavedCardsListOut)
async def list_cards(
    current=Depends(get_current_user),
    service: PaymentMethodsService = Depends(get_service),
):
    _require_native()
    cards = await service.list_cards(_owner_id(current), email=current.get("email"))
    return SavedCardsListOut(cards=[_serialize(c) for c in cards])


@router.post("", response_model=SavedCardOut)
async def add_card(
    payload: AddCardIn,
    current=Depends(get_current_user),
    service: PaymentMethodsService = Depends(get_service),
):
    _require_native()
    card = await service.add_card(
        _owner_id(current), payload.payment_method_id, email=current.get("email")
    )
    return _serialize(card)


@router.patch("/{payment_method_id}/default", status_code=204)
async def set_default(
    payment_method_id: str,
    current=Depends(get_current_user),
    service: PaymentMethodsService = Depends(get_service),
):
    _require_native()
    await service.set_default(_owner_id(current), payment_method_id)


@router.delete("/{payment_method_id}", status_code=204)
async def delete_card(
    payment_method_id: str,
    current=Depends(get_current_user),
    service: PaymentMethodsService = Depends(get_service),
):
    _require_native()
    await service.delete_card(_owner_id(current), payment_method_id)
