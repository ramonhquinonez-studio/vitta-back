"""Verifies the Stripe signature, de-dupes by event id, and fans the
event out to whichever module registered a handler for its type. `078`
(subscriptions) and `079` (Connect / consultation payments) each register
their handlers at import time via `register_handler(...)`.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import HTTPException

from app.modules.payments.infrastructure.stripe_client import as_dict

Handler = Callable[[dict], Awaitable[None]]

_HANDLERS: dict[str, list[Handler]] = {}


def register_handler(event_type: str, handler: Handler) -> None:
    handlers = _HANDLERS.setdefault(event_type, [])
    if handler not in handlers:  # idempotent — safe to call at import time
        handlers.append(handler)


def _handlers_for(event_type: str) -> list[Handler]:
    return list(_HANDLERS.get(event_type, ()))


class WebhookDispatcher:
    def __init__(self, stripe: Any, webhook_secret: str, events_repo: Any):
        self._stripe = stripe
        self._secret = webhook_secret
        self._events = events_repo

    def verify(self, *, payload: bytes, signature: str | None) -> dict:
        if not self._secret:
            raise HTTPException(status_code=503, detail="Webhooks no configurados")
        try:
            event = self._stripe.Webhook.construct_event(payload, signature, self._secret)
        except Exception as exc:  # SignatureVerificationError / ValueError
            raise HTTPException(status_code=400, detail=f"Invalid webhook: {exc}") from exc
        # The real SDK returns a StripeObject (no .get()); our dispatch/handlers
        # treat the event as a plain dict.
        return as_dict(event)

    async def dispatch(self, event: dict) -> dict:
        event_id = event.get("id")
        event_type = event.get("type", "")
        if not event_id:
            raise HTTPException(status_code=400, detail="Missing Stripe event id")

        if not await self._events.mark_processing(event_id, event_type):
            return {"ok": True, "duplicate": True}

        handlers = _handlers_for(event_type)
        try:
            data_object = (event.get("data") or {}).get("object") or {}
            for handler in handlers:
                await handler(data_object)
        except Exception as exc:
            await self._events.mark_done(event_id, ok=False, note=str(exc))
            raise

        await self._events.mark_done(event_id, ok=True)
        return {"ok": True, "handled": len(handlers)}
