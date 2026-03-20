import os
from typing import List, Optional, Dict
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings

_app = None

def init_firebase():
    global _app
    if _app is None:
        if not settings.FIREBASE_CREDENTIALS_PATH:
            return None
        if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            return None
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _app = firebase_admin.initialize_app(cred)
    return _app

def send_push_to_tokens(
    tokens: List[str], title: str, body: str, data: Optional[Dict[str,str]] = None
):
    if _app is None:
        return None
    if not tokens:
        return None
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k:str(v) for k,v in (data or {}).items()},
        tokens=tokens,
    )
    return messaging.send_multicast(message)
