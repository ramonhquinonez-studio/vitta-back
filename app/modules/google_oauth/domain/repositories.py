from typing import Protocol


class GoogleOAuthRepository(Protocol):
    async def get_tokens(self, user_id: str) -> dict | None:
        ...

    async def save_tokens(self, user_id: str, tokens: dict) -> None:
        ...

    async def delete_tokens(self, user_id: str) -> dict | None:
        """Deletes and returns the stored tokens doc (or None if nothing was
        stored) — the caller needs the token values back to revoke them with
        Google before they're gone from our own DB."""
        ...
