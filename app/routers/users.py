from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Any, Dict, Optional

from ..core.deps import get_db, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

def _uid_from_current(current: Dict[str, Any]) -> ObjectId:
    uid = current.get("sub") or current.get("id")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    try:
        return ObjectId(uid)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user id")

def _serialize_user(u: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(u["_id"]),
        "email": u.get("email"),
        "name": u.get("name"),
        "role": u.get("role", "pro"),
        "created_at": u.get("created_at"),
    }

@router.get("/me", response_model=Dict[str, Any])
async def me(
    current = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    uid = _uid_from_current(current)
    user = await db.users.find_one({"_id": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user(user)
