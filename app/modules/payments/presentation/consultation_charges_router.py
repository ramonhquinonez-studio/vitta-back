from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.modules.appointments.infrastructure.mongo_appointments_repository import (
    MongoAppointmentsRepository,
)
from app.modules.consultations.infrastructure.mongo_consultations_repository import (
    MongoConsultationsRepository,
)
from app.modules.me.infrastructure.mongo_me_repository import MongoMeRepository
from app.modules.nutritionist_profile.infrastructure.mongo_nutritionist_profile_repository import (
    MongoNutritionistProfileRepository,
)
from app.modules.patients.infrastructure.mongo_patients_repository import (
    MongoPatientsRepository,
)

from ..application.connect_service import ConnectService
from ..application.consultation_charges_service import ConsultationChargesService
from ..application.stripe_customers import StripeCustomers
from ..infrastructure.mongo_payments_repository import MongoPaymentsRepository
from ..infrastructure.mongo_stripe_customers_repository import MongoStripeCustomersRepository
from ..infrastructure.stripe_client import get_stripe

router = APIRouter(prefix="/payments", tags=["payments"])


class AccountLinkIn(BaseModel):
    refresh_url: str
    return_url: str


class AccountLinkOut(BaseModel):
    url: str


class ChargeSheetOut(BaseModel):
    payment_id: str
    payment_intent_client_secret: str
    ephemeral_key_secret: str
    customer_id: str
    publishable_key: str
    amount_cents: int
    currency: str
    status: str
    requires_action: bool


def _uid(current) -> str:
    uid = current.get("sub") or current.get("id")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return uid


def _require_native() -> None:
    if not settings.stripe_native_enabled:
        raise HTTPException(status_code=503, detail="Pagos no disponibles todavía.")


def _payments_repo(db) -> MongoPaymentsRepository:
    return MongoPaymentsRepository(db)


def get_connect_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ConnectService:
    return ConnectService(
        get_stripe(), _payments_repo(db), country=settings.STRIPE_CONNECT_COUNTRY
    )


def get_charges_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ConsultationChargesService:
    stripe = get_stripe()
    customers = StripeCustomers(stripe, MongoStripeCustomersRepository(db))
    me_repo = MongoMeRepository(db)
    consultations_repo = MongoConsultationsRepository(db)
    appointments_repo = MongoAppointmentsRepository(db)
    profile_repo = MongoNutritionistProfileRepository(db)

    async def get_patient_for_user(user_id: str):
        return await me_repo.get_patient_for_user(user_id)

    async def get_consultation(owner_id: str, ref_id: str):
        # `ref_id` is a consultation id when it comes from the wizard, or an
        # appointment id when it comes from `nutri_app`'s "Historial de
        # consultas" (which lists past appointments). Accept either.
        c = await consultations_repo.get_for_owner(owner_id, ref_id)
        if c is not None:
            return {"patient_id": c.patient_id, "appointment_id": c.appointment_id}
        try:
            a = await appointments_repo.get_for_owner(owner_id, ref_id)
        except Exception:
            a = None
        if a is not None and a.patient_id:
            return {"patient_id": a.patient_id, "appointment_id": ref_id}
        return None

    async def get_session_price(owner_id: str):
        profile = await profile_repo.get_for_owner(owner_id)
        if profile is None:
            return None, "MXN"
        return profile.session_price, profile.session_price_currency

    return ConsultationChargesService(
        stripe,
        customers,
        _payments_repo(db),
        get_patient_for_user=get_patient_for_user,
        get_consultation=get_consultation,
        get_session_price=get_session_price,
    )


# -- Connect (nutritionist) ---------------------------------------------

@router.post("/connect/account-link", response_model=AccountLinkOut)
async def connect_account_link(
    payload: AccountLinkIn,
    current=Depends(require_role("nutritionist")),
    service: ConnectService = Depends(get_connect_service),
):
    _require_native()
    url = await service.account_link(
        _uid(current),
        email=current.get("email"),
        refresh_url=payload.refresh_url,
        return_url=payload.return_url,
    )
    return AccountLinkOut(url=url)


@router.get("/connect/status")
async def connect_status(
    current=Depends(require_role("nutritionist")),
    service: ConnectService = Depends(get_connect_service),
):
    _require_native()
    return await service.status(_uid(current))


# -- Consultation charge (patient) ------------------------------------

@router.post("/consultations/{consultation_id}/sheet", response_model=ChargeSheetOut)
async def consultation_sheet(
    consultation_id: str,
    current=Depends(get_current_user),
    service: ConsultationChargesService = Depends(get_charges_service),
):
    _require_native()
    return await service.create_sheet(
        _uid(current), consultation_id, email=current.get("email")
    )


@router.post("/{payment_id}/verify")
async def verify_payment(
    payment_id: str,
    current=Depends(get_current_user),
    service: ConsultationChargesService = Depends(get_charges_service),
):
    _require_native()
    return await service.verify(_uid(current), payment_id)


@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: str,
    current=Depends(require_role("nutritionist")),
    service: ConsultationChargesService = Depends(get_charges_service),
):
    _require_native()
    return await service.refund(_uid(current), payment_id)


@router.get("/mine")
async def my_payments(
    current=Depends(get_current_user),
    service: ConsultationChargesService = Depends(get_charges_service),
):
    _require_native()
    return await service.list_for_patient(_uid(current))


@router.get("/received")
async def received_payments(
    current=Depends(require_role("nutritionist")),
    service: ConsultationChargesService = Depends(get_charges_service),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _require_native()
    owner_id = _uid(current)
    rows = await service.list_for_nutritionist(owner_id)
    # Resolve each payer's display name here (the charges service stays free
    # of the patients module) — mirrors the consultations list endpoint.
    patients_repo = MongoPatientsRepository(db)
    names: dict[str, str | None] = {}
    for row in rows:
        pid = row.get("patient_id")
        if pid and pid not in names:
            patient = await patients_repo.get_for_owner(owner_id, pid)
            names[pid] = patient.name if patient else None
        row["patient_name"] = names.get(pid)
    return rows
