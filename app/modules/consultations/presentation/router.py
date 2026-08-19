from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.schemas.consultation import (
    ConsultationCloseIn,
    ConsultationEvaluationIn,
    ConsultationOut,
    ConsultationStartIn,
    ConsultationUpdateIn,
    EvaluationSnapshotOut,
)

from ..application.consultations_service import ConsultationsService
from ..domain.entities import Consultation
from ..infrastructure.mongo_consultations_repository import MongoConsultationsRepository

router = APIRouter(prefix="/consultations", tags=["consultations"])


def get_consultations_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ConsultationsService:
    return ConsultationsService(MongoConsultationsRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _serialize(consultation: Consultation) -> ConsultationOut:
    evaluation_out = None
    if consultation.evaluation is not None:
        evaluation_out = EvaluationSnapshotOut(
            weight_kg=consultation.evaluation.weight_kg,
            height_cm=consultation.evaluation.height_cm,
            body_fat_pct=consultation.evaluation.body_fat_pct,
            waist_cm=consultation.evaluation.waist_cm,
            hip_cm=consultation.evaluation.hip_cm,
            arm_cm=consultation.evaluation.arm_cm,
            notes=consultation.evaluation.notes,
        )
    return ConsultationOut(
        id=consultation.id,
        patient_id=consultation.patient_id,
        appointment_id=consultation.appointment_id,
        status=consultation.status,
        current_step=consultation.current_step,
        visit_type=consultation.visit_type,
        evaluation=evaluation_out,
        private_notes=consultation.private_notes,
        next_appointment_id=consultation.next_appointment_id,
        completed_at=consultation.completed_at,
        created_at=consultation.created_at,
        updated_at=consultation.updated_at,
    )


@router.post("/start", response_model=ConsultationOut)
async def start_consultation(
    payload: ConsultationStartIn,
    current=Depends(get_current_user),
    service: ConsultationsService = Depends(get_consultations_service),
):
    consultation = await service.start(
        _owner_id(current),
        patient_id=payload.patient_id,
        appointment_id=payload.appointment_id,
    )
    return _serialize(consultation)


@router.get("/{consultation_id}", response_model=ConsultationOut)
async def get_consultation(
    consultation_id: str,
    current=Depends(get_current_user),
    service: ConsultationsService = Depends(get_consultations_service),
):
    try:
        consultation = await service.get_consultation(_owner_id(current), consultation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(consultation)


@router.patch("/{consultation_id}", response_model=ConsultationOut)
async def update_consultation(
    consultation_id: str,
    payload: ConsultationUpdateIn,
    current=Depends(get_current_user),
    service: ConsultationsService = Depends(get_consultations_service),
):
    try:
        consultation = await service.update_consultation(
            _owner_id(current),
            consultation_id,
            visit_type=payload.visit_type,
            current_step=payload.current_step,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(consultation)


@router.patch("/{consultation_id}/evaluation", response_model=ConsultationOut)
async def update_evaluation(
    consultation_id: str,
    payload: ConsultationEvaluationIn,
    current=Depends(get_current_user),
    service: ConsultationsService = Depends(get_consultations_service),
):
    try:
        consultation = await service.update_evaluation(
            _owner_id(current),
            consultation_id,
            weight_kg=payload.weight_kg,
            height_cm=payload.height_cm,
            body_fat_pct=payload.body_fat_pct,
            waist_cm=payload.waist_cm,
            hip_cm=payload.hip_cm,
            arm_cm=payload.arm_cm,
            notes=payload.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(consultation)


@router.patch("/{consultation_id}/close", response_model=ConsultationOut)
async def update_close(
    consultation_id: str,
    payload: ConsultationCloseIn,
    current=Depends(get_current_user),
    service: ConsultationsService = Depends(get_consultations_service),
):
    try:
        consultation = await service.update_close(
            _owner_id(current),
            consultation_id,
            private_notes=payload.private_notes,
            next_appointment_id=payload.next_appointment_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(consultation)


@router.post("/{consultation_id}/complete", response_model=ConsultationOut)
async def complete_consultation(
    consultation_id: str,
    current=Depends(get_current_user),
    service: ConsultationsService = Depends(get_consultations_service),
):
    try:
        consultation = await service.complete(_owner_id(current), consultation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(consultation)
