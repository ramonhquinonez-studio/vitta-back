# Feature Specification: Stripe Subscription — native-sheet payment

**Feature Branch**: `078-back-stripe-subscription-native-sheet`
**Created**: 2026-09-08
**Status**: Done (code + unit tests; live Stripe verification pending an account)
**Type**: Feature

## Objective

Let the nutritionist pay for a paid plan **from inside the app** (native card sheet in
`nutri_pro` `109`), not just via the hosted-Checkout redirect. Extends the existing
`billing` module (`041`) with a recurring-subscription variant of `fidelity_back`'s
`init_payment_sheet`: create the Stripe Subscription `incomplete`, hand the client the
first invoice's PaymentIntent client secret, let the SDK confirm it, then reconcile.

Builds on `077-back-payments-foundation` (Customer helper, ephemeral keys, webhook
dispatcher, payment-methods). The redirect path (`POST /billing/checkout`) stays as the
**web fallback**.

## In Scope

### Plans
- Ops: create Products + recurring Prices in the Stripe dashboard for each non-default
  plan.
- Update `seed_billing_plans.py` (and the "Pro" seed) to carry real `stripe_price_id`.

### `POST /billing/subscription-sheet` `{plan_id}`
- Default/free plan → no Stripe call, `enroll_default_plan(owner)`, return
  `{status: "active", requires_action: false}` with empty secrets.
- Paid plan:
  - `ensure_customer(owner, email)`, `EphemeralKey.create`
  - Owner already on a **different paid plan** → `Subscription.modify(sub_id,
    items=[{id: item, price: new_price}], proration_behavior="create_prorations")`
  - Otherwise → `Subscription.create(customer, items=[{price}],
    payment_behavior="default_incomplete", payment_settings={save_default_payment_method:
    "on_subscription"}, expand=["latest_invoice.payment_intent"],
    metadata={owner_id, plan_id})`
  - If the owner has a saved default card, attach it and let the first invoice attempt
    it server-side (`off_session=False`); the client only shows the sheet when the PI
    still needs a payment method or `requires_action`.
- Persist `provider_customer_id` + `provider_subscription_id` on the `billing`
  `Subscription` row immediately (status from the Subscription object).
- Return (fidelity-shape):
  `{ subscription_id, plan_id, payment_intent_client_secret, ephemeral_key_secret,
     customer_id, publishable_key, status, requires_action }`

### `POST /billing/subscription/verify` `{subscription_id}`
- `Subscription.retrieve(expand=["latest_invoice.payment_intent"])`
- Reconcile `Subscription.status`, `current_period_end`, `provider_subscription_id`
  into the repo (client-triggered, alongside the webhook — same belt-and-suspenders as
  fidelity's `/v1/payments/verify`).
- Return `{ plan_id, status, current_period_end }`.

### Webhook handlers (registered with `077`'s dispatcher)
- `invoice.paid` → `active`
- `invoice.payment_failed` → `past_due`
- `customer.subscription.updated` → mirror `status` + `current_period_end` + `plan_id`
  (resolve price → plan)
- `customer.subscription.deleted` → `canceled`
- All keyed to the owner via `metadata.owner_id` or `provider_customer_id`.

### Quota
- `_effective_plan` / `check_patient_quota` already fall back to the default plan for
  non-`{active,trialing}` statuses — verify a `past_due`/`canceled` sub correctly
  reverts the nutritionist to the free limit.

## Out of Scope

- Trials, promo codes, tax (Stripe Tax) — later.
- Cancel/downgrade UI semantics beyond Stripe defaults (client uses the portal or a
  `Subscription.update(cancel_at_period_end=True)` — spec that in `109` if needed).
- Removing `POST /billing/checkout` / `POST /billing/portal` — kept as web/fallback.

## Documentation Impact
- `specs/SPEC_ROADMAP.md`; `CLAUDE.md` `billing` bullet.
- Cross-repo: consumed by `nutri_pro` `109`.

## Acceptance Criteria

1. `subscription-sheet` for a paid plan returns a confirmable PaymentIntent client
   secret and creates an `incomplete` Stripe Subscription; the `billing` row shows
   `provider_subscription_id`.
2. After the client confirms, `subscription/verify` reports `active` and the row
   reflects it — even if the webhook hasn't landed yet.
3. `invoice.payment_failed` flips the row to `past_due` and `check_patient_quota`
   enforces the free limit again.
4. `subscription-sheet` for the default plan performs zero Stripe calls.

## Validation
- `tests/test_billing_subscription_sheet.py` (fake stripe): create / modify / verify /
  default-plan no-op / webhook transitions / quota revert.
- Live: `stripe listen`, subscribe with `4242…` test card end-to-end, then a
  `pm_card_chargeDeclined` price to see `past_due`.
- Full suite green.
