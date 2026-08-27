import unittest
from datetime import datetime, timedelta

from app.modules.messaging.application.messaging_service import MessagingService
from app.modules.messaging.domain.entities import Message


class _FakeMessagingRepository:
    def __init__(self):
        self.messages: list[Message] = []
        self.owned_patients: set[tuple[str, str]] = {("owner-1", "patient-1")}
        self.sequence = 1

    async def list_for_thread(self, owner_id, patient_id, *, since=None):
        items = [
            m for m in self.messages if m.owner_id == owner_id and m.patient_id == patient_id
        ]
        if since is not None:
            items = [m for m in items if m.created_at > since]
        return items

    async def create(
        self, owner_id, patient_id, *, sender_role, text, attachment_url=None, attachment_type=None
    ):
        message = Message(
            id=str(self.sequence),
            owner_id=owner_id,
            patient_id=patient_id,
            sender_role=sender_role,
            text=text,
            created_at=datetime.utcnow(),
            attachment_url=attachment_url,
            attachment_type=attachment_type,
        )
        self.sequence += 1
        self.messages.append(message)
        return message

    async def patient_exists_for_owner(self, owner_id, patient_id):
        return (owner_id, patient_id) in self.owned_patients


class MessagingServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_send_from_nutritionist_creates_a_message(self):
        repo = _FakeMessagingRepository()
        service = MessagingService(repo)

        message = await service.send_from_nutritionist("owner-1", "patient-1", "Hola, ¿cómo vas?")

        self.assertEqual(message.sender_role, "nutritionist")
        self.assertEqual(message.text, "Hola, ¿cómo vas?")

    async def test_send_from_nutritionist_rejects_blank_text(self):
        repo = _FakeMessagingRepository()
        service = MessagingService(repo)

        with self.assertRaises(ValueError):
            await service.send_from_nutritionist("owner-1", "patient-1", "   ")

    async def test_send_from_nutritionist_allows_an_attachment_with_no_text(self):
        repo = _FakeMessagingRepository()
        service = MessagingService(repo)

        message = await service.send_from_nutritionist(
            "owner-1",
            "patient-1",
            "",
            attachment_url="/uploads/messaging/owner-1/patient-1/photo.jpg",
            attachment_type="image/jpeg",
        )

        self.assertEqual(message.text, "")
        self.assertEqual(message.attachment_url, "/uploads/messaging/owner-1/patient-1/photo.jpg")

    async def test_send_from_nutritionist_rejects_a_patient_not_owned(self):
        repo = _FakeMessagingRepository()
        service = MessagingService(repo)

        with self.assertRaises(LookupError):
            await service.send_from_nutritionist("owner-1", "patient-999", "hola")

    async def test_list_for_thread_rejects_a_patient_not_owned(self):
        repo = _FakeMessagingRepository()
        service = MessagingService(repo)

        with self.assertRaises(LookupError):
            await service.list_for_thread("owner-1", "patient-999")

    async def test_list_for_thread_returns_only_that_threads_messages(self):
        repo = _FakeMessagingRepository()
        repo.owned_patients.add(("owner-1", "patient-2"))
        service = MessagingService(repo)
        await service.send_from_nutritionist("owner-1", "patient-1", "para paciente 1")
        await service.send_from_nutritionist("owner-1", "patient-2", "para paciente 2")

        result = await service.list_for_thread("owner-1", "patient-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "para paciente 1")

    async def test_list_for_thread_filters_by_since(self):
        repo = _FakeMessagingRepository()
        service = MessagingService(repo)
        old_message = await repo.create("owner-1", "patient-1", sender_role="patient", text="viejo")
        old_message_backdated = Message(
            id=old_message.id,
            owner_id=old_message.owner_id,
            patient_id=old_message.patient_id,
            sender_role=old_message.sender_role,
            text=old_message.text,
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
        repo.messages[0] = old_message_backdated
        await service.send_from_nutritionist("owner-1", "patient-1", "nuevo")

        result = await service.list_for_thread(
            "owner-1", "patient-1", since=datetime.utcnow() - timedelta(minutes=1)
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "nuevo")


if __name__ == "__main__":
    unittest.main()
