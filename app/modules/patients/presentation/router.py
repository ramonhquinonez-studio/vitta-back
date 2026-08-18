from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.core.storage import save_upload
from app.db.mongo import get_db
from app.schemas.auth import InviteCodeOut
from app.schemas.pagination import Page, PaginationParams
from app.schemas.patients import PatientIn, PatientOut, PatientUpdate

from ..application.patients_service import PatientsService
from ..domain.entities import Patient
from ..infrastructure.mongo_patients_repository import MongoPatientsRepository


router = APIRouter(prefix="/patients", tags=["patients"])


def get_patients_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> PatientsService:
    return PatientsService(MongoPatientsRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _serialize(patient: Patient) -> PatientOut:
    return PatientOut(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        sex=patient.sex,
        height_cm=patient.height_cm,
        allergies=patient.allergies,
        notes=patient.notes,
        owner_id=patient.owner_id,
    )


@router.get("", response_model=Page[PatientOut])
async def list_patients(
    pagination: PaginationParams = Depends(),
    q: str | None = Query(None, description="Busqueda por nombre (regex, case-insensitive)"),
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    items, total = await service.list_patients(
        _owner_id(current),
        page=pagination.page,
        limit=pagination.limit,
        query=q,
    )
    return Page(
        items=[_serialize(item) for item in items],
        page=pagination.page,
        limit=pagination.limit,
        total=total,
    )


@router.post("", response_model=PatientOut, status_code=201)
async def create_patient(
    payload: PatientIn,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    patient = await service.create_patient(_owner_id(current), payload.model_dump())
    return _serialize(patient)


@router.post("/invite-codes", response_model=InviteCodeOut, status_code=201)
async def create_invite_code(
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    return await service.create_invite_code(_owner_id(current))


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        patient = await service.get_patient(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(patient)


@router.patch("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    updates = {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None
    }
    try:
        patient = await service.update_patient(_owner_id(current), patient_id, updates)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(patient)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        await service.delete_patient(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/{patient_id}/body_compositions", response_model=dict, status_code=201)
async def add_patient_body_composition(
    patient_id: str,
    at: datetime | None = Form(None),
    provider: str | None = Form(None),
    weight_kg: float | None = Form(None),
    body_fat_pct: float | None = Form(None),
    skeletal_muscle_kg: float | None = Form(None),
    body_fat_mass_kg: float | None = Form(None),
    total_body_water_l: float | None = Form(None),
    protein_kg: float | None = Form(None),
    minerals_kg: float | None = Form(None),
    bmi: float | None = Form(None),
    visceral_fat_level: float | None = Form(None),
    bmr_kcal: float | None = Form(None),
    waist_hip_ratio: float | None = Form(None),
    obesity_degree_pct: float | None = Form(None),
    inbody_score: float | None = Form(None),
    ideal_weight_kg: float | None = Form(None),
    weight_control_kg: float | None = Form(None),
    fat_control_kg: float | None = Form(None),
    muscle_control_kg: float | None = Form(None),
    grip_strength_left_kg: float | None = Form(None),
    grip_strength_right_kg: float | None = Form(None),
    file: UploadFile | None = File(None),
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    attachment_url: str | None = None
    attachment_type: str | None = None
    if file is not None and file.filename:
        attachment_url, attachment_type = await save_upload(
            file, subfolder=f"body_compositions/{patient_id}"
        )

    metrics = {
        key: value
        for key, value in {
            "weight_kg": weight_kg,
            "body_fat_pct": body_fat_pct,
            "skeletal_muscle_kg": skeletal_muscle_kg,
            "body_fat_mass_kg": body_fat_mass_kg,
            "total_body_water_l": total_body_water_l,
            "protein_kg": protein_kg,
            "minerals_kg": minerals_kg,
            "bmi": bmi,
            "visceral_fat_level": visceral_fat_level,
            "bmr_kcal": bmr_kcal,
            "waist_hip_ratio": waist_hip_ratio,
            "obesity_degree_pct": obesity_degree_pct,
            "inbody_score": inbody_score,
            "ideal_weight_kg": ideal_weight_kg,
            "weight_control_kg": weight_control_kg,
            "fat_control_kg": fat_control_kg,
            "muscle_control_kg": muscle_control_kg,
            "grip_strength_left_kg": grip_strength_left_kg,
            "grip_strength_right_kg": grip_strength_right_kg,
        }.items()
        if value is not None
    }

    payload = {
        "at": at,
        "provider": provider,
        "metrics": metrics,
        "attachment_url": attachment_url,
        "attachment_type": attachment_type,
    }
    try:
        return await service.add_body_composition(_owner_id(current), patient_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{patient_id}/body_compositions", response_model=list[dict])
async def list_patient_body_compositions(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        return await service.list_body_compositions(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{patient_id}/food_diary_entries", response_model=list[dict])
async def list_patient_food_diary_entries(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        return await service.list_food_diary_entries(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
