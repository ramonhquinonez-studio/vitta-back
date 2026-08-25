from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.schemas.checkin import FormTemplateCreate, FormTemplateOut

from ..application.checkin_service import CheckinService
from ..infrastructure.mongo_checkin_repository import MongoCheckinRepository

router = APIRouter(
    prefix="/checkin",
    tags=["checkin"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_checkin_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> CheckinService:
    return CheckinService(MongoCheckinRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


@router.post("/templates", response_model=FormTemplateOut, status_code=201)
async def create_template(
    payload: FormTemplateCreate,
    current=Depends(get_current_user),
    service: CheckinService = Depends(get_checkin_service),
):
    try:
        return await service.create_template(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/templates", response_model=list[FormTemplateOut])
async def list_templates(
    include_archived: bool = Query(False),
    current=Depends(get_current_user),
    service: CheckinService = Depends(get_checkin_service),
):
    return await service.list_templates(_owner_id(current), include_archived=include_archived)


@router.get("/templates/{template_id}", response_model=FormTemplateOut)
async def get_template(
    template_id: str,
    current=Depends(get_current_user),
    service: CheckinService = Depends(get_checkin_service),
):
    try:
        return await service.get_template(_owner_id(current), template_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/templates/{template_id}", response_model=FormTemplateOut)
async def update_template(
    template_id: str,
    payload: FormTemplateCreate,
    current=Depends(get_current_user),
    service: CheckinService = Depends(get_checkin_service),
):
    try:
        return await service.update_template(_owner_id(current), template_id, payload.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/templates/{template_id}", status_code=204)
async def archive_template(
    template_id: str,
    current=Depends(get_current_user),
    service: CheckinService = Depends(get_checkin_service),
):
    try:
        await service.archive_template(_owner_id(current), template_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
