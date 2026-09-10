"""Patient → nutritionist charge for a consultation. `fidelity_back`'s
`init_payment_sheet` shape (Customer + ephemeral key + PaymentIntent +
credential dict + `/verify`), plus Connect: `application_fee_amount` +
`transfer_data.destination`.

Collaborators are injected as callables so the service stays free of the
consultations / nutritionist_profile / patients modules and is unit
testable.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import HTTPException

from app.core.config import settings

from .errors import stripe_error_to_http
from .stripe_customers import StripeCustomers
from ..domain.payment_entities import Payment
from ..infrastructure.stripe_client import as_dict

# (price, currency) — price in the profile's own units (e.g. MXN), not cents.
PriceResolver = Callable[[str], Awaitable[tuple[float | None, str]]]
# owner_id, consultation_id -> {"patient_id": ..., "appointment_id": ...} | None
ConsultationResolver = Callable[[str, str], Awaitable[dict | None]]
# user_id -> {"id": patient_id, "owner_id": nutritionist_id} | None
PatientResolver = Callable[[str], Awaitable[dict | None]]


def _fee_cents(amount_cents: int) -> int:
    return round(amount_cents * settings.PLATFORM_FEE_BPS / 10_000)


class ConsultationChargesService:
    def __init__(
        self,
        stripe: Any,
        customers: StripeCustomers,
        payments_repo: Any,
        *,
        get_patient_for_user: PatientResolver,
        get_consultation: ConsultationResolver,
        get_session_price: PriceResolver,
    ):
        self._stripe = stripe
        self._customers = customers
        self._repo = payments_repo
        self._get_patient = get_patient_for_user
        self._get_consultation = get_consultation
        self._get_price = get_session_price

    async def create_sheet(self, user_id: str, consultation_id: str, *, email: str | None) -> dict:
        patient = await self._get_patient(user_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        nutritionist_id = patient.get("owner_id") or ""
        patient_id = patient.get("id") or ""

        consultation = await self._get_consultation(nutritionist_id, consultation_id)
        if not consultation or consultation.get("patient_id") != patient_id:
            raise HTTPException(status_code=404, detail="Consulta no encontrada")

        # Already paid? Nothing to do — surface it, don't double-charge.
        for p in await self._repo.list_for_patient(patient_id):
            if p.consultation_id == consultation_id and p.status == "paid":
                raise HTTPException(status_code=409, detail="Esta consulta ya fue pagada.")

        account = await self._repo.get_connect_account(nutritionist_id)
        if account is None or not account.charges_enabled:
            raise HTTPException(status_code=400, detail="Este nutriólogo aún no puede recibir pagos.")

        price, currency = await self._get_price(nutritionist_id)
        if not price or price <= 0:
            raise HTTPException(status_code=400, detail="La consulta no tiene un precio definido.")
        amount_cents = round(price * 100)
        currency = (currency or "mxn").lower()

        customer_id = await self._customers.ensure_customer(user_id, email=email)
        default_pm = self._default_payment_method(customer_id)

        pi_args: dict[str, Any] = {
            "amount": amount_cents,
            "currency": currency,
            "customer": customer_id,
            "application_fee_amount": _fee_cents(amount_cents),
            "transfer_data": {"destination": account.account_id},
            "setup_future_usage": "off_session",
            "metadata": {
                "kind": "consultation",
                "consultation_id": consultation_id,
                "patient_id": patient_id,
                "nutritionist_id": nutritionist_id,
            },
        }
        if default_pm:
            pi_args.update({"payment_method": default_pm, "confirm": True, "off_session": False})
        else:
            pi_args["automatic_payment_methods"] = {"enabled": True}

        try:
            pi = as_dict(self._stripe.PaymentIntent.create(**pi_args))
        except self._stripe.error.CardError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc

        pi_status = (pi.get("status") or "").lower()
        payment = await self._repo.create_payment(
            Payment(
                id="",
                kind="consultation",
                consultation_id=consultation_id,
                appointment_id=consultation.get("appointment_id"),
                patient_id=patient_id,
                nutritionist_id=nutritionist_id,
                amount_cents=amount_cents,
                fee_cents=_fee_cents(amount_cents),
                currency=currency,
                status="paid" if pi_status == "succeeded" else "pending",
                payment_intent_id=pi.get("id") or "",
            )
        )

        return {
            "payment_id": payment.id,
            "payment_intent_client_secret": pi.get("client_secret") or "",
            "ephemeral_key_secret": self._customers.ephemeral_key_secret(customer_id),
            "customer_id": customer_id,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            "amount_cents": amount_cents,
            "currency": currency,
            "status": pi_status,
            "requires_action": pi_status == "requires_action",
        }

    async def verify(self, user_id: str, payment_id: str) -> dict:
        patient = await self._get_patient(user_id)
        payment = await self._repo.get_payment(payment_id)
        if not payment or not patient or payment.patient_id != patient.get("id"):
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        try:
            pi = as_dict(self._stripe.PaymentIntent.retrieve(payment.payment_intent_id))
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        status = _payment_status_from_pi((pi.get("status") or "").lower())
        updated = await self._repo.update_payment(payment_id, {"status": status})
        return _serialize(updated)

    async def refund(self, nutritionist_id: str, payment_id: str) -> dict:
        payment = await self._repo.get_payment(payment_id)
        if not payment or payment.nutritionist_id != nutritionist_id:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        if payment.status != "paid":
            raise HTTPException(status_code=409, detail="Solo se puede reembolsar un pago completado.")
        try:
            # Destination charge: pull the money back from the nutritionist's
            # connected balance (reverse_transfer) and hand back the platform
            # fee too — a full, clean unwind. Without these the patient's
            # refund would come entirely from the platform's balance while
            # the nutritionist keeps their cut.
            self._stripe.Refund.create(
                payment_intent=payment.payment_intent_id,
                reverse_transfer=True,
                refund_application_fee=True,
            )
        except self._stripe.error.StripeError as exc:  # type: ignore[attr-defined]
            raise stripe_error_to_http(exc) from exc
        updated = await self._repo.update_payment(
            payment_id, {"status": "refunded", "refunded_cents": payment.amount_cents}
        )
        return _serialize(updated)

    async def list_for_patient(self, user_id: str) -> list[dict]:
        patient = await self._get_patient(user_id)
        if not patient:
            return []
        return [_serialize(p) for p in await self._repo.list_for_patient(patient["id"])]

    async def list_for_nutritionist(self, nutritionist_id: str) -> list[dict]:
        return [_serialize(p) for p in await self._repo.list_for_nutritionist(nutritionist_id)]

    # --- internals --------------------------------------------------

    def _default_payment_method(self, customer_id: str) -> str | None:
        try:
            customer = as_dict(self._stripe.Customer.retrieve(customer_id))
        except self._stripe.error.StripeError:  # type: ignore[attr-defined]
            return None
        return ((customer.get("invoice_settings") or {}).get("default_payment_method")) or None


def _payment_status_from_pi(pi_status: str) -> str:
    if pi_status == "succeeded":
        return "paid"
    if pi_status in ("canceled", "requires_payment_method"):
        return "failed"
    return "pending"


def _serialize(p: Payment) -> dict:
    return {
        "id": p.id,
        "kind": p.kind,
        "consultation_id": p.consultation_id,
        "appointment_id": p.appointment_id,
        "patient_id": p.patient_id,
        "nutritionist_id": p.nutritionist_id,
        "amount_cents": p.amount_cents,
        "fee_cents": p.fee_cents,
        "net_cents": p.amount_cents - p.fee_cents,
        "currency": p.currency,
        "status": p.status,
        "refunded_cents": p.refunded_cents,
        "created_at": p.created_at,
    }
