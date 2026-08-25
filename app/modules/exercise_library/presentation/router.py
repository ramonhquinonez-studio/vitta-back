from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.schemas.exercise_library import ExerciseLibraryItemCreate, ExerciseLibraryItemOut

from ..application.exercise_library_service import ExerciseLibraryService
from ..infrastructure.mongo_exercise_library_repository import MongoExerciseLibraryRepository

router = APIRouter(
    prefix="/exercise-library",
    tags=["exercise_library"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_exercise_library_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ExerciseLibraryService:
    return ExerciseLibraryService(MongoExerciseLibraryRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


@router.get("", response_model=list[ExerciseLibraryItemOut])
async def list_exercise_library(
    current=Depends(get_current_user),
    service: ExerciseLibraryService = Depends(get_exercise_library_service),
):
    return await service.list_items(_owner_id(current))


@router.post("", response_model=ExerciseLibraryItemOut, status_code=201)
async def create_exercise_library_item(
    payload: ExerciseLibraryItemCreate,
    current=Depends(get_current_user),
    service: ExerciseLibraryService = Depends(get_exercise_library_service),
):
    try:
        return await service.create_item(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{item_id}", status_code=204)
async def delete_exercise_library_item(
    item_id: str,
    current=Depends(get_current_user),
    service: ExerciseLibraryService = Depends(get_exercise_library_service),
):
    try:
        await service.delete_item(_owner_id(current), item_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
