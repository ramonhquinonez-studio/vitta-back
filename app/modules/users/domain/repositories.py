from typing import Protocol


class UsersRepository(Protocol):
    async def get_user(self, user_id: str) -> dict | None:
        ...
