from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str
    name: str | None = None
    role: str = "user"
    password_hash: str | None = None


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
