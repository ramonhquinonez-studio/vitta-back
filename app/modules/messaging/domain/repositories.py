from datetime import datetime
from typing import Protocol

from .entities import Message


class MessagingRepository(Protocol):
    async def list_for_thread(
        self, owner_id: str, patient_id: str, *, since: datetime | None = None
    ) -> list[Message]:
        ...

    async def create(
        self,
        owner_id: str,
        patient_id: str,
        *,
        sender_role: str,
        text: str,
        attachment_url: str | None = None,
        attachment_type: str | None = None,
    ) -> Message:
        ...

    async def patient_exists_for_owner(self, owner_id: str, patient_id: str) -> bool:
        ...
