import json
import unittest

from app.modules.stripe_webhooks.application.webhook_dispatcher import (
    WebhookDispatcher,
    register_handler,
)
from tests._fakes.fake_stripe import FakeStripe


class _FakeEventsRepo:
    def __init__(self):
        self.seen: set[str] = set()
        self.done: dict[str, bool] = {}

    async def mark_processing(self, event_id, event_type):
        if event_id in self.seen:
            return False
        self.seen.add(event_id)
        return True

    async def mark_done(self, event_id, *, ok=True, note=None):
        self.done[event_id] = ok


SECRET = "whsec_test"


def _dispatcher(events):
    return WebhookDispatcher(FakeStripe(), SECRET, events)


def _signed(event: dict):
    payload = json.dumps(event).encode()
    return payload, f"sig_{SECRET}"


class StripeWebhookIdempotencyTest(unittest.IsolatedAsyncioTestCase):
    async def test_bad_signature_is_400(self):
        dispatcher = _dispatcher(_FakeEventsRepo())
        with self.assertRaises(Exception) as ctx:
            dispatcher.verify(payload=b"{}", signature="wrong")
        self.assertEqual(getattr(ctx.exception, "status_code", None), 400)

    async def test_event_processed_exactly_once(self):
        events = _FakeEventsRepo()
        calls: list[str] = []

        async def handler(obj):
            calls.append(obj["id"])

        register_handler("test.event.once", handler)
        dispatcher = _dispatcher(events)

        event = {"id": "evt_1", "type": "test.event.once", "data": {"object": {"id": "obj_1"}}}
        payload, sig = _signed(event)

        first = await dispatcher.dispatch(dispatcher.verify(payload=payload, signature=sig))
        second = await dispatcher.dispatch(dispatcher.verify(payload=payload, signature=sig))

        self.assertEqual(calls, ["obj_1"])  # handler ran once
        self.assertNotIn("duplicate", first)
        self.assertTrue(second["duplicate"])

    async def test_unregistered_type_is_acked(self):
        dispatcher = _dispatcher(_FakeEventsRepo())
        event = {"id": "evt_2", "type": "nobody.listens", "data": {"object": {}}}
        payload, sig = _signed(event)
        result = await dispatcher.dispatch(dispatcher.verify(payload=payload, signature=sig))
        self.assertEqual(result, {"ok": True, "handled": 0})

    async def test_handler_failure_marks_error_and_reraises(self):
        events = _FakeEventsRepo()

        async def boom(obj):
            raise RuntimeError("kaboom")

        register_handler("test.event.boom", boom)
        dispatcher = _dispatcher(events)
        event = {"id": "evt_3", "type": "test.event.boom", "data": {"object": {}}}
        payload, sig = _signed(event)

        with self.assertRaises(RuntimeError):
            await dispatcher.dispatch(dispatcher.verify(payload=payload, signature=sig))
        self.assertFalse(events.done["evt_3"])


if __name__ == "__main__":
    unittest.main()
