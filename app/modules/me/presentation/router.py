from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.core.notify import send_push_to_tokens
from app.core.storage import save_upload
from app.db.mongo import get_db
from app.schemas.checkin import FormResponseCreate, FormResponseOut, FormTemplateOut
from app.schemas.messaging import MessageIn, MessageOut
from app.schemas.patients import PatientUpdate
from app.schemas.workout_log import WorkoutExerciseLogIn

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
    at: datetime | None = Form(None),
    weight_kg: float | None = Form(None),
    body_fat_pct: float | None = Form(None),
    waist_cm: float | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile | None = File(None),
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    attachment_url: str | None = None
    attachment_type: str | None = None
    if file is not None and file.filename:
        attachment_url, attachment_type = await save_upload(
            file, subfolder=f"measurements/{_user_id(current)}"
        )

    payload = {
        "at": at,
        "weight_kg": weight_kg,
        "body_fat_pct": body_fat_pct,
        "waist_cm": waist_cm,
        "notes": notes,
        "attachment_url": attachment_url,
        "attachment_type": attachment_type,
    }
    try:
        return await service.add_measurement(_user_id(current), payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/hydration", response_model=dict)
async def my_hydration(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.get_hydration(_user_id(current))


@router.post("/hydration", response_model=dict)
async def add_my_hydration(
    payload: dict[str, Any],
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    delta = payload.get("delta_ml")
    if not isinstance(delta, int):
        raise HTTPException(
            status_code=400, detail="delta_ml is required and must be an integer"
        )
    try:
        return await service.add_hydration(_user_id(current), delta)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/messages", response_model=list[MessageOut])
async def my_messages(
    since: datetime | None = Query(None),
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    messages = await service.list_messages(_user_id(current), since=since)
    return [MessageOut(**m) for m in messages]


@router.post("/messages", response_model=MessageOut, status_code=201)
async def send_my_message(
    payload: MessageIn,
    current=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    service: MeService = Depends(get_me_service),
):
    try:
        message = await service.send_message(
            _user_id(current),
            payload.text,
            attachment_url=payload.attachment_url,
            attachment_type=payload.attachment_type,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    patient = await service.get_my_patient_record(_user_id(current))
    owner_id = patient.get("owner_id") if patient else None
    if owner_id:
        tokens = [d["token"] async for d in db.devices.find({"user_id": owner_id}, {"token": 1, "_id": 0})]
        send_push_to_tokens(
            tokens,
            "Nuevo mensaje de tu paciente",
            payload.text[:120] or "Foto",
            {"type": "chat_message", "patientId": patient.get("id", "")},
        )

    return MessageOut(**message)


@router.post("/messages/attachment", response_model=dict)
async def upload_my_message_attachment(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    content_type = file.content_type or ""
    allowed = (
        content_type.startswith("image/")
        or content_type.startswith("video/")
        or content_type == "application/pdf"
    )
    if not allowed:
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen, video o PDF.")
    patient = await service.get_my_patient_record(_user_id(current))
    owner_id = patient.get("owner_id") if patient else None
    if not owner_id:
        raise HTTPException(status_code=404, detail="No tienes un nutriólogo asignado todavía")
    try:
        attachment_url, saved_content_type = await save_upload(
            file,
            subfolder=f"messaging/{owner_id}/{patient['id']}",
            max_size_bytes=25 * 1024 * 1024,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return {"attachment_url": attachment_url, "content_type": saved_content_type}


@router.post("/workout-logs/photo", response_model=dict)
async def upload_my_workout_log_photo(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    photo_url, content_type = await save_upload(
        file, subfolder=f"workout_logs/{_user_id(current)}"
    )
    return {"photo_url": photo_url, "content_type": content_type}


@router.get("/checkin-templates", response_model=list[FormTemplateOut])
async def my_checkin_templates(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.list_checkin_templates(_user_id(current))


@router.post("/checkin-responses", response_model=FormResponseOut, status_code=201)
async def submit_my_checkin_response(
    payload: FormResponseCreate,
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.submit_checkin_response(_user_id(current), payload.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/checkin-responses", response_model=list[FormResponseOut])
async def my_checkin_responses(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.list_checkin_responses(_user_id(current))


@router.get("/workout-plan/active", response_model=dict | None)
async def my_active_workout_plan(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.get_active_workout_plan(_user_id(current))


@router.get("/workout-logs", response_model=list[dict])
async def my_workout_logs(
    workout_plan_id: str | None = Query(None),
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.list_workout_logs(_user_id(current), workout_plan_id=workout_plan_id)


@router.put("/workout-logs/exercise", response_model=dict)
async def upsert_my_workout_log(
    payload: WorkoutExerciseLogIn,
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.upsert_workout_log(_user_id(current), payload)
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


@router.get("/articles", response_model=list[dict])
async def my_articles(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.list_articles(_user_id(current))
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


@router.get("/food_diary_entries", response_model=list[dict])
async def my_food_diary_entries(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
    limit: int = 50,
):
    return await service.list_food_diary_entries(_user_id(current), limit=limit)


@router.post("/food_diary_entries", response_model=dict, status_code=201)
async def add_food_diary_entry(
    payload: dict[str, Any],
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.add_food_diary_entry(_user_id(current), payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/recommendations", response_model=list[dict])
async def my_recommendations(
    kind: str | None = Query(None, pattern="^(supplement|brand)$"),
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    return await service.list_recommendations(_user_id(current), kind=kind)


@router.get("/clinical/history", response_model=dict)
async def my_clinical_history(
    current=Depends(get_current_user),
    service: MeService = Depends(get_me_service),
):
    try:
        return await service.get_clinical_history(_user_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
