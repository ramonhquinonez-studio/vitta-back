from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ..core.security import decode_access
from ..db import mongo

bearer = HTTPBearer(auto_error=True)

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        payload = decode_access(creds.credentials)
        return payload  # {"sub": user_id, "role": "...", "exp": ...}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

async def get_db():
    if mongo.db is None:
        await mongo.connect_to_mongo()
    return mongo.db
