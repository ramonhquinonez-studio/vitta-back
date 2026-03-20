# app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from passlib.exc import UnknownHashError
from typing import List, Optional, Dict
import firebase_admin
from firebase_admin import credentials, messaging


_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return _pwd.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    if not hashed or not isinstance(hashed, str):
        return False
    try:
        return _pwd.verify(plain, hashed)
    except UnknownHashError:
        return False

def _create_token(*, data: dict, secret: str, minutes: int | None = None, days: int | None = None) -> str:
    now = datetime.now(tz=timezone.utc)
    to_encode = {**data, "iat": now}
    if minutes is not None:
        to_encode["exp"] = now + timedelta(minutes=minutes)
    if days is not None:
        to_encode["exp"] = now + timedelta(days=days)
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALG)

def create_access_token(user_id: str, role: str = "user") -> str:
    return _create_token(
        data={"sub": user_id, "type": "access", "role": role},
        secret=settings.JWT_SECRET,
        minutes=settings.JWT_EXPIRE_MIN,
    )

def create_refresh_token(user_id: str, role: str = "user") -> str:
    return _create_token(
        data={"sub": user_id, "type": "refresh", "role": role},
        secret=settings.JWT_REFRESH_SECRET,
        days=settings.JWT_REFRESH_EXPIRE_DAYS,
    )

# ---------- NUEVO: decodificadores ----------
def decode_access(token: str) -> dict:
    """Decodifica un access token y devuelve el payload (lanza JWTError si es inválido)."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])

def decode_refresh(token: str) -> dict:
    """Decodifica un refresh token y devuelve el payload (lanza JWTError si es inválido)."""
    return jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALG])

_app = None

def init_firebase():
    global _app
    if _app is None:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _app = firebase_admin.initialize_app(cred)

def send_push_to_tokens(
    tokens: List[str], title: str, body: str, data: Optional[Dict[str,str]] = None
):
    if not tokens:
        return None
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k:str(v) for k,v in (data or {}).items()},
        tokens=tokens,
    )
    return messaging.send_multicast(message)