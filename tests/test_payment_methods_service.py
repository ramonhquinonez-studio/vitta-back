import unittest

from app.modules.payment_methods.application.payment_methods_service import (
    PaymentMethodsService,
)
from app.modules.payments.application.stripe_customers import StripeCustomers
from tests._fakes.fake_stripe import FakeStripe


class _FakeRepo:
    def __init__(self):
        self._map: dict[str, str] = {}

    async def get_customer_id(self, user_id):
        return self._map.get(user_id)

    async def set_customer_id(self, user_id, customer_id):
        self._map[user_id] = customer_id


def _service(stripe: FakeStripe):
    customers = StripeCustomers(stripe, _FakeRepo())
    return PaymentMethodsService(stripe, customers), customers


class PaymentMethodsServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_add_first_card_becomes_default_and_lists(self):
        stripe = FakeStripe()
        service, customers = _service(stripe)
        cid = await customers.ensure_customer("user-1")
        pm_id = stripe.add_card_fixture(cid)  # exists in Stripe, not yet attached

        added = await service.add_card("user-1", pm_id)
        self.assertTrue(added.is_default)
        self.assertEqual(added.last4, "4242")

        cards = await service.list_cards("user-1")
        self.assertEqual([c.id for c in cards], [pm_id])
        self.assertTrue(cards[0].is_default)

    async def test_second_card_is_not_default(self):
        stripe = FakeStripe()
        service, customers = _service(stripe)
        cid = await customers.ensure_customer("user-1")
        first = stripe.add_card_fixture(cid)
        second = stripe.add_card_fixture(cid)

        await service.add_card("user-1", first)
        added2 = await service.add_card("user-1", second)
        self.assertFalse(added2.is_default)

    async def test_set_default_moves_the_flag(self):
        stripe = FakeStripe()
        service, customers = _service(stripe)
        cid = await customers.ensure_customer("user-1")
        first = stripe.add_card_fixture(cid)
        second = stripe.add_card_fixture(cid)
        await service.add_card("user-1", first)
        await service.add_card("user-1", second)

        await service.set_default("user-1", second)

        cards = {c.id: c.is_default for c in await service.list_cards("user-1")}
        self.assertFalse(cards[first])
        self.assertTrue(cards[second])

    async def test_delete_card_removes_it(self):
        stripe = FakeStripe()
        service, customers = _service(stripe)
        cid = await customers.ensure_customer("user-1")
        pm_id = stripe.add_card_fixture(cid)
        await service.add_card("user-1", pm_id)

        await service.delete_card("user-1", pm_id)

        self.assertEqual(await service.list_cards("user-1"), [])

    async def test_cannot_touch_another_users_card(self):
        stripe = FakeStripe()
        service, customers = _service(stripe)
        other_cid = await customers.ensure_customer("user-2")
        pm_id = stripe.add_card_fixture(other_cid)
        await service.add_card("user-2", pm_id)

        await customers.ensure_customer("user-1")
        with self.assertRaises(Exception) as ctx:
            await service.delete_card("user-1", pm_id)
        self.assertEqual(getattr(ctx.exception, "status_code", None), 404)

    async def test_card_error_maps_to_409(self):
        stripe = FakeStripe()
        stripe.raise_on["PaymentMethod.attach"] = FakeStripe.error.CardError("declined")
        service, customers = _service(stripe)
        cid = await customers.ensure_customer("user-1")
        with self.assertRaises(Exception) as ctx:
            await service.add_card("user-1", "pm_x")
        self.assertEqual(getattr(ctx.exception, "status_code", None), 409)


if __name__ == "__main__":
    unittest.main()
