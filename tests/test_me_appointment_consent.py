import unittest
from datetime import UTC, datetime, timedelta

from app.modules.booking_policy.application.booking_policy_service import BookingPolicyService
from app.modules.booking_policy.domain.entities import BookingPolicy
from app.modules.me.application.me_service import MeService


class _FakePolicyRepo:
    def __init__(self, policy: BookingPolicy | None):
        self.policy = policy

    async def get_for_owner(self, owner_id):
        return self.policy

    async def upsert_for_owner(self, policy):
        self.policy = policy
        return policy


class _FakeMeRepo:
    def __init__(self, session_price=800.0):
        self.session_price = session_price
        self.created = None

    async def get_patient_for_user(self, user_id):
        return {"id": "patient-1", "owner_id": "owner-1"}

    async def get_nutritionist_profile(self, owner_id):
        return {"session_price": self.session_price, "session_price_currency": "MXN"}

    async def find_owner_overlap(self, owner_id, *, start, end, exclude_appointment_id=None):
        return None

    async def create_patient_appointment(self, **kwargs):
        self.created = kwargs
        return {"id": "appt-1", "status": "pending", **kwargs}


def _service(policy: BookingPolicy | None):
    return MeService(
        _FakeMeRepo(),
        booking_policy_service=BookingPolicyService(_FakePolicyRepo(policy)),
    )


def _payload(**extra):
    start = datetime.now(UTC) + timedelta(days=2)
    return {"start": start.isoformat(), "mode": "online", **extra}


class MeAppointmentConsentTest(unittest.IsolatedAsyncioTestCase):
    async def test_no_policy_books_without_consent_field(self):
        service = _service(None)
        result = await service.request_appointment("user-1", _payload())
        self.assertEqual(result["status"], "pending")
        self.assertIsNone(service._repository.created.get("policy_snapshot"))

    async def test_none_mode_needs_no_consent(self):
        service = _service(BookingPolicy(owner_id="owner-1", payment_mode="none"))
        await service.request_appointment("user-1", _payload())
        self.assertIsNone(service._repository.created.get("policy_snapshot"))

    async def test_deposit_policy_rejects_missing_consent(self):
        service = _service(BookingPolicy(owner_id="owner-1", payment_mode="deposit"))
        with self.assertRaises(ValueError):
            await service.request_appointment("user-1", _payload())
        with self.assertRaises(ValueError):
            await service.request_appointment("user-1", _payload(policy_accepted=False))

    async def test_deposit_policy_snapshots_on_consent(self):
        service = _service(BookingPolicy(owner_id="owner-1", payment_mode="deposit", deposit_value=25))
        await service.request_appointment("user-1", _payload(policy_accepted=True))
        created = service._repository.created
        snap = created["policy_snapshot"]
        self.assertEqual(snap["payment_mode"], "deposit")
        self.assertEqual(snap["amount_due_cents"], 20000)  # 25% of 800
        self.assertIsInstance(created["policy_accepted_at"], datetime)

    async def test_requires_approval_alone_needs_consent(self):
        service = _service(BookingPolicy(owner_id="owner-1", requires_approval=True))
        with self.assertRaises(ValueError):
            await service.request_appointment("user-1", _payload())
        await service.request_appointment("user-1", _payload(policy_accepted=True))
        self.assertIsNotNone(service._repository.created["policy_snapshot"])

    async def test_get_booking_policy_returns_resolved(self):
        service = _service(BookingPolicy(owner_id="owner-1", payment_mode="full"))
        resolved = await service.get_booking_policy("user-1")
        self.assertEqual(resolved["amount_due_cents"], 80000)
