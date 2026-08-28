from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, get_db

from ..application.users_service import UsersService
from ..infrastructure.mongo_users_repository import MongoUsersRepository

router = APIRouter(prefix="/users", tags=["users"])


def get_users_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> UsersService:
    return UsersService(MongoUsersRepository(db))


def _user_id(current) -> str:
    user_id = current.get("sub") or current.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return user_id


@router.get("/me", response_model=Dict[str, Any])
async def me(
    current=Depends(get_current_user),
    service: UsersService = Depends(get_users_service),
):
    try:
        return await service.get_my_profile(_user_id(current))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
