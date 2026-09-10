# Tasks: Stripe live-integration fixes

- [x] T1 — `stripe_client.as_dict()` recursive normalizer.
- [x] T2 — apply `as_dict` at SDK boundaries: subscriptions service (create/retrieve/modify), webhook dispatcher (`construct_event`), connect service (`Account.retrieve`), consultation charges (PI create/retrieve, Customer retrieve).
- [x] T3 — `start_subscription_sheet`: expand + read `latest_invoice.confirmation_secret.client_secret` (fallback to legacy `payment_intent`).
- [x] T4 — `Settings.STRIPE_PRICE_PRO`; `seed_billing_plans.py` reads it from settings.
- [x] T5 — consultation `refund` → `reverse_transfer=True, refund_application_fee=True` (was refunding from the platform balance only, not unwinding the transfer/fee).
- [x] T6 — `FakeStripe`: `confirmation_secret` on the invoice + `omit_payment_intent` flag; `Refund.create` accepts the reversal kwargs. Regression tests in `test_billing_subscription_sheet.py` + `test_payments_connect_consultations.py`.
- [x] T7 — full suite 309 green; live smoke (subscription sheet + full Connect consultation charge/verify/received/refund + webhooks) green.
- [x] T8 — roadmap + `CLAUDE.md` + `.env.example` Stripe section.

## Test-mode setup notes (for re-verifying later)
- Keys borrowed from `fidelity_back/.env` (test mode). `stripe listen --forward-to
  localhost:8000/stripe/webhook` must be running for webhooks.
- Connect is enabled on that account. The demo nutritionist's `stripe_connect_accounts`
  row points at a `type=custom` test account (`acct_…`, `charges_enabled: true`) so the
  charge path works without hosted onboarding. `nutritionist_profiles.session_price` =
  800 MXN.
