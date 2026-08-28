from ..domain.repositories import UsersRepository


class UsersService:
    def __init__(self, repository: UsersRepository):
        self._repository = repository

    async def get_my_profile(self, user_id: str) -> dict:
        user = await self._repository.get_user(user_id)
        if not user:
            raise LookupError("User not found")
        return {
            "id": user["id"],
            "email": user.get("email"),
            "name": user.get("name"),
            "role": user.get("role") or "pro",
            "created_at": user.get("created_at"),
        }
