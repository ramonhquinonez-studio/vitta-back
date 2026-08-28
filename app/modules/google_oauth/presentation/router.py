from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.deps import get_current_user, get_db

from ..application.google_oauth_service import GoogleOAuthService
from ..infrastructure.mongo_google_oauth_repository import MongoGoogleOAuthRepository

router = APIRouter(prefix="/google", tags=["google"])


def get_google_oauth_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> GoogleOAuthService:
    return GoogleOAuthService(MongoGoogleOAuthRepository(db))


def _user_id(current) -> str:
    user_id = current.get("sub") or current.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return user_id


@router.post("/oauth/start_url")
async def oauth_start_url(
    current=Depends(get_current_user),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    # Endpoint AUTENTICADO: genera la URL de Google con state firmado
    return {"url": service.build_authorization_url(_user_id(current))}


@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    # NO requiere Authorization; se identifica por 'state'
    state = request.query_params.get("state")
    try:
        await service.handle_callback(
            authorization_response=str(request.url), state=state
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(settings.APP_OAUTH_SUCCESS_REDIRECT, status_code=302)


@router.get("/status")
async def google_status(
    current=Depends(get_current_user),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    return {"connected": await service.is_connected(_user_id(current))}


@router.delete("/disconnect")
async def google_disconnect(
    current=Depends(get_current_user),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    disconnected = await service.disconnect(_user_id(current))
    if not disconnected:
        return {"ok": True, "disconnected": True, "msg": "No tokens stored"}
    return {"ok": True, "disconnected": True}
