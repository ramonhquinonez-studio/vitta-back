# Implementation Plan: Stripe Subscription — native-sheet payment

**Branch**: `078-back-stripe-subscription-native-sheet` | **Spec**: `specs/078-back-stripe-subscription-native-sheet/spec.md`

## Steps
1. Ops (not code): Stripe dashboard → Products + recurring Prices; record price ids.
2. `seed_billing_plans.py` + Pro seed → real `stripe_price_id`.
3. `billing` domain/repo: add `provider_subscription_id` write path (entity already has
   the field); add `current_period_end` handling.
4. `billing_service.py`:
   - `start_subscription_sheet(owner_id, email, plan_id)` — default no-op branch;
     create-vs-modify branch; persist ids; return the credential dict.
   - `verify_subscription(owner_id, subscription_id)` — retrieve + reconcile.
   - inject `stripe` + `StripeCustomers` (from `077`) as deps.
5. `billing` router: `POST /billing/subscription-sheet`, `POST /billing/subscription/verify`.
6. `billing` webhook handler module — register 4 handlers with `077`'s dispatcher;
   price→plan resolution helper.
7. Tests: `tests/test_billing_subscription_sheet.py` with the `FakeStripe` from `077`
   extended (Subscription.create/modify/retrieve, Invoice/PaymentIntent expansion).
8. `stripe listen` live smoke; full suite; roadmap + CLAUDE.md.

## Decisions
- **`payment_behavior="default_incomplete"`** — the canonical Stripe pattern for
  collecting the first payment client-side; the first invoice's PaymentIntent is what
  the native sheet confirms.
- **`verify` in addition to the webhook** — the client gets an immediate answer;
  fidelity does the same (`/v1/payments/verify`).
- **Plan change = `Subscription.modify` with prorations**, not cancel+recreate — keeps
  one Stripe subscription per nutritionist.
