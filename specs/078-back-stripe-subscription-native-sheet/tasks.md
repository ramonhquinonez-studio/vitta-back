# Tasks: Stripe Subscription — native-sheet payment

- [ ] T1 — Ops: Stripe Products + recurring Prices; record ids. **Needs a real account.**
- [x] T2 — `seed_billing_plans.py`: `seed_paid_plans()` reads `STRIPE_PRICE_PRO` etc.
- [x] T3 — `Subscription` entity/repo already carry `provider_subscription_id` + `current_period_end` (no change needed).
- [x] T4 — `StripeSubscriptionsService` (`start_subscription_sheet` — default no-op / create / modify; `verify_subscription`); `stripe` + `StripeCustomers` deps. Separate from `BillingService` so its constructor doesn't disturb existing tests.
- [x] T5 — Routes: `POST /billing/subscription-sheet`, `POST /billing/subscription/verify` (both 503 until keys set).
- [x] T6 — `subscription_webhook_handlers.py` — pure `apply_*` + `handle_*` wrappers; `register()` from `app/main.py` (`invoice.paid|payment_failed`, `customer.subscription.updated|deleted`; price→plan resolver).
- [x] T7 — `tests/test_billing_subscription_sheet.py` (10 tests, extended `FakeStripe` with `Subscription.create/modify/retrieve`).
- [ ] T8 — `stripe listen` end-to-end (success + declined-renewal). **Needs a real account.**
- [x] T9 — Full backend suite green (279 → then 293 with 079); roadmap + `CLAUDE.md`.
