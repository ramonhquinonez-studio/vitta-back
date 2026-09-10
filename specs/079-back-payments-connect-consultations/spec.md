# Feature Specification: Patient → nutritionist payments (Stripe Connect)

**Feature Branch**: `079-back-payments-connect-consultations`
**Created**: 2026-09-08
**Status**: Done (code + unit tests; live Stripe verification pending an account)
**Type**: Feature (large)

## Later addition (2026-09-09, for `nutri_pro` `110`)

`GET /payments/received` now returns a `patient_name` on each row. The
`ConsultationChargesService` stays free of the patients module — the router
handler resolves names via `MongoPatientsRepository.get_for_owner` (one
lookup per distinct payer), mirroring the consultations list endpoint. No
schema/service change, no new test (covered by the router smoke guardrail).

## Objective

Let a patient pay their nutritionist for a consultation, **from inside `nutri_app`**,
with Vitta taking a platform fee. This is a marketplace flow — money moves patient →
nutritionist — so it needs **Stripe Connect** (Express connected accounts + destination
charges). `fidelity_back` has no Connect precedent; the *charge* mechanics reuse its
`init_payment_sheet` shape (Customer + ephemeral key + PaymentIntent + credential dict
+ `/verify`), with `application_fee_amount` + `transfer_data.destination` added.

Builds on `077-back-payments-foundation`.

## In Scope

### Config
- `PLATFORM_FEE_BPS` (basis points, e.g. `1000` = 10%) in settings.
- Payout schedule left to Stripe Connect defaults.

### Connected accounts (nutritionist onboarding)
- `stripe_connect_account_id` field on `nutritionist_profile`.
- `POST /payments/connect/account-link` (nutritionist-auth) →
  `Account.create(type="express", country=..., capabilities={card_payments, transfers},
  business_type="individual", metadata={owner_id})` (once), then
  `AccountLink.create(account, refresh_url, return_url, type="account_onboarding")` —
  return the URL (Stripe-hosted KYC; the client opens it, redirect is unavoidable).
- `GET /payments/connect/status` → `Account.retrieve` →
  `{ charges_enabled, payouts_enabled, requirements_currently_due, disabled_reason }`,
  cached on the profile and refreshed on `account.updated`.

### Consultation pricing
- New fields on `Consultation` (or the linked `Appointment` — decide during design;
  `Consultation` is the better home since `026` made it the encounter record):
  `price_cents`, `currency`, `payment_status` (`unpaid | pending | paid | refunded`),
  `payment_id`.
- Default `price_cents` = `nutritionist_profile.session_price` × 100; nutritionist can
  override per consultation.

### Charge — `POST /payments/consultations/{consultation_id}/sheet` (patient-auth)
- Resolve consultation → nutritionist → connect account; **400** if not
  `charges_enabled`.
- `ensure_customer(patient, email)`, `EphemeralKey.create`.
- `PaymentIntent.create(amount=price_cents, currency, customer,
  application_fee_amount=round(price_cents * PLATFORM_FEE_BPS / 10000),
  transfer_data={destination: connect_account}, setup_future_usage="off_session",
  metadata={consultation_id, patient_id, nutritionist_id, kind: "consultation"})`.
  Saved default card → `payment_method=…, confirm=True, off_session=False`; else
  `automatic_payment_methods.enabled`.
- Write a `payments` row: `{id, kind, consultation_id, appointment_id, patient_id,
  nutritionist_id, amount_cents, fee_cents, currency, status, payment_intent_id,
  created_at}`; set the consultation `payment_status` from the PI status.
- Return the fidelity-shape credential dict + `{amount_cents, currency}`.

### Reconcile / manage
- `POST /payments/{id}/verify` (patient-auth) — `PaymentIntent.retrieve`, update the
  `payments` row + consultation `payment_status`.
- `POST /payments/{id}/refund` (nutritionist-auth) — `Refund.create`; row → `refunded`,
  consultation → `refunded`.
- `GET /me/payments` (patient) — their consultation payments.
- `GET /payments` (nutritionist) — received, with `net = amount − fee`, status, payout
  hint.

### Webhook handlers (registered with `077`'s dispatcher)
- `payment_intent.succeeded / payment_failed` → `payments` row + consultation status
- `charge.refunded` → reconcile `refunded_amount` (assign, not increment — idempotent)
- `account.updated` → refresh cached Connect flags
- `transfer.created` / `payout.paid` — optional, informational only in v1

## Out of Scope

- Patient subscriptions; wallet / stored balance; tipping.
- Multi-currency per nutritionist (single currency from the profile).
- Instant payouts / payout management beyond showing status.
- Dispute/chargeback handling beyond a log line (Stripe dashboard for v1).
- **When** the charge is triggered — that's a client product decision, spec'd in
  `nutri_pro` `110` / `nutri_app` `067`. The backend only exposes the per-consultation
  charge endpoint.
- MXN Connect payout eligibility — **flagged as an ops verification step** before build
  (Stripe's supported countries/currencies for connected-account payouts).

## As built (deviations from the plan above)

- **Connect account id is its own collection** `stripe_connect_accounts` (`owner_id`,
  `account_id`, cached `charges_enabled`/`payouts_enabled`/`requirements_due`), not a
  field on `nutritionist_profile` — self-contained in the `payments` module, mirrors
  `stripe_customers`, no cross-module entity change.
- **No `Consultation` payment fields.** "Is this consultation paid?" is answered from
  the `payments` ledger (`consultation_id` + `status == "paid"`). Keeps the blast
  radius off the consultations module.
- **Price = `nutritionist_profile.session_price` only** — no per-consultation override
  yet (tracked as a follow-up spec). `create_sheet` 400s if the profile has no price.
- Routes: `GET /payments/mine` (patient) + `GET /payments/received` (nutritionist)
  instead of `GET /me/payments` + `GET /payments` — avoids editing the `me` module.
- New router file `consultation_charges_router.py` (prefix `/payments`), separate from
  the `077` `/billing`-prefixed one.

## Documentation Impact
- `specs/SPEC_ROADMAP.md`; `CLAUDE.md` (new `payments` charge sub-area — Connect +
  consultation ledger).
- Cross-repo: `nutri_pro` `110`, `nutri_app` `067`.

## Acceptance Criteria

1. `POST /payments/connect/account-link` returns a Stripe onboarding URL; after the
   nutritionist finishes KYC, `GET /payments/connect/status` reports `charges_enabled`.
2. `POST /payments/consultations/{id}/sheet` for a chargeable consultation returns a
   confirmable PaymentIntent whose `application_fee_amount` = fee bps of the price and
   whose `transfer_data.destination` is the nutritionist's account.
3. On success (webhook or `/verify`), the `payments` row and the consultation's
   `payment_status` both read `paid`; `GET /payments` shows `net` = price − fee.
4. `POST /payments/{id}/refund` moves both to `refunded`; a replayed `charge.refunded`
   webhook is idempotent.
5. `sheet` on a consultation whose nutritionist has no enabled Connect account → 400.

## Validation
- `tests/test_payments_connect_service.py`, `tests/test_payments_consultation_charge.py`
  (fake stripe: Account/AccountLink, PaymentIntent with fee + transfer_data, Refund,
  webhook transitions).
- Live: Stripe test-mode Connect (Express test onboarding), a full patient charge with
  `4242…`, verify the fee split in the Stripe dashboard, a refund.
- Full suite green.
