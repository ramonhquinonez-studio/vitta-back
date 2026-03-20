from typing import Protocol

from .entities import AuthUser


class AuthRepository(Protocol):
    async def get_user_by_email(self, email: str) -> AuthUser | None:
        ...

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        ...

    async def create_user(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> AuthUser:
        ...
