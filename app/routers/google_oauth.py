from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GRequest
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from jose import jwt, JWTError
import requests

from app.core.config import settings
from app.core.deps import get_db, get_current_user

router = APIRouter(prefix="/google", tags=["google"])

STATE_AUD = "google_oauth"
STATE_TTL_MIN = 10

def _flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.GOOGLE_SCOPES,
    )

def _make_state_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "aud": STATE_AUD,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=STATE_TTL_MIN)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def _decode_state_token(state: str) -> str:
    try:
        payload = jwt.decode(state, settings.JWT_SECRET, algorithms=[settings.JWT_ALG], audience=STATE_AUD)
        sub = payload.get("sub")
        if not sub:
            raise JWTError("no sub")
        return sub
    except JWTError as e:
        raise HTTPException(status_code=400, detail=f"Invalid state: {e}")

@router.post("/oauth/start_url")
async def oauth_start_url(current=Depends(get_current_user)):
    # Endpoint AUTENTICADO: genera la URL de Google con state firmado
    flow = _flow()
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    user_id = (current.get("sub") or current.get("id"))
    state = _make_state_token(user_id)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return {"url": auth_url}

@router.get("/oauth/callback")
async def oauth_callback(request: Request, db=Depends(get_db)):
    # NO requiere Authorization; se identifica por 'state'
    # Extrae state de la query para saber el user_id
    qs = dict(request.query_params)
    state = qs.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Missing state")
    user_sub = _decode_state_token(state)
    uid = ObjectId(user_sub)

    flow = _flow()
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    # Usa la URL completa para fetch_token (tiene 'code' y 'state')
    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials

    doc = {
        "user_id": uid,
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_type": "Bearer",
        "expiry": creds.expiry,
        "scope": " ".join(settings.GOOGLE_SCOPES),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.google_tokens.update_one({"user_id": uid}, {"$set": doc}, upsert=True)

    # Puedes redirigir a una página “ok” o devolver un JSON simple
    # Aquí devolvemos una página mínima para cerrar el navegador manualmente
    return RedirectResponse(settings.APP_OAUTH_SUCCESS_REDIRECT, status_code=302)

@router.get("/status")
async def google_status(current=Depends(get_current_user), db=Depends(get_db)):
    uid = ObjectId(current.get("sub") or current.get("id"))
    t = await db.google_tokens.find_one({"user_id": uid})
    return {"connected": bool(t)}


@router.delete("/disconnect")
async def google_disconnect(current=Depends(get_current_user), db=Depends(get_db)):
    uid = ObjectId(current.get("sub") or current.get("id"))
    doc = await db.google_tokens.find_one({"user_id": uid})
    if not doc:
        return {"ok": True, "disconnected": True, "msg": "No tokens stored"}

    # Revocar en Google (intenta con refresh y access)
    try:
        for tok_key in ("refresh_token", "access_token"):
            tok = doc.get(tok_key)
            if tok:
                # https://oauth2.googleapis.com/revoke?token=...
                requests.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": tok},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    timeout=5,
                )
    except Exception:
        # No interrumpas por errores de red
        pass

    # Borra tokens en tu DB
    await db.google_tokens.delete_one({"user_id": uid})
    return {"ok": True, "disconnected": True}