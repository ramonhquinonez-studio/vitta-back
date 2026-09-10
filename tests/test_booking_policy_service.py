import unittest

from app.modules.booking_policy.application.booking_policy_service import BookingPolicyService
from app.modules.booking_policy.domain.entities import BookingPolicy


class _FakeRepo:
    def __init__(self, stored: BookingPolicy | None = None):
        self.stored = stored

    async def get_for_owner(self, owner_id):
        return self.stored

    async def upsert_for_owner(self, policy):
        self.stored = policy
        return policy


class BookingPolicyServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_returns_defaults_when_unsaved(self):
        service = BookingPolicyService(_FakeRepo())
        policy = await service.get_for_owner("owner-1")
        self.assertEqual(policy.payment_mode, "none")
        self.assertEqual(policy.deposit_value, 30.0)
        self.assertEqual(policy.reschedule_limit, 1)
        self.assertFalse(policy.needs_consent)

    async def test_upsert_persists_and_validates(self):
        repo = _FakeRepo()
        service = BookingPolicyService(repo)
        saved = await service.upsert_for_owner(
            "owner-1",
            {"payment_mode": "deposit", "deposit_value": 25, "reschedule_limit": 2},
        )
        self.assertEqual(saved.payment_mode, "deposit")
        self.assertEqual(saved.deposit_value, 25)
        self.assertTrue(saved.needs_consent)
        self.assertIsNotNone(saved.updated_at)
        self.assertIs(repo.stored, saved)

    async def test_upsert_rejects_bad_values(self):
        service = BookingPolicyService(_FakeRepo())
        for bad in (
            {"payment_mode": "sometimes"},
            {"deposit_type": "percentage", "deposit_value": 150},
            {"deposit_type": "fixed", "deposit_value": 0},
            {"reschedule_limit": -5},
            {"cancellation_cutoff_hours": -1},
            {"slot_hold_minutes": 3},
            {"slot_hold_minutes": 300},
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    await service.upsert_for_owner("owner-1", bad)

    async def test_resolve_percentage_deposit(self):
        service = BookingPolicyService(_FakeRepo())
        policy = BookingPolicy(owner_id="o", payment_mode="deposit", deposit_value=30)
        resolved = service.resolve_for_patient(policy, session_price=800.0, currency="MXN")
        self.assertEqual(resolved["amount_due_cents"], 24000)
        self.assertEqual(resolved["currency"], "MXN")
        self.assertTrue(resolved["needs_consent"])
        self.assertIn("depósito", resolved["policy_text"].lower())

    async def test_resolve_fixed_deposit_capped_at_price(self):
        service = BookingPolicyService(_FakeRepo())
        policy = BookingPolicy(
            owner_id="o", payment_mode="deposit", deposit_type="fixed", deposit_value=500
        )
        self.assertEqual(
            service.resolve_for_patient(policy, session_price=800.0, currency="MXN")["amount_due_cents"],
            50000,
        )
        # deposit larger than the price → capped
        self.assertEqual(
            service.resolve_for_patient(policy, session_price=300.0, currency="MXN")["amount_due_cents"],
            30000,
        )

    async def test_resolve_full_prepay(self):
        service = BookingPolicyService(_FakeRepo())
        policy = BookingPolicy(owner_id="o", payment_mode="full")
        resolved = service.resolve_for_patient(policy, session_price=650.0, currency="MXN")
        self.assertEqual(resolved["amount_due_cents"], 65000)
        self.assertIn("total", resolved["policy_text"].lower())

    async def test_resolve_none_or_no_price_is_zero_due(self):
        service = BookingPolicyService(_FakeRepo())
        none_policy = BookingPolicy(owner_id="o")
        self.assertEqual(
            service.resolve_for_patient(none_policy, session_price=800.0, currency="MXN")["amount_due_cents"],
            0,
        )
        deposit_no_price = BookingPolicy(owner_id="o", payment_mode="deposit")
        r = service.resolve_for_patient(deposit_no_price, session_price=None, currency="MXN")
        self.assertEqual(r["amount_due_cents"], 0)
        self.assertTrue(r["needs_consent"])  # still needs consent — a deposit is owed

    async def test_custom_policy_text_wins_over_auto(self):
        service = BookingPolicyService(_FakeRepo())
        policy = BookingPolicy(owner_id="o", payment_mode="deposit", policy_text="Mi política.")
        resolved = service.resolve_for_patient(policy, session_price=800.0, currency="MXN")
        self.assertEqual(resolved["policy_text"], "Mi política.")

    async def test_auto_text_covers_approval_and_reschedule_limit(self):
        service = BookingPolicyService(_FakeRepo())
        policy = BookingPolicy(
            owner_id="o",
            payment_mode="deposit",
            requires_approval=True,
            reschedule_limit=0,
        )
        text = service.resolve_for_patient(policy, session_price=800.0, currency="MXN")["policy_text"]
        self.assertIn("confirme", text)
        self.assertIn("No se permite reprogramar", text)
