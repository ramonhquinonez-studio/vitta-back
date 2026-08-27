from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.core.storage import save_upload
from app.db.mongo import get_db
from app.schemas.workout_plan import WorkoutPlanCreate, WorkoutPlanOut, WorkoutPlanUpdate

_MAX_VIDEO_SIZE_BYTES = 150 * 1024 * 1024

from ..application.workout_plans_service import WorkoutPlansService
from ..infrastructure.mongo_workout_plans_repository import MongoWorkoutPlansRepository

router = APIRouter(
    prefix="/workout-plans",
    tags=["workout_plans"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_workout_plans_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> WorkoutPlansService:
    return WorkoutPlansService(MongoWorkoutPlansRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


@router.post("/exercise-media", response_model=dict)
async def upload_exercise_media(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
):
    owner_id = _owner_id(current)
    content_type = file.content_type or ""
    is_photo = content_type.startswith("image/")
    is_video = content_type.startswith("video/")
    if not (is_photo or is_video):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen o video.")
    try:
        url, saved_content_type = await save_upload(
            file,
            subfolder=f"workout_plans/{owner_id}/media",
            max_size_bytes=_MAX_VIDEO_SIZE_BYTES,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return {
        "url": url,
        "media_type": "photo" if is_photo else "video",
        "content_type": saved_content_type,
    }


@router.post("", response_model=WorkoutPlanOut, status_code=201)
async def create_workout_plan(
    payload: WorkoutPlanCreate,
    current=Depends(get_current_user),
    service: WorkoutPlansService = Depends(get_workout_plans_service),
):
    try:
        return await service.create_plan(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[WorkoutPlanOut])
async def list_workout_plans(
    current=Depends(get_current_user),
    service: WorkoutPlansService = Depends(get_workout_plans_service),
):
    return await service.list_plans(_owner_id(current))


@router.get("/{plan_id}", response_model=WorkoutPlanOut)
async def get_workout_plan(
    plan_id: str,
    current=Depends(get_current_user),
    service: WorkoutPlansService = Depends(get_workout_plans_service),
):
    try:
        return await service.get_plan(_owner_id(current), plan_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{plan_id}", response_model=WorkoutPlanOut)
async def update_workout_plan(
    plan_id: str,
    payload: WorkoutPlanUpdate,
    current=Depends(get_current_user),
    service: WorkoutPlansService = Depends(get_workout_plans_service),
):
    updates = {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None
    }
    try:
        return await service.update_plan(_owner_id(current), plan_id, updates)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{plan_id}", status_code=204)
async def delete_workout_plan(
    plan_id: str,
    current=Depends(get_current_user),
    service: WorkoutPlansService = Depends(get_workout_plans_service),
):
    try:
        await service.delete_plan(_owner_id(current), plan_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return None


@router.post("/{plan_id}/assign")
async def assign_workout_plan(
    plan_id: str,
    body: dict = Body(...),
    current=Depends(get_current_user),
    service: WorkoutPlansService = Depends(get_workout_plans_service),
):
    patient_id = body.get("patient_id") or body.get("patientId")
    try:
        return await service.assign_plan(_owner_id(current), plan_id, patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422 if "patient_id" in str(exc) else 400, detail=str(exc)
        ) from exc
