# Implementation Plan: Payments Foundation

**Branch**: `077-back-payments-foundation` | **Spec**: `specs/077-back-payments-foundation/spec.md`

## Reference
`fidelity_back`: `app/modules/payments/application/payments_service.py`
(`_ensure_stripe_customer`, `EphemeralKey.create`, `_stripe_error_detail`),
`app/modules/payment_methods/`, `app/modules/stripe_webhooks/` (signature verify +
`_mark_event_processing` / `_mark_event_done` idempotency).

## Steps

1. Pin `stripe` in `requirements.txt`; add `stripe_native_enabled` to settings.
2. `app/modules/payments/`:
   - `infrastructure/stripe_client.py` — builds the configured `stripe` module (api key
     set), single place.
   - `application/stripe_customers.py` — `ensure_customer`; `infrastructure/mongo_stripe_customers_repository.py`
     (`stripe_customers` collection).
   - `application/errors.py` — `stripe_error_to_http(exc)`.
   - `presentation/router.py` — `POST /billing/setup-intent`.
   - Services take `stripe` + repos as constructor deps (fake-able), mirroring
     `PaymentsServiceDeps`.
3. `app/modules/payment_methods/`:
   - domain `PaymentMethod` entity + repo protocol (local metadata: `id`, `last4`,
     `brand`, `exp`, `holder_name`, `is_default`, `stripe_payment_method_id`).
   - `application/payment_methods_service.py` — list/add/set-default/delete, all going
     through Stripe + the local mirror.
   - `infrastructure/mongo_payment_methods_repository.py`.
   - `presentation/router.py` — the 4 routes under `/billing/payment-methods`.
4. `app/modules/stripe_webhooks/`:
   - `application/webhook_dispatcher.py` — `verify(payload, sig) -> event`,
     `mark_processing` / `mark_done`, `register(event_type, handler)`.
   - `infrastructure/mongo_webhook_events_repository.py` (`stripe_webhook_events`).
   - `presentation/router.py` — `POST /stripe/webhook`.
5. `billing` router: gate `POST /billing/webhook` to 404 unless mock; note the move.
6. `app/main.py` — mount the 3 routers.
7. Tests with a `FakeStripe` (Customer/EphemeralKey/PaymentMethod/SetupIntent/Webhook
   stubs) — 3 new test files.
8. `stripe listen` smoke; full suite.

## Decisions
- **One `stripe_customers` collection keyed by bare `user_id`** — not per-tenant like
  fidelity (Vitta is single-tenant). Same user id space for nutritionists and patients.
- **Publishable key in responses**, not a config endpoint — fewer round trips, matches
  fidelity's psheet.
- **New `/stripe/webhook`** rather than extending `/billing/webhook` — `079` needs the
  same dispatcher and it isn't billing-specific.
