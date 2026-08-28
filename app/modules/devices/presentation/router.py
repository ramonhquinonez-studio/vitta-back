from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, get_db
from app.core.notify import send_push_to_tokens

from ..application.devices_service import DevicesService
from ..infrastructure.mongo_devices_repository import MongoDevicesRepository

router = APIRouter(prefix="/devices", tags=["devices"])


def get_devices_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> DevicesService:
    return DevicesService(MongoDevicesRepository(db))


def _user_id(current) -> str:
    user_id = current.get("sub") or current.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return user_id


@router.post("/register")
async def register_device(
    body: dict,
    current=Depends(get_current_user),
    service: DevicesService = Depends(get_devices_service),
):
    try:
        await service.register_device(
            user_id=_user_id(current),
            token=body.get("token") or "",
            platform=body.get("platform") or "unknown",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/test")
async def test_push(
    current=Depends(get_current_user),
    service: DevicesService = Depends(get_devices_service),
):
    tokens = await service.list_tokens_for_user(_user_id(current))
    if not tokens:
        raise HTTPException(status_code=404, detail="No tokens registered")
    send_push_to_tokens(tokens, "Test", "Esto es una notificación de prueba", {"type": "test"})
    return {"ok": True, "sent_to": len(tokens)}
