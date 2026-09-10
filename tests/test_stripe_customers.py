import unittest

from app.modules.payments.application.stripe_customers import StripeCustomers
from tests._fakes.fake_stripe import FakeStripe


class _FakeRepo:
    def __init__(self):
        self._map: dict[str, str] = {}

    async def get_customer_id(self, user_id):
        return self._map.get(user_id)

    async def set_customer_id(self, user_id, customer_id):
        self._map[user_id] = customer_id


class StripeCustomersTest(unittest.IsolatedAsyncioTestCase):
    async def test_ensure_customer_creates_once_and_reuses(self):
        stripe = FakeStripe()
        repo = _FakeRepo()
        customers = StripeCustomers(stripe, repo)

        first = await customers.ensure_customer("user-1", email="a@b.com")
        second = await customers.ensure_customer("user-1", email="a@b.com")

        self.assertEqual(first, second)
        self.assertEqual(len(stripe._customers), 1)

    async def test_ensure_customer_isolated_per_user(self):
        customers = StripeCustomers(FakeStripe(), _FakeRepo())
        a = await customers.ensure_customer("user-1")
        b = await customers.ensure_customer("user-2")
        self.assertNotEqual(a, b)

    async def test_ephemeral_key_secret(self):
        customers = StripeCustomers(FakeStripe(), _FakeRepo())
        cid = await customers.ensure_customer("user-1")
        secret = customers.ephemeral_key_secret(cid)
        self.assertTrue(secret.startswith("ek_secret_"))

    async def test_stripe_error_maps_to_http_502(self):
        stripe = FakeStripe()
        stripe.raise_on["Customer.create"] = FakeStripe.error.StripeError("boom")
        customers = StripeCustomers(stripe, _FakeRepo())
        with self.assertRaises(Exception) as ctx:
            await customers.ensure_customer("user-1")
        self.assertEqual(getattr(ctx.exception, "status_code", None), 502)


if __name__ == "__main__":
    unittest.main()
