from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh,
    hash_password,
    verify_password,
)

from ..domain.entities import AuthTokens, AuthUser
from ..domain.repositories import AuthRepository


class AuthService:
    def __init__(self, repository: AuthRepository):
        self._repository = repository

    async def register(self, *, name: str, email: str, password: str) -> AuthUser:
        normalized_email = self._normalize_email(email)
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValueError("Name is required")

        existing = await self._repository.get_user_by_email(normalized_email)
        if existing is not None:
            raise FileExistsError("Email already registered")

        return await self._repository.create_user(
            name=normalized_name,
            email=normalized_email,
            password_hash=hash_password(password),
            role="user",
        )

    async def login(self, *, email: str, password: str) -> AuthTokens:
        normalized_email = self._normalize_email(email)
        user = await self._repository.get_user_by_email(normalized_email)
        if user is None or not verify_password(password, user.password_hash or ""):
            raise PermissionError("Invalid email or password")
        return self._issue_tokens(user.id, user.role)

    async def refresh(self, *, refresh_token: str) -> AuthTokens:
        try:
            data = decode_refresh(refresh_token)
        except JWTError as exc:
            raise PermissionError("Invalid token") from exc

        if data.get("type") != "refresh":
            raise PermissionError("Invalid token type")

        uid = data.get("sub")
        if not uid:
            raise PermissionError("Invalid token payload")

        role = data.get("role", "user")
        return self._issue_tokens(uid, role)

    def _issue_tokens(self, user_id: str, role: str) -> AuthTokens:
        return AuthTokens(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id, role),
        )

    def _normalize_email(self, email: str) -> str:
        normalized = (email or "").strip().lower()
        if not normalized:
            raise ValueError("Email is required")
        return normalized
