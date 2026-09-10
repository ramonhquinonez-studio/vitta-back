import unittest

from app.modules.billing.application import subscription_webhook_handlers as wh
from app.modules.billing.application.stripe_subscriptions_service import (
    StripeSubscriptionsService,
)
from app.modules.billing.domain.entities import Subscription, SubscriptionPlan
from app.modules.payments.application.stripe_customers import StripeCustomers
from tests._fakes.fake_stripe import FakeStripe

FREE = SubscriptionPlan(id="p_free", name="Gratis", client_limit=3, stripe_price_id=None, is_default=True)
PRO = SubscriptionPlan(id="p_pro", name="Pro", client_limit=None, stripe_price_id="price_pro", is_default=False)
PLUS = SubscriptionPlan(id="p_plus", name="Plus", client_limit=20, stripe_price_id="price_plus", is_default=False)


class _FakeBillingRepo:
    def __init__(self, plans):
        self.plans = {p.id: p for p in plans}
        self.subs: dict[str, Subscription] = {}

    async def list_plans(self):
        return list(self.plans.values())

    async def get_plan(self, plan_id):
        return self.plans.get(plan_id)

    async def get_default_plan(self):
        return next((p for p in self.plans.values() if p.is_default), None)

    async def get_subscription_for_owner(self, owner_id):
        return self.subs.get(owner_id)

    async def get_subscription_for_customer(self, customer_id):
        return next((s for s in self.subs.values() if s.provider_customer_id == customer_id), None)

    async def upsert_subscription(self, subscription):
        self.subs[subscription.owner_id] = subscription
        return subscription


class _FakeCustomersRepo:
    def __init__(self):
        self._m = {}

    async def get_customer_id(self, user_id):
        return self._m.get(user_id)

    async def set_customer_id(self, user_id, customer_id):
        self._m[user_id] = customer_id


def _service(stripe, repo):
    customers = StripeCustomers(stripe, _FakeCustomersRepo())
    return StripeSubscriptionsService(repo, stripe, customers)


class SubscriptionSheetTest(unittest.IsolatedAsyncioTestCase):
    async def test_free_plan_enrolls_without_stripe_call(self):
        stripe = FakeStripe()
        repo = _FakeBillingRepo([FREE, PRO])
        out = await _service(stripe, repo).start_subscription_sheet("owner-1", "a@b.com", "p_free")
        self.assertEqual(out["status"], "active")
        self.assertEqual(out["payment_intent_client_secret"], "")
        self.assertEqual(len(stripe._subscriptions), 0)
        self.assertEqual(repo.subs["owner-1"].plan_id, "p_free")

    async def test_paid_plan_returns_confirmable_client_secret(self):
        stripe = FakeStripe()  # default: incomplete + requires_payment_method
        repo = _FakeBillingRepo([FREE, PRO])
        out = await _service(stripe, repo).start_subscription_sheet("owner-1", "a@b.com", "p_pro")
        self.assertTrue(out["subscription_id"].startswith("sub_"))
        self.assertTrue(out["payment_intent_client_secret"].startswith("pi_secret_"))
        self.assertTrue(out["ephemeral_key_secret"])
        self.assertEqual(out["status"], "incomplete")
        row = repo.subs["owner-1"]
        self.assertEqual(row.plan_id, "p_pro")
        self.assertEqual(row.provider_subscription_id, out["subscription_id"])

    async def test_client_secret_from_confirmation_secret_on_newer_api(self):
        # Current Stripe API: latest_invoice has no `payment_intent`, only
        # `confirmation_secret` — the sheet must still get a client secret.
        stripe = FakeStripe()
        stripe.omit_payment_intent = True
        repo = _FakeBillingRepo([FREE, PRO])
        out = await _service(stripe, repo).start_subscription_sheet("owner-1", "a@b.com", "p_pro")
        self.assertTrue(out["payment_intent_client_secret"].startswith("pi_secret_"))

    async def test_plan_change_modifies_the_existing_subscription(self):
        stripe = FakeStripe()
        repo = _FakeBillingRepo([FREE, PRO, PLUS])
        svc = _service(stripe, repo)
        first = await svc.start_subscription_sheet("owner-1", "a@b.com", "p_pro")
        stripe.subscription_status = "active"
        stripe.pi_status = "succeeded"
        # simulate the first sub now active
        repo.subs["owner-1"] = Subscription(
            owner_id="owner-1", plan_id="p_pro", status="active",
            provider_customer_id="cus_1", provider_subscription_id=first["subscription_id"],
        )

        second = await svc.start_subscription_sheet("owner-1", "a@b.com", "p_plus")

        self.assertEqual(second["subscription_id"], first["subscription_id"])  # modified, not new
        self.assertEqual(repo.subs["owner-1"].plan_id, "p_plus")

    async def test_verify_reconciles_status(self):
        stripe = FakeStripe()
        repo = _FakeBillingRepo([FREE, PRO])
        svc = _service(stripe, repo)
        out = await svc.start_subscription_sheet("owner-1", "a@b.com", "p_pro")
        # client confirmed the PI; Stripe now says active
        stripe._subscriptions[out["subscription_id"]]["status"] = "active"

        verified = await svc.verify_subscription("owner-1", out["subscription_id"])
        self.assertEqual(verified["status"], "active")
        self.assertEqual(repo.subs["owner-1"].status, "active")

    async def test_verify_rejects_unknown_subscription(self):
        repo = _FakeBillingRepo([FREE, PRO])
        with self.assertRaises(LookupError):
            await _service(FakeStripe(), repo).verify_subscription("owner-1", "sub_nope")


class SubscriptionWebhookApplyTest(unittest.IsolatedAsyncioTestCase):
    def _repo_with_pro(self):
        repo = _FakeBillingRepo([FREE, PRO, PLUS])
        repo.subs["owner-1"] = Subscription(
            owner_id="owner-1", plan_id="p_pro", status="incomplete",
            provider_customer_id="cus_1", provider_subscription_id="sub_1",
        )
        return repo

    async def test_invoice_paid_activates(self):
        repo = self._repo_with_pro()
        await wh.apply_invoice_paid(repo, {"customer": "cus_1"})
        self.assertEqual(repo.subs["owner-1"].status, "active")

    async def test_invoice_payment_failed_sets_past_due(self):
        repo = self._repo_with_pro()
        await wh.apply_invoice_payment_failed(repo, {"customer": "cus_1"})
        self.assertEqual(repo.subs["owner-1"].status, "past_due")

    async def test_subscription_deleted_cancels(self):
        repo = self._repo_with_pro()
        await wh.apply_subscription_deleted(repo, {"customer": "cus_1"})
        self.assertEqual(repo.subs["owner-1"].status, "canceled")

    async def test_subscription_updated_resolves_new_plan_from_price(self):
        repo = self._repo_with_pro()
        await wh.apply_subscription_updated(repo, {
            "id": "sub_1",
            "customer": "cus_1",
            "status": "active",
            "items": {"data": [{"price": {"id": "price_plus"}, "current_period_end": 1_900_000_000}]},
        })
        self.assertEqual(repo.subs["owner-1"].plan_id, "p_plus")
        self.assertEqual(repo.subs["owner-1"].status, "active")

    async def test_unknown_customer_is_a_noop(self):
        repo = self._repo_with_pro()
        await wh.apply_invoice_paid(repo, {"customer": "cus_other"})
        self.assertEqual(repo.subs["owner-1"].status, "incomplete")


if __name__ == "__main__":
    unittest.main()
