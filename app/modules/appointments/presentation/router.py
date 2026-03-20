from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import get_current_user
from app.db.mongo import get_db

from ..application.appointments_service import AppointmentsService, OverlapError
from ..domain.entities import Appointment
from ..infrastructure.google_calendar_gateway import GoogleCalendarGateway
from ..infrastructure.mongo_appointments_repository import MongoAppointmentsRepository


router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentCreate(BaseModel):
    patient_id: str = Field(validation_alias="patientId")
    start: datetime
    end: datetime | None = None
    mode: Literal["online", "onsite"]
    status: Literal["confirmed", "pending", "canceled"] = "pending"
    note: str | None = None
    plan_id: str | None = Field(default=None, validation_alias="planId")
    no_sync: bool = False
    model_config = ConfigDict(populate_by_name=True)


class AppointmentUpdate(BaseModel):
    patient_id: str | None = Field(default=None, validation_alias="patientId")
    start: datetime | None = None
    end: datetime | None = None
    mode: Literal["online", "onsite"] | None = None
    status: Literal["confirmed", "pending", "canceled"] | None = None
    note: str | None = None
    plan_id: str | None = Field(default=None, validation_alias="planId")
    no_sync: bool | None = None
    model_config = ConfigDict(populate_by_name=True)


class AppointmentPatientOut(BaseModel):
    id: str | None = None
    name: str | None = None
    email: str | None = None


class AppointmentOut(BaseModel):
    id: str
    patient_id: str | None
    start: datetime
    end: datetime | None
    mode: str
    status: str
    note: str | None = None
    plan_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    google_event_id: str | None = None
    patient: AppointmentPatientOut | None = None


def get_appointments_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AppointmentsService:
    return AppointmentsService(
        repository=MongoAppointmentsRepository(db),
        calendar_gateway=GoogleCalendarGateway(db),
    )


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _serialize(appointment: Appointment) -> AppointmentOut:
    patient = appointment.patient
    patient_out = None
    if patient is not None:
        patient_out = AppointmentPatientOut(
            id=patient.id,
            name=patient.name,
            email=patient.email,
        )
    return AppointmentOut(
        id=appointment.id,
        patient_id=appointment.patient_id,
        start=appointment.start,
        end=appointment.end,
        mode=appointment.mode,
        status=appointment.status,
        note=appointment.note,
        plan_id=appointment.plan_id,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        google_event_id=appointment.google_event_id,
        patient=patient_out,
    )


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    status: str | None = Query(None),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None, alias="to"),
    q: str | None = Query(None, description="Busca por nombre de paciente o nota"),
    current=Depends(get_current_user),
    service: AppointmentsService = Depends(get_appointments_service),
):
    appointments = await service.list_appointments(
        _owner_id(current),
        status=status,
        from_dt=from_,
        to_dt=to,
        query=q,
    )
    return [_serialize(item) for item in appointments]


@router.post("", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    payload: AppointmentCreate,
    current=Depends(get_current_user),
    service: AppointmentsService = Depends(get_appointments_service),
):
    try:
        appointment = await service.create_appointment(
            _owner_id(current),
            patient_id=payload.patient_id,
            start=payload.start,
            end=payload.end,
            mode=payload.mode,
            status=payload.status,
            note=payload.note,
            plan_id=payload.plan_id,
            no_sync=payload.no_sync,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OverlapError as exc:
        raise HTTPException(
            status_code=409,
            detail=service.conflict_detail(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _serialize(appointment)


@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(
    appointment_id: str,
    current=Depends(get_current_user),
    service: AppointmentsService = Depends(get_appointments_service),
):
    try:
        appointment = await service.get_appointment(_owner_id(current), appointment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    current=Depends(get_current_user),
    service: AppointmentsService = Depends(get_appointments_service),
):
    try:
        appointment = await service.update_appointment(
            _owner_id(current),
            appointment_id,
            patient_id=payload.patient_id,
            start=payload.start,
            end=payload.end,
            mode=payload.mode,
            status=payload.status,
            note=payload.note,
            plan_id=payload.plan_id,
            no_sync=payload.no_sync,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OverlapError as exc:
        raise HTTPException(
            status_code=409,
            detail=service.conflict_detail(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _serialize(appointment)


@router.delete("/{appointment_id}", status_code=204)
async def delete_appointment(
    appointment_id: str,
    current=Depends(get_current_user),
    service: AppointmentsService = Depends(get_appointments_service),
):
    try:
        await service.delete_appointment(_owner_id(current), appointment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return None
