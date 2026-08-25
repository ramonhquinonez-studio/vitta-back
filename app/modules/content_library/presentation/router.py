from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, require_role
from app.db.mongo import get_db
from app.schemas.content_library import ArticleIn, ArticleOut, ArticleUpdate

from ..application.content_library_service import ContentLibraryService
from ..infrastructure.mongo_content_library_repository import MongoContentLibraryRepository

router = APIRouter(prefix="/content", tags=["content_library"])


def get_content_library_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ContentLibraryService:
    return ContentLibraryService(MongoContentLibraryRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


@router.get("/articles", response_model=list[ArticleOut])
async def list_articles(
    current=Depends(get_current_user),
    service: ContentLibraryService = Depends(get_content_library_service),
):
    return await service.list_articles()


@router.get("/articles/mine", response_model=list[ArticleOut])
async def list_my_articles(
    current=Depends(require_role("nutritionist")),
    service: ContentLibraryService = Depends(get_content_library_service),
):
    return await service.list_my_articles(_owner_id(current))


@router.post("/articles", response_model=ArticleOut, status_code=201)
async def create_article(
    payload: ArticleIn,
    current=Depends(require_role("nutritionist")),
    service: ContentLibraryService = Depends(get_content_library_service),
):
    try:
        return await service.create(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/articles/{article_id}", response_model=ArticleOut)
async def update_article(
    article_id: str,
    payload: ArticleUpdate,
    current=Depends(require_role("nutritionist")),
    service: ContentLibraryService = Depends(get_content_library_service),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        return await service.update(_owner_id(current), article_id, updates)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: str,
    current=Depends(require_role("nutritionist")),
    service: ContentLibraryService = Depends(get_content_library_service),
):
    try:
        await service.delete(_owner_id(current), article_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}
