from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.schemas.recommendations import (
    RecommendationAssignmentsOut,
    RecommendationAssignRequest,
    RecommendationBulkCreate,
    RecommendationCreate,
    RecommendationOut,
    RecommendationUpdate,
)

from ..application.recommendations_service import RecommendationsService
from ..domain.entities import Recommendation
from ..infrastructure.mongo_recommendations_repository import MongoRecommendationsRepository


router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
    dependencies=[Depends(require_role("nutritionist"))],
)


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
        "owner_id": rec.owner_id,
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
        "equivalency_group_id": rec.equivalency_group_id,
    }


@router.get("", response_model=list[RecommendationOut])
async def list_my_recommendations(
    kind: str | None = Query(None, pattern="^(supplement|brand)$"),
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    items = await service.list_my_recommendations(_owner_id(current), kind=kind)
    return [_serialize(r) for r in items]


@router.get("/platform", response_model=list[RecommendationOut])
async def list_platform_recommendations(
    kind: str | None = Query(None, pattern="^(supplement|brand)$"),
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    """Platform-curated recommendations (`owner_id: None`) — the "Biblioteca
    pública" tab. A nutritionist copies one into their own list (via the
    regular POST) before assigning it to patients."""
    items = await service.list_platform_recommendations(kind=kind)
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


@router.post("/{recommendation_id}/assign")
async def assign_recommendation(
    recommendation_id: str,
    payload: RecommendationAssignRequest,
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    try:
        count = await service.assign_to_patients(
            _owner_id(current), recommendation_id, payload.patient_ids
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"assigned": count}


@router.delete("/{recommendation_id}/assign/{patient_id}")
async def unassign_recommendation(
    recommendation_id: str,
    patient_id: str,
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    try:
        await service.unassign_from_patient(_owner_id(current), recommendation_id, patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/{recommendation_id}/assignments", response_model=RecommendationAssignmentsOut)
async def list_recommendation_assignments(
    recommendation_id: str,
    current=Depends(get_current_user),
    service: RecommendationsService = Depends(get_recommendations_service),
):
    patient_ids = await service.list_assignments(_owner_id(current), recommendation_id)
    return {"patient_ids": patient_ids}
