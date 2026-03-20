from datetime import datetime, timezone
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.core.config import settings

def build_creds(doc: Dict[str, Any]) -> Credentials:
    return Credentials(
        token=doc["access_token"],
        refresh_token=doc.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES,
        expiry=doc.get("expiry"),
    )

def calendar_service(creds: Credentials):
    return build("calendar", "v3", credentials=creds, cache_discovery=False)

def event_payload(*, summary: str, description: str|None, start: datetime, end: datetime, online: bool):
    # Google espera RFC3339 con timezone/UTC
    def iso(dt: datetime) -> dict:
        # puedes usar .isoformat(); aquí dejamos explícito UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return {"dateTime": dt.astimezone(timezone.utc).isoformat(), "timeZone": "UTC"}

    ev = {
        "summary": summary,
        "description": description,
        "start": iso(start),
        "end": iso(end),
    }
    if online:
        ev["conferenceData"] = {"createRequest": {"requestId": f"meet-{int(start.timestamp())}"}}
    return ev
