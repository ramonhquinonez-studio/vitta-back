from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.config import settings
from app.db.mongo import get_db
from app.schemas.auth import (
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginIn,
    RefreshIn,
    RegisterIn,
    ResetPasswordIn,
    TokensOut,
)

from ..application.auth_service import AuthService
from ..infrastructure.mongo_auth_repository import MongoAuthRepository


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterOut(BaseModel):
    id: str
    email: str


def get_auth_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AuthService:
    return AuthService(MongoAuthRepository(db))


@router.post("/register", response_model=RegisterOut)
async def register(
    payload: RegisterIn,
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = await service.register(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            invite_code=payload.invite_code,
        )
    except FileExistsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RegisterOut(id=user.id, email=user.email)


@router.post("/login", response_model=TokensOut)
async def login(
    payload: LoginIn,
    service: AuthService = Depends(get_auth_service),
):
    try:
        tokens = await service.login(email=payload.email, password=payload.password)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return TokensOut(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/forgot-password", response_model=ForgotPasswordOut)
async def forgot_password(
    payload: ForgotPasswordIn,
    service: AuthService = Depends(get_auth_service),
):
    # Siempre responde igual exista o no el correo, para no filtrar qué
    # cuentas están registradas.
    token = await service.forgot_password(email=payload.email)
    message = "Si el correo existe, se enviaron instrucciones para restablecer la contraseña."

    # No hay integración de envío de correo todavía: fuera de local/dev el
    # token nunca viaja en la respuesta.
    exposed_token = token if settings.APP_ENV.lower() not in ("prod", "production", "staging") else None
    return ForgotPasswordOut(message=message, reset_token=exposed_token)


@router.post("/reset-password", response_model=dict)
async def reset_password(
    payload: ResetPasswordIn,
    service: AuthService = Depends(get_auth_service),
):
    try:
        await service.reset_password(token=payload.token, new_password=payload.new_password)
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/refresh", response_model=TokensOut)
async def refresh(
    payload: RefreshIn,
    service: AuthService = Depends(get_auth_service),
):
    try:
        tokens = await service.refresh(refresh_token=payload.refresh_token)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return TokensOut(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )
