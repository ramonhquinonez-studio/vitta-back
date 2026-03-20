from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
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
