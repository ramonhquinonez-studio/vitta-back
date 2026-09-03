from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.schemas.eating_out_options import (
    EatingOutOptionCreate,
    EatingOutOptionOut,
    EatingOutOptionUpdate,
)

from ..application.eating_out_options_service import EatingOutOptionsService
from ..domain.entities import EatingOutOption
from ..infrastructure.mongo_eating_out_options_repository import (
    MongoEatingOutOptionsRepository,
)


router = APIRouter(
    prefix="/eating-out-options",
    tags=["eating_out_options"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_eating_out_options_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> EatingOutOptionsService:
    return EatingOutOptionsService(MongoEatingOutOptionsRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _serialize(option: EatingOutOption) -> dict:
    return {
        "id": option.id,
        "restaurant": option.restaurant,
        "dish": option.dish,
        "kcal": option.kcal,
        "protein": option.protein,
        "carbs": option.carbs,
        "fat": option.fat,
    }


@router.get("", response_model=list[EatingOutOptionOut])
async def list_my_options(
    current=Depends(get_current_user),
    service: EatingOutOptionsService = Depends(get_eating_out_options_service),
):
    items = await service.list_my_options(_owner_id(current))
    return [_serialize(o) for o in items]


@router.post("", response_model=EatingOutOptionOut, status_code=201)
async def create_option(
    payload: EatingOutOptionCreate,
    current=Depends(get_current_user),
    service: EatingOutOptionsService = Depends(get_eating_out_options_service),
):
    try:
        option = await service.create_option(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(option)


@router.patch("/{option_id}", response_model=EatingOutOptionOut)
async def update_option(
    option_id: str,
    payload: EatingOutOptionUpdate,
    current=Depends(get_current_user),
    service: EatingOutOptionsService = Depends(get_eating_out_options_service),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        option = await service.update_option(_owner_id(current), option_id, updates)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(option)


@router.delete("/{option_id}")
async def delete_option(
    option_id: str,
    current=Depends(get_current_user),
    service: EatingOutOptionsService = Depends(get_eating_out_options_service),
):
    try:
        await service.delete_option(_owner_id(current), option_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}
