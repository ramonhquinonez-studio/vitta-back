from ..domain.repositories import DevicesRepository


class DevicesService:
    def __init__(self, repository: DevicesRepository):
        self._repository = repository

    async def register_device(self, *, user_id: str, token: str, platform: str) -> None:
        token = token.strip()
        if not token:
            raise ValueError("token required")
        platform = (platform or "unknown").strip()
        await self._repository.register_device(user_id=user_id, token=token, platform=platform)

    async def list_tokens_for_user(self, user_id: str) -> list[str]:
        return await self._repository.list_tokens_for_user(user_id)
