from __future__ import annotations

from typing import Protocol

from .entities import BookingPolicy


class BookingPolicyRepository(Protocol):
    async def get_for_owner(self, owner_id: str) -> BookingPolicy | None: ...

    async def upsert_for_owner(self, policy: BookingPolicy) -> BookingPolicy: ...
