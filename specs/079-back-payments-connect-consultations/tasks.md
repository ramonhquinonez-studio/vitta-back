# Tasks: Patient → nutritionist payments (Stripe Connect)

- [ ] T0 — Ops: enable Connect; verify MXN/country payout eligibility. **Needs a real account.**
- [x] T1 — `PLATFORM_FEE_BPS` + `STRIPE_CONNECT_COUNTRY` in settings.
- [x] T2 — `stripe_connect_accounts` collection + repo (chose a dedicated collection over a `nutritionist_profile` field).
- [x] T3 — `ConnectService`: `account_link` (create-once), `status` (refresh from Stripe); `account.updated` webhook handler.
- [x] T4 — `Payment` / `ConnectAccount` entities + `MongoPaymentsRepository` (`payments` collection, `payment_intent_id` unique).
- [x] T5 — `ConsultationChargesService`: `create_sheet` (fee = bps of price, `transfer_data.destination`, saved-card-confirm branch, double-charge guard), `verify`, `refund` (owner + paid-only), list helpers. Collaborators injected as callables.
- [x] T6 — Routes (`consultation_charges_router.py`, prefix `/payments`, all 503 until keys): `POST /payments/connect/account-link`, `GET /payments/connect/status`, `POST /payments/consultations/{id}/sheet`, `POST /payments/{id}/verify`, `POST /payments/{id}/refund`, `GET /payments/mine`, `GET /payments/received`.
- [x] T7 — `connect_webhook_handlers.py` — pure `apply_*` + `handle_*` wrappers; `register()` from `app/main.py` (`payment_intent.succeeded|payment_failed`, `charge.refunded` idempotent, `account.updated`).
- [x] T8 — `tests/test_payments_connect_consultations.py` (14 tests; `FakeStripe` extended with `Account`/`AccountLink`/`PaymentIntent`/`Refund`).
- [ ] T9 — Live Connect test-mode: onboarding + charge + fee split + refund. **Needs a real account.**
- [x] T10 — Full suite green (293); roadmap + `CLAUDE.md`. Per-consultation price override deferred to a follow-up spec.
