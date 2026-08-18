from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.schemas.patients import PatientUpdate

from ..application.me_service import MeService
from ..infrastructure.mongo_me_repository import MongoMeRepository


router = APIRouter(prefix="/me", tags=["me"])


def get_me_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> MeService:
    return MeService(MongoMeRepository(db))


def _user_id(current) -> str:
    user_id = current.get("id") or current.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return user_id


def _unwrap_runtime_error(exc: RuntimeError):
    detail = exc.args[0] if exc.args else str(exc)
    if isinstance(detail, dict):
        raise HTTPException(status_code=409, detail=detail) from exc
    raise HTTPException(status_code=400, detail=str(detail)) from exc


@router.get("/profile", response_model=dict)
async def my_profile(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.get_profile(_user_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/profile", response_model=dict)
async def update_my_profile(
    payload: PatientUpdate,
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    updates = {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None
    }
    try:
        return await service.update_profile(_user_id(current), updates)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/appointments", response_model=list[dict])
async def my_appointments(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None, alias="to"),
):
    try:
        return await service.list_appointments(_user_id(current), from_dt=from_, to_dt=to)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/consultations", response_model=list[dict])
async def my_consultations(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.list_consultations(_user_id(current))


@router.get("/plan/active", response_model=dict | None)
async def my_active_plan(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.get_active_plan(_user_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/appointments", response_model=dict, status_code=201)
async def request_appointment(
    payload: dict[str, Any],
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.request_appointment(_user_id(current), payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        _unwrap_runtime_error(exc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/appointments/{appointment_id}", response_model=dict)
async def my_appointment_detail(
    appointment_id: str,
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.get_appointment_detail(_user_id(current), appointment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/appointments/{appointment_id}/cancel", response_model=dict)
async def cancel_my_appointment(
    appointment_id: str,
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.cancel_appointment(_user_id(current), appointment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/appointments/{appointment_id}/reschedule", response_model=dict)
async def reschedule_my_appointment(
    appointment_id: str,
    payload: dict[str, Any],
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.reschedule_appointment(_user_id(current), appointment_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        _unwrap_runtime_error(exc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/measurements", response_model=list[dict])
async def my_measurements(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
    limit: int = 50,
):
    try:
        return await service.list_measurements(_user_id(current), limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/measurements", response_model=dict)
async def add_measurement(
    payload: dict[str, Any],
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.add_measurement(_user_id(current), payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/progress", response_model=dict)
async def my_progress(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
    range: str | None = Query("30d"),
):
    try:
        return await service.get_progress(_user_id(current), range)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/prescriptions", response_model=list[dict])
async def my_prescriptions(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
    limit: int = 10,
):
    try:
        return await service.list_prescriptions(_user_id(current), limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/recipe_collections", response_model=list[dict])
async def my_recipe_collections(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.list_recipe_collections(_user_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/recipes/{recipe_id}", response_model=dict)
async def my_recipe_detail(
    recipe_id: str,
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.get_recipe(_user_id(current), recipe_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/body_compositions", response_model=list[dict])
async def my_body_compositions(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.list_body_compositions(_user_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/education_videos", response_model=list[dict])
async def my_education_videos(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.list_education_videos(_user_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/nutritionist_profile", response_model=dict | None)
async def my_nutritionist_profile(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.get_nutritionist_profile(_user_id(current))


@router.get("/clinical/history", response_model=dict)
async def my_clinical_history(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.get_clinical_history(_user_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
