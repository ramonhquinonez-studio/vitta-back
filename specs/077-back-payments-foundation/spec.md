# Feature Specification: Payments Foundation (Stripe, native-SDK ready)

**Feature Branch**: `077-back-payments-foundation`
**Created**: 2026-09-08
**Status**: Done (code + unit tests; live Stripe verification pending an account)
**Type**: Feature (infrastructure)

## Objective

Shared Stripe infrastructure that both upcoming payment flows build on:
- `078-back-stripe-subscription-native-sheet` — nutritionist → Vitta subscription
- `079-back-payments-connect-consultations` — patient → nutritionist (Connect)

Modeled directly on how `fidelity_back` handles Stripe (`app/modules/payments`,
`app/modules/payment_methods`, `app/modules/stripe_webhooks`): one Customer per app
user, ephemeral keys, saved payment methods attached to the Customer, and an
idempotent webhook dispatcher. The `stripe` SDK is injected as a dependency (as
fidelity does via `PaymentsServiceDeps.stripe`) so services stay unit-testable with a
fake.

The existing `billing` module (`041-back-billing-foundation`) keeps its
`MockBillingProvider` / redirect `POST /billing/checkout` path — this spec adds the
*native-SDK* rails alongside it, it does not replace the mock.

## In Scope

### Config
- Pin `stripe` in `requirements.txt` to an exact version (fidelity uses `10.10.0`;
  pick current-stable and pin).
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET` already exist
  in settings — add a computed `stripe_native_enabled` = all three present.
- Publishable key is returned inside each sheet response (fidelity pattern), not a
  separate config endpoint.

### `app/modules/payments/` — shared helpers
- **`StripeCustomers`**: `ensure_customer(user_id, *, email) -> customer_id`. One Stripe
  Customer per user id (works for nutritionists and patients alike), persisted in a new
  `stripe_customers` collection (`user_id`, `customer_id`, `created_at`).
- **Ephemeral keys**: thin `EphemeralKey.create(customer=...)` wrapper.
- **`SetupIntent`**: `POST /billing/setup-intent` → `{client_secret, ephemeral_key_secret,
  customer_id, publishable_key}` — lets a client add a card with no payment.
- **Stripe error mapping**: `CardError → 409`, other `StripeError → 502`, message
  sanitized (`_stripe_error_detail`, fidelity pattern).

### `app/modules/payment_methods/` — saved cards
Mirrors `fidelity_back`'s `/v1/payment-methods`:
- `GET /billing/payment-methods` → the owner's cards (`PaymentMethod.list(customer,
  type='card')` + `invoice_settings.default_payment_method` to flag the default)
- `POST /billing/payment-methods` `{payment_method_id}` → `PaymentMethod.attach(pm,
  customer)`, set as default when it's the first
- `PATCH /billing/payment-methods/{id}/default` → `Customer.modify(invoice_settings.
  default_payment_method=id)`
- `DELETE /billing/payment-methods/{id}` → `PaymentMethod.detach`
- Auth: any authenticated user (a `require_role` is not needed — both patient and
  nutritionist manage their own cards).

### `app/modules/stripe_webhooks/` — idempotent dispatcher
- Single endpoint `POST /stripe/webhook` (raw body + `Stripe-Signature`), verifies the
  signature against `STRIPE_WEBHOOK_SECRET`.
- Idempotency: `stripe_webhook_events` collection — `mark_processing(event_id, type)`
  returns `False` on a duplicate (short-circuit), `mark_done(event_id, ok, note)`.
- A small registry: `078` and `079` register handlers keyed by event type; unknown
  types are acked and ignored.
- The current `POST /billing/webhook` (in the `billing` router) is superseded — leave
  it returning 404 when `BILLING_PROVIDER != stripe`, and route real events through the
  new endpoint. Document the migration in the `billing` module doc.

## Out of Scope

- The subscription-sheet and consultation-charge endpoints (`078`, `079`).
- Removing `MockBillingProvider` — kept for local dev and the redirect fallback.
- Apple Pay / Google Pay domain registration (client-side concern; tracked in the
  nutri_pro/nutri_app specs).
- A public config endpoint — publishable key travels in sheet responses.

## Documentation Impact

- **Global docs**: `specs/SPEC_ROADMAP.md`; `CLAUDE.md` (new `payments` / `payment_methods`
  / `stripe_webhooks` modules, and the `billing` webhook migration).
- **Cross-repo**: consumed by `nutri_pro` `109`/`110` and `nutri_app` `067`.

## Acceptance Criteria

1. `POST /billing/setup-intent` (authed) returns a usable client secret + ephemeral key
   for a Customer that's created once and reused on the next call.
2. `POST /billing/payment-methods` with a `pm_…` id attaches it to the caller's Customer;
   `GET` lists it; `PATCH …/default` flips the default; `DELETE` detaches it.
3. `POST /stripe/webhook` rejects a bad signature (400) and processes a valid event
   exactly once — a replayed event id returns `{ok, duplicate: true}` without re-running.
4. A `stripe.error.CardError` from any of these surfaces as HTTP 409 with a short
   Spanish-safe message, never a raw stack.

## Validation

- Unit tests with a fake `stripe` module injected: `tests/test_stripe_customers.py`,
  `tests/test_payment_methods_service.py`, `tests/test_stripe_webhook_idempotency.py`.
- Live: `stripe listen --forward-to localhost:8000/stripe/webhook` + a manual
  SetupIntent confirmed with a test card, card shows in `GET /billing/payment-methods`.
- Full backend suite green.
