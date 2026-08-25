import unittest

from app.modules.billing.application.billing_service import BillingService
from app.modules.billing.domain.entities import Subscription, SubscriptionPlan


class _FakeBillingRepository:
    def __init__(self, plans: list[SubscriptionPlan] | None = None):
        self.plans = {p.id: p for p in (plans or [])}
        self.subscriptions: dict[str, Subscription] = {}

    async def list_plans(self):
        return list(self.plans.values())

    async def get_plan(self, plan_id):
        return self.plans.get(plan_id)

    async def get_default_plan(self):
        for plan in self.plans.values():
            if plan.is_default:
                return plan
        return None

    async def get_subscription_for_owner(self, owner_id):
        return self.subscriptions.get(owner_id)

    async def get_subscription_for_customer(self, provider_customer_id):
        for sub in self.subscriptions.values():
            if sub.provider_customer_id == provider_customer_id:
                return sub
        return None

    async def upsert_subscription(self, subscription):
        self.subscriptions[subscription.owner_id] = subscription
        return subscription


class _FakeBillingProvider:
    def __init__(self):
        self.checkout_calls = []
        self.portal_calls = []
        self.webhook_event: dict = {}

    async def create_checkout_session(self, *, owner_id, owner_email, plan):
        self.checkout_calls.append((owner_id, owner_email, plan.id))
        return f"https://mock/checkout/{plan.id}"

    async def create_portal_session(self, *, provider_customer_id):
        self.portal_calls.append(provider_customer_id)
        return f"https://mock/portal/{provider_customer_id}"

    def parse_webhook_event(self, *, payload, signature):
        return self.webhook_event


_FREE_PLAN = SubscriptionPlan(
    id="plan-free", name="Gratis", client_limit=3, stripe_price_id=None, is_default=True
)
_PRO_PLAN = SubscriptionPlan(
    id="plan-pro", name="Pro", client_limit=50, stripe_price_id="price_123", is_default=False
)


class BillingServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_my_subscription_enrolls_default_plan_when_none_exists(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN, _PRO_PLAN])
        service = BillingService(repo, _FakeBillingProvider())

        subscription = await service.get_my_subscription("owner-1")

        self.assertEqual(subscription.plan_id, "plan-free")
        self.assertEqual(subscription.status, "active")

    async def test_check_patient_quota_passes_under_the_limit(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN])
        service = BillingService(repo, _FakeBillingProvider())

        await service.check_patient_quota("owner-1", current_patient_count=2)

    async def test_check_patient_quota_raises_at_the_limit(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN])
        service = BillingService(repo, _FakeBillingProvider())

        with self.assertRaises(PermissionError):
            await service.check_patient_quota("owner-1", current_patient_count=3)

    async def test_check_patient_quota_falls_back_to_the_default_plan_when_canceled(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN, _PRO_PLAN])
        service = BillingService(repo, _FakeBillingProvider())
        await repo.upsert_subscription(
            Subscription(owner_id="owner-1", plan_id="plan-pro", status="canceled")
        )

        # Pro's limit (50) would pass, but a canceled subscription falls
        # back to the free plan's limit (3) instead of keeping Pro's forever.
        with self.assertRaises(PermissionError):
            await service.check_patient_quota("owner-1", current_patient_count=3)

    async def test_check_patient_quota_falls_back_to_the_default_plan_when_past_due(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN, _PRO_PLAN])
        service = BillingService(repo, _FakeBillingProvider())
        await repo.upsert_subscription(
            Subscription(owner_id="owner-1", plan_id="plan-pro", status="past_due")
        )

        with self.assertRaises(PermissionError):
            await service.check_patient_quota("owner-1", current_patient_count=3)

    async def test_check_patient_quota_uses_the_paid_plan_while_trialing(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN, _PRO_PLAN])
        service = BillingService(repo, _FakeBillingProvider())
        await repo.upsert_subscription(
            Subscription(owner_id="owner-1", plan_id="plan-pro", status="trialing")
        )

        # Under Pro's limit (50), well over Free's (3) — trialing counts as entitled.
        await service.check_patient_quota("owner-1", current_patient_count=10)

    async def test_check_patient_quota_reactivating_restores_the_paid_plan(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN, _PRO_PLAN])
        service = BillingService(repo, _FakeBillingProvider())
        await repo.upsert_subscription(
            Subscription(owner_id="owner-1", plan_id="plan-pro", status="active")
        )

        # plan_id was never touched while canceled, so reactivating (status
        # flips back to active) immediately restores Pro's real limit.
        await service.check_patient_quota("owner-1", current_patient_count=10)

    async def test_check_patient_quota_never_raises_for_an_unlimited_plan(self):
        unlimited = SubscriptionPlan(
            id="plan-unlimited", name="Unlimited", client_limit=None, stripe_price_id=None, is_default=True
        )
        repo = _FakeBillingRepository(plans=[unlimited])
        service = BillingService(repo, _FakeBillingProvider())

        await service.check_patient_quota("owner-1", current_patient_count=10_000)

    async def test_start_checkout_delegates_to_the_provider(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN, _PRO_PLAN])
        provider = _FakeBillingProvider()
        service = BillingService(repo, provider)

        url = await service.start_checkout("owner-1", "owner@example.com", "plan-pro")

        self.assertEqual(url, "https://mock/checkout/plan-pro")
        self.assertEqual(provider.checkout_calls, [("owner-1", "owner@example.com", "plan-pro")])

    async def test_start_checkout_rejects_an_unknown_plan(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN])
        service = BillingService(repo, _FakeBillingProvider())

        with self.assertRaises(LookupError):
            await service.start_checkout("owner-1", "owner@example.com", "plan-nope")

    async def test_open_portal_requires_an_existing_billing_customer(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN])
        service = BillingService(repo, _FakeBillingProvider())

        with self.assertRaises(ValueError):
            await service.open_portal("owner-1")

    async def test_handle_webhook_updates_subscription_status(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN, _PRO_PLAN])
        provider = _FakeBillingProvider()
        service = BillingService(repo, provider)
        await repo.upsert_subscription(
            Subscription(
                owner_id="owner-1",
                plan_id="plan-pro",
                status="active",
                provider_customer_id="cus_123",
            )
        )
        provider.webhook_event = {
            "type": "customer.subscription.updated",
            "customer_id": "cus_123",
            "subscription_id": "sub_123",
            "status": "past_due",
        }

        await service.handle_webhook(payload=b"{}", signature="sig")

        updated = await repo.get_subscription_for_owner("owner-1")
        self.assertEqual(updated.status, "past_due")
        self.assertEqual(updated.provider_subscription_id, "sub_123")

    async def test_handle_webhook_is_a_noop_for_an_unknown_customer(self):
        repo = _FakeBillingRepository(plans=[_FREE_PLAN])
        provider = _FakeBillingProvider()
        service = BillingService(repo, provider)
        provider.webhook_event = {
            "type": "customer.subscription.updated",
            "customer_id": "cus_unknown",
            "status": "past_due",
        }

        await service.handle_webhook(payload=b"{}", signature="sig")  # should not raise


if __name__ == "__main__":
    unittest.main()
