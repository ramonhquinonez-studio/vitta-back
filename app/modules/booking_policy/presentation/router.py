from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.modules.nutritionist_profile.infrastructure.mongo_nutritionist_profile_repository import (
    MongoNutritionistProfileRepository,
)

from ..application.booking_policy_service import BookingPolicyService
from ..domain.entities import BookingPolicy
from ..infrastructure.mongo_booking_policy_repository import MongoBookingPolicyRepository

router = APIRouter(
    prefix="/booking-policy",
    tags=["booking_policy"],
    dependencies=[Depends(require_role("nutritionist"))],
)


class BookingPolicyUpdate(BaseModel):
    payment_mode: str | None = None
    deposit_type: str | None = None
    deposit_value: float | None = None
    requires_approval: bool | None = None
    reschedule_limit: int | None = None
    reschedule_notice_hours: int | None = Field(default=None, ge=0)
    cancellation_cutoff_hours: int | None = Field(default=None, ge=0)
    slot_hold_minutes: int | None = None
    policy_text: str | None = None


class BookingPolicyOut(BaseModel):
    payment_mode: str
    deposit_type: str
    deposit_value: float
    requires_approval: bool
    reschedule_limit: int
    reschedule_notice_hours: int
    cancellation_cutoff_hours: int
    slot_hold_minutes: int
    policy_text: str | None
    # Resolved preview against the nutritionist's own session price.
    amount_due_cents: int
    currency: str
    resolved_policy_text: str


def get_booking_policy_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> BookingPolicyService:
    return BookingPolicyService(MongoBookingPolicyRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


async def _serialize(
    policy: BookingPolicy, service: BookingPolicyService, db: AsyncIOMotorDatabase, owner_id: str
) -> BookingPolicyOut:
    profile = await MongoNutritionistProfileRepository(db).get_for_owner(owner_id)
    price = profile.session_price if profile else None
    currency = profile.session_price_currency if profile else "MXN"
    resolved = service.resolve_for_patient(policy, session_price=price, currency=currency)
    return BookingPolicyOut(
        payment_mode=policy.payment_mode,
        deposit_type=policy.deposit_type,
        deposit_value=policy.deposit_value,
        requires_approval=policy.requires_approval,
        reschedule_limit=policy.reschedule_limit,
        reschedule_notice_hours=policy.reschedule_notice_hours,
        cancellation_cutoff_hours=policy.cancellation_cutoff_hours,
        slot_hold_minutes=policy.slot_hold_minutes,
        policy_text=policy.policy_text,
        amount_due_cents=resolved["amount_due_cents"],
        currency=resolved["currency"],
        resolved_policy_text=resolved["policy_text"],
    )


@router.get("/me", response_model=BookingPolicyOut)
async def get_my_booking_policy(
    current=Depends(get_current_user),
    service: BookingPolicyService = Depends(get_booking_policy_service),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    owner_id = _owner_id(current)
    policy = await service.get_for_owner(owner_id)
    return await _serialize(policy, service, db, owner_id)


@router.put("/me", response_model=BookingPolicyOut)
async def update_my_booking_policy(
    payload: BookingPolicyUpdate,
    current=Depends(get_current_user),
    service: BookingPolicyService = Depends(get_booking_policy_service),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    owner_id = _owner_id(current)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        policy = await service.upsert_for_owner(owner_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _serialize(policy, service, db, owner_id)
