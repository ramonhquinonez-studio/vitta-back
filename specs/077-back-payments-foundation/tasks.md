# Tasks: Payments Foundation

- [x] T1 — Pin `stripe==15.5.1` in `requirements.txt`; `stripe_native_enabled` property on `Settings`.
- [x] T2 — `payments` module: `stripe_client.get_stripe()`, `StripeCustomers` + `MongoStripeCustomersRepository` (`stripe_customers`), `stripe_error_to_http`, `POST /billing/setup-intent`.
- [x] T3 — `payment_methods` module: `SavedCard` entity + `PaymentMethodsService` (Stripe is source of truth, no local mirror) + 4 routes (`GET/POST /billing/payment-methods`, `PATCH …/{id}/default`, `DELETE …/{id}`).
- [x] T4 — `stripe_webhooks` module: `WebhookDispatcher` (`verify` + idempotency via `stripe_webhook_events` + idempotent `register_handler`), `POST /stripe/webhook`.
- [x] T5 — `billing` router: `POST /billing/webhook` marked deprecated, still 404 unless mock; note added.
- [x] T6 — 3 router shims in `app/routers/`; mounted in `app/main.py`; 2 Mongo indexes (`stripe_customers` unique, `stripe_webhook_events` TTL 30d).
- [x] T7 — `tests/_fakes/fake_stripe.py` (`FakeStripe`); `tests/test_stripe_customers.py`, `tests/test_payment_methods_service.py`, `tests/test_stripe_webhook_idempotency.py` (14 tests).
- [ ] T8 — `stripe listen` local smoke (setup-intent + card attach) — **needs a real Stripe test account**.
- [x] T9 — Full backend suite green (269, +14); roadmap + `CLAUDE.md` pending final pass.

## Endpoints (all 503 until `STRIPE_SECRET_KEY`/`_PUBLISHABLE_KEY`/`_WEBHOOK_SECRET` are set)
- `POST /billing/setup-intent`
- `GET/POST /billing/payment-methods`, `PATCH /billing/payment-methods/{id}/default`, `DELETE /billing/payment-methods/{id}`
- `POST /stripe/webhook`
