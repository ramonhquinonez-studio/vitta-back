from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from ..core.deps import get_current_user
from ..db import mongo
from ..schemas.users import UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
async def me(current=Depends(get_current_user)):
    # Asegura conexión (por si alguien llama sin startup)
    if mongo.db is None:
        await mongo.connect_to_mongo()

    user_id = current["sub"]
    user = await mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user.get("role", "nutritionist")
    )
