import unittest
from datetime import datetime, timedelta

from app.modules.booking_policy.application.enforcement import (
    BY_NUTRITIONIST,
    BY_PATIENT,
    FORFEIT,
    NO_CHARGE,
    REFUND,
    evaluate_cancellation,
    evaluate_reschedule,
)

_NOW = datetime(2026, 4, 1, 12, 0)


def _snap(**over):
    base = {
        "payment_mode": "deposit",
        "amount_due_cents": 24000,
        "amount_paid_cents": 24000,
        "cancellation_cutoff_hours": 24,
        "reschedule_limit": 1,
        "reschedule_notice_hours": 24,
    }
    base.update(over)
    return base


class CancellationTest(unittest.TestCase):
    def test_patient_before_cutoff_gets_a_full_refund(self):
        out = evaluate_cancellation(
            _snap(), start=_NOW + timedelta(hours=48), now=_NOW, by=BY_PATIENT
        )
        self.assertEqual(out["outcome"], REFUND)
        self.assertEqual(out["refund_cents"], 24000)
        self.assertEqual(out["status"], "canceled")

    def test_patient_inside_cutoff_forfeits(self):
        out = evaluate_cancellation(
            _snap(), start=_NOW + timedelta(hours=6), now=_NOW, by=BY_PATIENT
        )
        self.assertEqual(out["outcome"], FORFEIT)
        self.assertEqual(out["refund_cents"], 0)

    def test_free_booking_is_a_no_charge_cancel(self):
        out = evaluate_cancellation(
            _snap(payment_mode="none", amount_due_cents=0, amount_paid_cents=0),
            start=_NOW + timedelta(hours=2),
            now=_NOW,
            by=BY_PATIENT,
        )
        self.assertEqual(out["outcome"], NO_CHARGE)

    def test_nutritionist_cancel_always_refunds_in_full(self):
        out = evaluate_cancellation(
            _snap(), start=_NOW + timedelta(hours=3), now=_NOW, by=BY_NUTRITIONIST
        )
        self.assertEqual(out["outcome"], REFUND)
        self.assertEqual(out["refund_cents"], 24000)

    def test_no_show_forfeits_and_sets_status(self):
        out = evaluate_cancellation(
            _snap(),
            start=_NOW - timedelta(hours=1),
            now=_NOW,
            by=BY_NUTRITIONIST,
            is_no_show=True,
        )
        self.assertEqual(out["outcome"], FORFEIT)
        self.assertEqual(out["status"], "no_show")


class RescheduleTest(unittest.TestCase):
    def test_within_limit_and_notice_is_allowed(self):
        out = evaluate_reschedule(
            _snap(),
            start=_NOW + timedelta(hours=48),
            now=_NOW,
            reschedule_count=0,
            by=BY_PATIENT,
        )
        self.assertTrue(out["allowed"])

    def test_limit_reached_is_blocked(self):
        out = evaluate_reschedule(
            _snap(reschedule_limit=1),
            start=_NOW + timedelta(hours=48),
            now=_NOW,
            reschedule_count=1,
            by=BY_PATIENT,
        )
        self.assertFalse(out["allowed"])

    def test_too_close_to_start_is_blocked(self):
        out = evaluate_reschedule(
            _snap(reschedule_notice_hours=24),
            start=_NOW + timedelta(hours=6),
            now=_NOW,
            reschedule_count=0,
            by=BY_PATIENT,
        )
        self.assertFalse(out["allowed"])

    def test_zero_limit_blocks_all_patient_reschedules(self):
        out = evaluate_reschedule(
            _snap(reschedule_limit=0),
            start=_NOW + timedelta(days=5),
            now=_NOW,
            reschedule_count=0,
            by=BY_PATIENT,
        )
        self.assertFalse(out["allowed"])

    def test_nutritionist_reschedule_is_always_allowed(self):
        out = evaluate_reschedule(
            _snap(reschedule_limit=0),
            start=_NOW + timedelta(hours=1),
            now=_NOW,
            reschedule_count=9,
            by=BY_NUTRITIONIST,
        )
        self.assertTrue(out["allowed"])


if __name__ == "__main__":
    unittest.main()
