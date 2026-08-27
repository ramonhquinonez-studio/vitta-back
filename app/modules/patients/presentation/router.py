from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.core.quota import PatientQuotaCheckerAdapter
from app.core.storage import save_upload
from app.db.mongo import get_db
from app.modules.billing.presentation.router import get_billing_service
from app.modules.nutritionist_profile.presentation.router import get_nutritionist_profile_service
from app.schemas.auth import InviteCodeOut
from app.schemas.pagination import Page, PaginationParams
from app.schemas.patients import ClaimPatientIn, PatientIn, PatientOut, PatientUpdate

from ..application.patients_service import PatientsService
from ..domain.entities import Patient
from ..infrastructure.mongo_patients_repository import MongoPatientsRepository


router = APIRouter(
    prefix="/patients",
    tags=["patients"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_patients_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> PatientsService:
    repository = MongoPatientsRepository(db)
    quota_checker = PatientQuotaCheckerAdapter(get_billing_service(db), repository.count_for_owner)
    return PatientsService(repository, quota_checker=quota_checker)


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
        user_id=patient.user_id,
        daily_kcal_goal=patient.daily_kcal_goal,
        daily_protein_g_goal=patient.daily_protein_g_goal,
        daily_carbs_g_goal=patient.daily_carbs_g_goal,
        daily_fat_g_goal=patient.daily_fat_g_goal,
        email=patient.email,
        phone=patient.phone,
        archived_at=patient.archived_at,
        tags=patient.tags,
    )


@router.get("", response_model=Page[PatientOut])
async def list_patients(
    pagination: PaginationParams = Depends(),
    q: str | None = Query(None, description="Busqueda por nombre (regex, case-insensitive)"),
    include_archived: bool = Query(False),
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    items, total = await service.list_patients(
        _owner_id(current),
        page=pagination.page,
        limit=pagination.limit,
        query=q,
        include_archived=include_archived,
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
    try:
        patient = await service.create_patient(_owner_id(current), payload.model_dump())
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return _serialize(patient)


@router.get("/dashboard", response_model=dict)
async def get_practice_dashboard(
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
    profile_service=Depends(get_nutritionist_profile_service),
):
    owner_id = _owner_id(current)
    dashboard = await service.get_dashboard(owner_id)
    profile = await profile_service.get_my_profile(owner_id)
    session_price = profile.get("session_price") or 0
    dashboard["estimated_revenue_this_month"] = dashboard["completed_appointments_this_month"] * session_price
    dashboard["revenue_currency"] = profile.get("session_price_currency") or "MXN"
    return dashboard


@router.post("/invite-codes", response_model=InviteCodeOut, status_code=201)
async def create_invite_code(
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    return await service.create_invite_code(_owner_id(current))


@router.post("/claim", response_model=PatientOut)
async def claim_patient(
    payload: ClaimPatientIn,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """The inverse direction of an invite code: a patient who self-registered
    without a nutritionist (`030-back-patient-self-registration`) shares
    their own connection code, and the nutritionist redeems it here to add
    that patient to their roster."""
    try:
        patient = await service.claim_patient(_owner_id(current), payload.code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return _serialize(patient)


@router.post("/{patient_id}/invite-code", response_model=InviteCodeOut, status_code=201)
async def create_patient_invite_code(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """Generates a code scoped to an existing chart-only patient — when
    redeemed, it links the new account to this patient instead of creating a
    duplicate (see `027-back-consultations-foundation`'s sibling spec
    `029-back-patient-account-linking`)."""
    try:
        return await service.create_invite_code(_owner_id(current), patient_id=patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@router.delete("/{patient_id}", response_model=PatientOut)
async def archive_patient(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """Soft-delete: archives the patient (excluded from the default roster
    and dashboard) instead of removing the chart, so it can be restored via
    `unarchive_patient` below."""
    try:
        patient = await service.archive_patient(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(patient)


@router.post("/{patient_id}/unarchive", response_model=PatientOut)
async def unarchive_patient(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        patient = await service.unarchive_patient(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(patient)


@router.post("/{patient_id}/workout-logs/toggle", response_model=dict)
async def toggle_patient_workout_log(
    patient_id: str,
    payload: dict[str, Any],
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """Lets the nutritionist mark a client's exercise done on their behalf
    (e.g. during an in-person session) — mirrors the patient-facing
    `POST /me/workout-logs/toggle`, scoped to a patient this owner has."""
    try:
        return await service.toggle_workout_log(_owner_id(current), patient_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@router.get("/{patient_id}/measurements", response_model=list[dict])
async def list_patient_measurements(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        return await service.list_measurements(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{patient_id}/checkin-responses", response_model=list[dict])
async def list_patient_checkin_responses(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        return await service.list_checkin_responses(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{patient_id}/workout-plan-assignments", response_model=list[dict])
async def list_patient_workout_plan_assignments(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        return await service.list_workout_plan_assignments(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{patient_id}/workout-logs", response_model=list[dict])
async def list_patient_workout_logs(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        return await service.list_workout_logs(_owner_id(current), patient_id)
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


@router.get("/{patient_id}/plan_assignments", response_model=list[dict])
async def list_patient_plan_assignments(
    patient_id: str,
    current=Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    try:
        return await service.list_plan_assignments(_owner_id(current), patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
