from fastapi import APIRouter
from ..core.config import settings

router = APIRouter(tags=["health"])

@router.get("/healthz")
async def healthz():
    return {"status": "ok"}

@router.get("/version")
async def version():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "env": settings.APP_ENV}
