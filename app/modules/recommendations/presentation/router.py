from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.schemas.recommendations import (
    RecommendationBulkCreate,
    RecommendationCreate,
    RecommendationOut,
    RecommendationUpdate,
)

from ..application.recommendations_service import RecommendationsService
from ..domain.entities import Recommendation
from ..infrastructure.mongo_recommendations_repository import MongoRecommendationsRepository


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendations_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RecommendationsService:
    return RecommendationsService(MongoRecommendationsRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _serialize(rec: Recommendation) -> dict:
    return {
        "id": rec.id,
        "kind": rec.kind,
        "title": rec.title,
        "subtitle": rec.subtitle,
        "category": rec.category,
        "brand": rec.brand,
        "description": rec.description,
        "benefits": rec.benefits,
        "usage": rec.usage,
        "notes": rec.notes,
        "price": rec.price,
        "rating": rec.rating,
        "emoji": rec.emoji,
    }


@router.get("", response_model=list[RecommendationOut])
async def list_my_recommendations(
    kind: str | None = Query(None, pattern="^(supplement|brand)$"),
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    items = await service.list_my_recommendations(_owner_id(current), kind=kind)
    return [_serialize(r) for r in items]


@router.post("", response_model=RecommendationOut, status_code=201)
async def create_recommendation(
    payload: RecommendationCreate,
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    try:
        rec = await service.create_recommendation(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(rec)


@router.post("/bulk", response_model=list[RecommendationOut], status_code=201)
async def create_recommendations_bulk(
    payload: RecommendationBulkCreate,
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    try:
        items = await service.create_bulk(
            _owner_id(current), [item.model_dump() for item in payload.items]
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_serialize(r) for r in items]


@router.patch("/{recommendation_id}", response_model=RecommendationOut)
async def update_recommendation(
    recommendation_id: str,
    payload: RecommendationUpdate,
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        rec = await service.update_recommendation(_owner_id(current), recommendation_id, updates)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(rec)


@router.delete("/{recommendation_id}")
async def delete_recommendation(
    recommendation_id: str,
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    try:
        await service.delete_recommendation(_owner_id(current), recommendation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}
