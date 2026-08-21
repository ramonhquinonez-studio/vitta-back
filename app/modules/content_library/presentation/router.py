from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.schemas.content_library import ArticleOut

from ..application.content_library_service import ContentLibraryService
from ..infrastructure.mongo_content_library_repository import MongoContentLibraryRepository

router = APIRouter(prefix="/content", tags=["content_library"])


def get_content_library_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ContentLibraryService:
    return ContentLibraryService(MongoContentLibraryRepository(db))


@router.get("/articles", response_model=list[ArticleOut])
async def list_articles(
    current=Depends(get_current_user),
    service: ContentLibraryService = Depends(get_content_library_service),
):
    return await service.list_articles()
