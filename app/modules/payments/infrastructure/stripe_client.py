"""Single place that hands out the configured `stripe` module.

Services take the module as a constructor argument (never import it
directly) so tests can inject a fake — the same pattern `fidelity_back`
uses via `PaymentsServiceDeps.stripe`.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings


def get_stripe() -> Any:
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def as_dict(obj: Any) -> Any:
    """Normalize a Stripe SDK return value to a plain, recursively-plain
    dict. The real `StripeObject` (SDK v15) raises `AttributeError` on
    `.get()` and other dict methods — but every payments service treats
    responses as dicts (matching how `FakeStripe` returns them). Call this
    on whatever `stripe.X.create()/retrieve()/modify()` and
    `Webhook.construct_event()` hand back, before the service touches it.
    """
    if isinstance(obj, dict):
        return {k: as_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [as_dict(v) for v in obj]
    to_dict = getattr(type(obj), "to_dict", None)
    if callable(to_dict) and not isinstance(obj, type):
        try:
            return as_dict(obj.to_dict())
        except Exception:
            pass
    return obj
