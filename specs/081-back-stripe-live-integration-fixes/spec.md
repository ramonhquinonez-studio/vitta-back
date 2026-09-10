# Feature Specification: Stripe live-integration fixes (SDK v15 + current API)

**Feature Branch**: `081-back-stripe-live-integration-fixes`
**Created**: 2026-09-09
**Status**: Done (2026-09-09) — subscription + Connect consultation flows live-verified in test mode
**Type**: Bugfix (found on first real-account wiring)

## Context

`077`/`078`/`079` were built and unit-tested against `FakeStripe` only. Wiring a
real Stripe **test-mode** account (keys borrowed from `fidelity_back`, `stripe listen`
for the webhook secret, a "Vitta Pro" recurring Price) surfaced two real bugs the
fake couldn't catch, plus a config gap.

## Bugs fixed

### 1. `StripeObject.get()` → `AttributeError` (500s)

`stripe` SDK v15's `StripeObject` no longer subclasses `dict`; calling `.get()` /
other dict methods raises `AttributeError: 'get' is a dict method…`. `FakeStripe._Obj`
*is* a dict subclass, so every `.get()` call on a Stripe response passed in tests and
500'd live. Hit `POST /billing/subscription-sheet` and **every** `POST /stripe/webhook`.

**Fix** — `app/modules/payments/infrastructure/stripe_client.py` gains `as_dict(obj)`:
recursively normalizes a `StripeObject` (or a fake's dict) to a plain dict via
`obj.to_dict()`. Applied at every SDK boundary that is then read with `.get()`:
`stripe_subscriptions_service` (`Subscription.create`/`retrieve`/`modify`),
`webhook_dispatcher.verify()` (`Webhook.construct_event`),
`connect_service.status()` (`Account.retrieve`),
`consultation_charges_service` (`PaymentIntent.create`/`retrieve`, `Customer.retrieve`).
Attribute access (`customer.id`, `key.secret`) was already fine and is unchanged.

### 2. Subscription sheet returned an empty client secret

Current Stripe API (2025+) removed `invoice.payment_intent`; the confirmable client
secret is now `latest_invoice.confirmation_secret.client_secret`. The old
`expand=["latest_invoice.payment_intent"]` returned nothing, so the native card sheet
had no PaymentIntent to confirm.

**Fix** — `start_subscription_sheet` now expands **both**
`latest_invoice.confirmation_secret` and `latest_invoice.payment_intent` (legacy
accounts) and reads `confirmation_secret.client_secret` first, falling back to
`payment_intent.client_secret`. `FakeStripe` updated to the current shape
(`confirmation_secret` always present; `omit_payment_intent` flag simulates a
newer-API account); regression test added.

### 3. `STRIPE_PRICE_PRO` not a config field

`seed_billing_plans.py` read it via `os.getenv` only, so putting it in `.env` broke
`Settings` (`extra="forbid"`). Added `STRIPE_PRICE_PRO: str = ""` to `Settings`; the
seed script now prefers `settings.STRIPE_PRICE_PRO`.

### 4. Consultation refund didn't unwind the destination charge

`ConsultationChargesService.refund` called `Refund.create(payment_intent=…)` with no
`reverse_transfer` / `refund_application_fee`. Verified live: the patient was refunded
in full **from the platform balance**, the nutritionist's transfer was **not** reversed
(they kept their cut), and the platform kept its fee — a net loss to the platform on
every refund. Fixed to `reverse_transfer=True, refund_application_fee=True` (full clean
unwind). Confirmed live: `transfer.amount_reversed == amount`, `reversed: true`.
`FakeStripe.Refund.create` + the refund test updated.

## Live verification (test mode, fidelity's account — Connect now enabled)

Subscription (`078`):
- `POST /billing/setup-intent` → real `seti_…` + `ek_test_…` + `cus_…` ✅
- `POST /billing/subscription-sheet` (Pro) → real `sub_…` + `pi_…` client secret,
  `status: incomplete` ✅

Connect + consultation charges (`079`) — after enabling Connect in test mode and
attaching a chargeable test connected account (`type=custom`, MX, test verification
data → `charges_enabled: true`) to the demo nutritionist:
- `GET /payments/connect/status` → `{connected, charges_enabled, requirements_due,
  disabled_reason}` all correct through the un-onboarded → onboarded transition ✅
- `POST /payments/connect/account-link` → real hosted-onboarding URL ✅
- `POST /payments/consultations/{id}/sheet` (patient) → PaymentIntent `amount 80000 mxn`,
  `application_fee_amount 8000` (10% = `PLATFORM_FEE_BPS`), `transfer_data.destination`
  = the nutritionist's account ✅
- confirm with `pm_card_visa` → `POST /payments/{id}/verify` → `paid`, `net_cents 72000` ✅
- `GET /payments/received` (pro) → the row with `patient_name` resolved ✅
- `POST /payments/{id}/refund` (pro) → `refunded`; on Stripe the transfer is fully
  reversed and the app fee refunded ✅
- `GET /payments/mine` (patient) → history ✅

Webhooks: 12 events over the session via `stripe listen`, **all 200, zero 500s**.

## Out of scope
- Enabling Connect (account-owner decision).
- The `nutri_pro` / `nutri_app` client sides (already built / drafted).
- Migrating to a dedicated Vitta Stripe account (borrowed keys are explicitly temporary).

## Acceptance Criteria
1. `subscription-sheet` and `stripe/webhook` return 2xx against a real test account.
2. `subscription-sheet` returns a non-empty `payment_intent_client_secret` on the
   current API.
3. `.env` can carry `STRIPE_PRICE_PRO`; `Settings` loads.
4. Full suite green (309), incl. a `confirmation_secret`-path regression test.

## Validation
- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 309.
- Manual: the live smoke sequence above.
