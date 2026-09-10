"""In-memory stand-in for the `stripe` SDK, injected into services the
same way `fidelity_back` does (`PaymentsServiceDeps.stripe`). Covers only
what specs 077-079 use; extend as those land.
"""

from __future__ import annotations

import json
from typing import Any


class _Obj(dict):
    """Dict that also allows attribute access, like a real Stripe object."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


class _Error:
    class StripeError(Exception):
        def __init__(self, message: str = "stripe error", user_message: str | None = None):
            super().__init__(message)
            self.user_message = user_message
            self.error = _Obj(message=message)

    class CardError(StripeError):
        pass

    class InvalidRequestError(StripeError):
        pass

    class SignatureVerificationError(StripeError):
        pass


class FakeStripe:
    error = _Error

    def __init__(self) -> None:
        self.api_key: str | None = None
        self._customers: dict[str, _Obj] = {}
        self._payment_methods: dict[str, _Obj] = {}
        self._subscriptions: dict[str, _Obj] = {}
        self._payment_intents: dict[str, _Obj] = {}
        self._accounts: dict[str, _Obj] = {}
        self._refunds: list[_Obj] = []
        self._seq = 0
        self.raise_on: dict[str, Exception] = {}  # e.g. {"PaymentMethod.attach": CardError()}
        # Tunable outcomes.
        self.subscription_status = "incomplete"
        self.pi_status = "requires_payment_method"
        self.current_period_end = 1_800_000_000
        self.account_charges_enabled = True
        # When True the subscription's latest_invoice has no `payment_intent`
        # (current Stripe API) — only `confirmation_secret`.
        self.omit_payment_intent = False

    # -- helpers --------------------------------------------------------

    def _id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}_{self._seq}"

    def _maybe_raise(self, op: str) -> None:
        exc = self.raise_on.get(op)
        if exc is not None:
            raise exc

    def add_card_fixture(self, customer_id: str, *, brand="visa", last4="4242") -> str:
        pm_id = self._id("pm")
        self._payment_methods[pm_id] = _Obj(
            id=pm_id, customer=customer_id,
            card=_Obj(brand=brand, last4=last4, exp_month=12, exp_year=2030),
        )
        return pm_id

    # -- Customer -----------------------------------------------------

    class _Customers:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, *, email=None, metadata=None):
            self._o._maybe_raise("Customer.create")
            cid = self._o._id("cus")
            self._o._customers[cid] = _Obj(id=cid, email=email, metadata=metadata or {},
                                           invoice_settings=_Obj(default_payment_method=None))
            return self._o._customers[cid]

        def retrieve(self, cid):
            return self._o._customers[cid]

        def modify(self, cid, *, invoice_settings=None):
            self._o._maybe_raise("Customer.modify")
            if invoice_settings:
                self._o._customers[cid]["invoice_settings"] = _Obj(**invoice_settings)
            return self._o._customers[cid]

    @property
    def Customer(self):  # noqa: N802
        return FakeStripe._Customers(self)

    # -- EphemeralKey -----------------------------------------------

    class _EphemeralKey:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, *, customer, stripe_version):
            return _Obj(id=self._o._id("ek"), secret=f"ek_secret_{customer}")

    @property
    def EphemeralKey(self):  # noqa: N802
        return FakeStripe._EphemeralKey(self)

    # -- SetupIntent ----------------------------------------------

    class _SetupIntent:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, *, customer, usage=None, payment_method_types=None):
            self._o._maybe_raise("SetupIntent.create")
            sid = self._o._id("seti")
            return _Obj(id=sid, client_secret=f"{sid}_secret", customer=customer, status="requires_payment_method")

    @property
    def SetupIntent(self):  # noqa: N802
        return FakeStripe._SetupIntent(self)

    # -- PaymentMethod ------------------------------------------

    class _PaymentMethod:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def attach(self, pm_id, *, customer):
            self._o._maybe_raise("PaymentMethod.attach")
            if pm_id not in self._o._payment_methods:
                self._o._payment_methods[pm_id] = _Obj(
                    id=pm_id, customer=customer,
                    card=_Obj(brand="visa", last4="4242", exp_month=12, exp_year=2030),
                )
            else:
                self._o._payment_methods[pm_id]["customer"] = customer
            return self._o._payment_methods[pm_id]

        def detach(self, pm_id):
            self._o._maybe_raise("PaymentMethod.detach")
            self._o._payment_methods.pop(pm_id, None)
            return _Obj(id=pm_id, customer=None)

        def retrieve(self, pm_id):
            if pm_id not in self._o._payment_methods:
                raise FakeStripe.error.InvalidRequestError("No such PaymentMethod")
            return self._o._payment_methods[pm_id]

        def list(self, *, customer, type=None):
            data = [pm for pm in self._o._payment_methods.values() if pm.get("customer") == customer]
            return _Obj(data=data)

    @property
    def PaymentMethod(self):  # noqa: N802
        return FakeStripe._PaymentMethod(self)

    # -- Subscription ------------------------------------------

    def _subscription_obj(self, sub_id, *, customer, price_id, item_id, metadata):
        return _Obj(
            id=sub_id,
            customer=customer,
            status=self.subscription_status,
            metadata=metadata or {},
            current_period_end=self.current_period_end,
            items=_Obj(data=[_Obj(id=item_id, price=_Obj(id=price_id),
                                  current_period_end=self.current_period_end)]),
            latest_invoice=_Obj(
                # Current Stripe API: the confirmable client secret lives on
                # the invoice's `confirmation_secret`.
                confirmation_secret=_Obj(
                    client_secret=f"pi_secret_{sub_id}", type="payment_intent"
                ),
                **(
                    {}
                    if self.omit_payment_intent
                    else {
                        "payment_intent": _Obj(
                            id=self._id("pi"),
                            client_secret=f"pi_secret_{sub_id}",
                            status=self.pi_status,
                        )
                    }
                ),
            ),
        )

    class _Subscription:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, *, customer, items, payment_behavior=None, payment_settings=None,
                   expand=None, metadata=None):
            self._o._maybe_raise("Subscription.create")
            sub_id = self._o._id("sub")
            price_id = items[0]["price"]
            obj = self._o._subscription_obj(
                sub_id, customer=customer, price_id=price_id,
                item_id=self._o._id("si"), metadata=metadata,
            )
            self._o._subscriptions[sub_id] = obj
            return obj

        def retrieve(self, sub_id, *, expand=None):
            return self._o._subscriptions[sub_id]

        def modify(self, sub_id, *, items=None, proration_behavior=None,
                   payment_behavior=None, expand=None):
            self._o._maybe_raise("Subscription.modify")
            existing = self._o._subscriptions[sub_id]
            price_id = items[0]["price"] if items else existing["items"]["data"][0]["price"]["id"]
            item_id = items[0].get("id") if items else existing["items"]["data"][0]["id"]
            obj = self._o._subscription_obj(
                sub_id, customer=existing["customer"], price_id=price_id,
                item_id=item_id, metadata=existing.get("metadata"),
            )
            self._o._subscriptions[sub_id] = obj
            return obj

    @property
    def Subscription(self):  # noqa: N802
        return FakeStripe._Subscription(self)

    # -- PaymentIntent ----------------------------------------

    class _PaymentIntent:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, **kwargs):
            self._o._maybe_raise("PaymentIntent.create")
            pi_id = self._o._id("pi")
            confirm = kwargs.get("confirm")
            status = "succeeded" if confirm else self._o.pi_status
            obj = _Obj(
                id=pi_id, client_secret=f"{pi_id}_secret", status=status,
                amount=kwargs.get("amount"), currency=kwargs.get("currency"),
                customer=kwargs.get("customer"),
                application_fee_amount=kwargs.get("application_fee_amount"),
                transfer_data=kwargs.get("transfer_data"),
                metadata=kwargs.get("metadata") or {},
            )
            self._o._payment_intents[pi_id] = obj
            return obj

        def retrieve(self, pi_id, **kwargs):
            return self._o._payment_intents[pi_id]

    @property
    def PaymentIntent(self):  # noqa: N802
        return FakeStripe._PaymentIntent(self)

    # -- Account / AccountLink (Connect) ---------------------

    class _Account:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, **kwargs):
            self._o._maybe_raise("Account.create")
            acct_id = self._o._id("acct")
            obj = _Obj(
                id=acct_id, charges_enabled=self._o.account_charges_enabled,
                payouts_enabled=self._o.account_charges_enabled,
                requirements=_Obj(currently_due=[], disabled_reason=None),
                metadata=kwargs.get("metadata") or {},
            )
            self._o._accounts[acct_id] = obj
            return obj

        def retrieve(self, acct_id):
            acc = self._o._accounts.get(acct_id)
            if acc is None:
                raise FakeStripe.error.InvalidRequestError("No such account")
            acc["charges_enabled"] = self._o.account_charges_enabled
            acc["payouts_enabled"] = self._o.account_charges_enabled
            return acc

    @property
    def Account(self):  # noqa: N802
        return FakeStripe._Account(self)

    class _AccountLink:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, *, account, refresh_url, return_url, type):
            return _Obj(url=f"https://connect.stripe.test/{account}")

    @property
    def AccountLink(self):  # noqa: N802
        return FakeStripe._AccountLink(self)

    # -- Refund ---------------------------------------------

    class _Refund:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def create(self, *, payment_intent, reverse_transfer=None, refund_application_fee=None, amount=None):
            self._o._maybe_raise("Refund.create")
            r = _Obj(
                id=self._o._id("re"),
                payment_intent=payment_intent,
                status="succeeded",
                reverse_transfer=bool(reverse_transfer),
                refund_application_fee=bool(refund_application_fee),
            )
            self._o._refunds.append(r)
            return r

    @property
    def Refund(self):  # noqa: N802
        return FakeStripe._Refund(self)

    # -- Webhook ------------------------------------------------

    class _Webhook:
        def __init__(self, outer: "FakeStripe"):
            self._o = outer

        def construct_event(self, payload, sig_header, secret):
            if sig_header != f"sig_{secret}":
                raise FakeStripe.error.SignatureVerificationError("bad signature")
            return json.loads(payload)

    @property
    def Webhook(self):  # noqa: N802
        return FakeStripe._Webhook(self)
