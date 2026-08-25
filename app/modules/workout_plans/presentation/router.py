from fastapi import APIRouter, Body, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.schemas.workout_plan import WorkoutPlanCreate, WorkoutPlanOut, WorkoutPlanUpdate

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
