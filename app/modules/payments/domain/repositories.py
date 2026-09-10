from __future__ import annotations

from typing import Protocol


class StripeCustomersRepository(Protocol):
    async def get_customer_id(self, user_id: str) -> str | None: ...

    async def set_customer_id(self, user_id: str, customer_id: str) -> None: ...
