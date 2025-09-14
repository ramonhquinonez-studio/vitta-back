from fastapi import APIRouter, HTTPException, status
from ..db import mongo
from ..schemas.auth import RegisterIn, LoginIn, TokenPair
from ..core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(payload: RegisterIn):
    # defensa extra por si alguien llama sin haber conectado
    if mongo.db is None:
        await mongo.connect_to_mongo()

    user = await  mongo.db.users.find_one({"email": payload.email})
    if user:
        raise HTTPException(status_code=409, detail="Email already registered")
    doc = {
        "name": payload.name,
        "email": payload.email,
        "password": hash_password(payload.password),
        "role": "nutritionist",
    }
    res = await mongo.db.users.insert_one(doc)
    return {"ok": True, "id": str(res.inserted_id)}


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginIn):
    if mongo.db is None:
        await mongo.connect_to_mongo()

    user = await mongo.db.users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    role = user.get("role", "nutritionist")
    access = create_access_token(str(user["_id"]), role)
    refresh = create_refresh_token(str(user["_id"]), role)
    return TokenPair(access=access, refresh=refresh)

@router.post("/refresh", response_model=TokenPair)
async def refresh_token(refresh: str):
    payload = None
    try:
        payload = decode_refresh(refresh)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    role = payload.get("role", "nutritionist")
    access = create_access_token(payload["sub"], role)
    new_refresh = create_refresh_token(payload["sub"], role)
    return TokenPair(access=access, refresh=new_refresh)

@router.post("/logout")
async def logout():
    return {"ok": True}
