# app/core/deps.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from jose import JWTError

from app.db.mongo import get_db as _get_db          # <- usamos la función correcta
from app.core.security import decode_access

# --- DB ---
def get_db() -> AsyncIOMotorDatabase:
    """
    Reexport de la DB actual. Evita acceder a un atributo 'db' inexistente.
    """
    return _get_db()

# --- Auth (opcional, por si lo usas en tus routers protegidos) ---
bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = creds.credentials
    try:
        data = decode_access(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await db.users.find_one({"_id": ObjectId(uid)}) if ObjectId.is_valid(uid) else None
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # puedes devolver el doc completo o una versión mínima
    return {"id": str(user["_id"]), "email": user["email"], "role": user.get("role", "user")}


def require_role(*roles: str):
    """Dependency factory gating a route to one or more account roles (e.g.
    "nutritionist"). `get_current_user` already decodes `role` from every
    JWT, but until now nothing checked it — every "owner-scoped" route just
    trusted whatever id was in the token, so a patient-role account could
    technically call nutritionist-only endpoints. Apply as
    `Depends(require_role("nutritionist"))` alongside `get_current_user`.
    """

    async def _check(current: dict = Depends(get_current_user)) -> dict:
        if current.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Not allowed for this account role")
        return current

    return _check
