from typing import Protocol


class DevicesRepository(Protocol):
    async def register_device(self, *, user_id: str, token: str, platform: str) -> None:
        ...

    async def list_tokens_for_user(self, user_id: str) -> list[str]:
        ...
