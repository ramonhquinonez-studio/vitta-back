from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.core.deps import get_db, get_current_user

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/register")
async def register_device(
    body: dict, db: AsyncIOMotorDatabase = Depends(get_db), current=Depends(get_current_user)
):
    token = (body.get("token") or "").strip()
    platform = (body.get("platform") or "unknown").strip()  # ios|android|web
    if not token:
        raise HTTPException(status_code=422, detail="token required")
    uid = ObjectId(current.get("sub") or current.get("id"))
    now = datetime.utcnow()
    await db.devices.update_one(
        {"user_id": uid, "token": token},
        {"$set": {"platform": platform, "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True
    )
    return {"ok": True}

@router.post("/test")
async def test_push(
    db: AsyncIOMotorDatabase = Depends(get_db), current=Depends(get_current_user)
):
    from app.core.notify import send_push_to_tokens
    uid = ObjectId(current.get("sub") or current.get("id"))
    tokens = [d["token"] async for d in db.devices.find({"user_id": uid}, {"token":1, "_id":0})]
    if not tokens:
        raise HTTPException(status_code=404, detail="No tokens registered")
    send_push_to_tokens(tokens, "Test", "Esto es una notificación de prueba", {"type":"test"})
    return {"ok": True, "sent_to": len(tokens)}
