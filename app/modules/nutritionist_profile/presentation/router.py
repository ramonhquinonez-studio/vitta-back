from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.core.storage import save_upload
from app.db.mongo import get_db
from app.schemas.nutritionist_profile import NutritionistProfileOut, NutritionistProfileUpdate

from ..application.nutritionist_profile_service import NutritionistProfileService
from ..infrastructure.mongo_nutritionist_profile_repository import MongoNutritionistProfileRepository


router = APIRouter(
    prefix="/nutritionist_profile",
    tags=["nutritionist_profile"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_nutritionist_profile_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> NutritionistProfileService:
    return NutritionistProfileService(MongoNutritionistProfileRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


@router.get("/me", response_model=NutritionistProfileOut)
async def my_nutritionist_profile(
    current=Depends(get_current_user),
    service: NutritionistProfileService = Depends(get_nutritionist_profile_service),
):
    return await service.get_my_profile(_owner_id(current))


@router.patch("/me", response_model=NutritionistProfileOut)
async def update_my_nutritionist_profile(
    payload: NutritionistProfileUpdate,
    current=Depends(get_current_user),
    service: NutritionistProfileService = Depends(get_nutritionist_profile_service),
):
    updates = {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None
    }
    try:
        return await service.update_my_profile(_owner_id(current), updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/me/complete-onboarding", response_model=NutritionistProfileOut)
async def complete_my_onboarding(
    current=Depends(get_current_user),
    service: NutritionistProfileService = Depends(get_nutritionist_profile_service),
):
    return await service.complete_onboarding(_owner_id(current))


@router.post("/me/logo", response_model=NutritionistProfileOut)
async def upload_my_logo(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    service: NutritionistProfileService = Depends(get_nutritionist_profile_service),
):
    owner_id = _owner_id(current)
    logo_url, _content_type = await save_upload(file, subfolder=f"nutritionist_profile/{owner_id}")
    try:
        return await service.update_my_profile(owner_id, {"logo_url": logo_url})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
