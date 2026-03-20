from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.db.mongo import get_db
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokensOut

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
        )
    except FileExistsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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
