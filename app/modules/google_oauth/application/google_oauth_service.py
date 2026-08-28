from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

from ..domain.repositories import GoogleOAuthRepository
from ..infrastructure.google_oauth_client import GoogleOAuthClient

_STATE_AUD = "google_oauth"
_STATE_TTL_MIN = 10


class GoogleOAuthService:
    def __init__(self, repository: GoogleOAuthRepository, client: GoogleOAuthClient | None = None):
        self._repository = repository
        self._client = client or GoogleOAuthClient()

    def _make_state_token(self, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "aud": _STATE_AUD,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=_STATE_TTL_MIN)).timestamp()),
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

    def _decode_state_token(self, state: str) -> str:
        try:
            payload = jwt.decode(
                state, settings.JWT_SECRET, algorithms=[settings.JWT_ALG], audience=_STATE_AUD
            )
            sub = payload.get("sub")
            if not sub:
                raise JWTError("no sub")
            return sub
        except JWTError as exc:
            raise ValueError(f"Invalid state: {exc}") from exc

    def build_authorization_url(self, user_id: str) -> str:
        state = self._make_state_token(user_id)
        return self._client.build_authorization_url(state=state)

    async def handle_callback(self, *, authorization_response: str, state: str | None) -> None:
        if not state:
            raise ValueError("Missing state")
        user_id = self._decode_state_token(state)
        credentials = self._client.fetch_credentials(authorization_response=authorization_response)
        await self._repository.save_tokens(
            user_id,
            {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_type": "Bearer",
                "expiry": credentials.expiry,
                "scope": " ".join(settings.GOOGLE_SCOPES),
                "updated_at": datetime.now(timezone.utc),
            },
        )

    async def is_connected(self, user_id: str) -> bool:
        return bool(await self._repository.get_tokens(user_id))

    async def disconnect(self, user_id: str) -> bool:
        tokens = await self._repository.delete_tokens(user_id)
        if tokens is None:
            return False
        for key in ("refresh_token", "access_token"):
            token = tokens.get(key)
            if token:
                self._client.revoke(token)
        return True
