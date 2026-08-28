from datetime import datetime

from ..domain.entities import Message
from ..domain.repositories import MessagingRepository


class MessagingService:
    def __init__(self, repository: MessagingRepository):
        self._repository = repository

    async def list_for_thread(
        self, owner_id: str, patient_id: str, *, since: datetime | None = None
    ) -> list[Message]:
        if not await self._repository.patient_exists_for_owner(owner_id, patient_id):
            raise LookupError("Patient not found")
        return await self._repository.list_for_thread(owner_id, patient_id, since=since)

    async def ensure_patient_belongs_to_owner(self, owner_id: str, patient_id: str) -> None:
        """Raises LookupError if `patient_id` isn't owned by `owner_id` — used
        before an upload so a nutritionist can't stash a file under another
        nutritionist's patient_id before any message referencing it exists."""
        if not await self._repository.patient_exists_for_owner(owner_id, patient_id):
            raise LookupError("Patient not found")

    async def send_from_nutritionist(
        self,
        owner_id: str,
        patient_id: str,
        text: str,
        *,
        attachment_url: str | None = None,
        attachment_type: str | None = None,
    ) -> Message:
        text = text.strip()
        if not text and not attachment_url:
            raise ValueError("text or attachment_url is required")
        if not await self._repository.patient_exists_for_owner(owner_id, patient_id):
            raise LookupError("Patient not found")
        return await self._repository.create(
            owner_id,
            patient_id,
            sender_role="nutritionist",
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
        )
