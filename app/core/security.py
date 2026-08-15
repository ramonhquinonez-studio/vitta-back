# app/core/security.py
import hashlib
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

# ---------- Password reset ----------
# Token sin estado: no requiere una colección en Mongo. Incluye un digest corto
# del password_hash actual; al resetear la contraseña ese hash cambia, así que
# el mismo token deja de ser válido automáticamente (uso único implícito).
RESET_PASSWORD_EXPIRE_MIN = 30


def _password_guard(password_hash: str) -> str:
    return hashlib.sha256((password_hash or "").encode("utf-8")).hexdigest()[:16]


def create_password_reset_token(user_id: str, password_hash: str) -> str:
    return _create_token(
        data={
            "sub": user_id,
            "type": "password_reset",
            "pwd_guard": _password_guard(password_hash),
        },
        secret=settings.JWT_SECRET,
        minutes=RESET_PASSWORD_EXPIRE_MIN,
    )


def decode_password_reset_token(token: str) -> dict:
    """Decodifica y valida la firma/expiración de un token de reset.
    No confirma por sí solo que siga "sin usar"; para eso ver `password_reset_guard_matches`."""
    data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    if data.get("type") != "password_reset":
        raise JWTError("Invalid token type")
    return data


def password_reset_guard_matches(payload: dict, current_password_hash: str) -> bool:
    """True si el token todavía es válido: la contraseña no ha cambiado desde
    que se emitió (uso único implícito, sin necesidad de una tabla de tokens)."""
    return payload.get("pwd_guard") == _password_guard(current_password_hash)

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