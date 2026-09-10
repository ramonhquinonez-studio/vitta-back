"""Maps `stripe` SDK exceptions to `HTTPException`s with a short,
user-safe Spanish message — never a raw stack or a card-network detail.
Mirrors `fidelity_back`'s `_stripe_error_detail`.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

_GENERIC = "No se pudo procesar el pago. Intenta de nuevo."


def stripe_error_to_http(exc: Any) -> HTTPException:
    name = type(exc).__name__
    # A declined / invalid card is a client-actionable 409; anything else
    # from Stripe is an upstream failure (502).
    status = 409 if name in ("CardError", "InvalidRequestError") else 502

    message = _GENERIC
    user_message = getattr(exc, "user_message", None)
    if isinstance(user_message, str) and user_message.strip():
        message = user_message.strip()
    else:
        err = getattr(exc, "error", None)
        err_message = getattr(err, "message", None) if err is not None else None
        if isinstance(err_message, str) and err_message.strip():
            message = err_message.strip()

    return HTTPException(status_code=status, detail=message)
