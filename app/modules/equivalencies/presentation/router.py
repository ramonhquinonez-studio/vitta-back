from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.schemas.equivalencies import (
    EquivalencyFoodCreate,
    EquivalencyFoodOut,
    EquivalencyGroupOut,
)

from ..application.equivalencies_service import EquivalenciesService
from ..infrastructure.mongo_equivalencies_repository import MongoEquivalenciesRepository

router = APIRouter(prefix="/equivalencies", tags=["equivalencies"])


def get_equivalencies_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> EquivalenciesService:
    return EquivalenciesService(MongoEquivalenciesRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


@router.get("/groups", response_model=list[EquivalencyGroupOut])
async def list_groups(
    current=Depends(get_current_user),
    service: EquivalenciesService = Depends(get_equivalencies_service),
):
    return await service.list_groups()


@router.get("/foods", response_model=list[EquivalencyFoodOut])
async def list_foods(
    group_id: str | None = Query(None),
    current=Depends(get_current_user),
    service: EquivalenciesService = Depends(get_equivalencies_service),
):
    return await service.list_foods(_owner_id(current), group_id=group_id)


@router.post("/foods", response_model=EquivalencyFoodOut, status_code=201)
async def create_food(
    payload: EquivalencyFoodCreate,
    current=Depends(get_current_user),
    service: EquivalenciesService = Depends(get_equivalencies_service),
):
    try:
        return await service.create_food(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/foods/{food_id}", status_code=204)
async def delete_food(
    food_id: str,
    current=Depends(get_current_user),
    service: EquivalenciesService = Depends(get_equivalencies_service),
):
    try:
        await service.delete_food(_owner_id(current), food_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
