# Implementation Plan: Patient → nutritionist payments (Stripe Connect)

**Branch**: `079-back-payments-connect-consultations` | **Spec**: `specs/079-back-payments-connect-consultations/spec.md`

## Pre-work (ops, before code)
- Enable Connect in the Stripe dashboard; set branding, statement descriptor, fee.
- Confirm MXN + nutritionist country is supported for Express connected-account payouts.

## Steps
1. Settings: `PLATFORM_FEE_BPS`.
2. `nutritionist_profile`: `stripe_connect_account_id` + cached Connect flags; migration
   note (existing profiles get `None`).
3. `Consultation` entity/schema/repo: `price_cents`, `currency`, `payment_status`,
   `payment_id`; default price from the profile.
4. `app/modules/payments/` (extend the `077` module):
   - `application/connect_service.py` — `account_link(owner)`, `status(owner)`.
   - `domain/entities.py` — `Payment`; `infrastructure/mongo_payments_repository.py`
     (`payments` collection).
   - `application/consultation_charges_service.py` — `create_sheet(consultation_id,
     patient)`, `verify(payment_id)`, `refund(payment_id, nutritionist)`, list helpers.
     Injects `stripe` + `StripeCustomers` + repos.
   - `presentation/router.py` — the 7 routes.
5. Webhook handlers module — register with `077`'s dispatcher.
6. Wire consultation `payment_status` updates into `consultations_service` where
   relevant (a consultation can't be "billed" twice).
7. Tests: 2 files with the shared `FakeStripe` extended (Account, AccountLink, Refund,
   `transfer_data`).
8. Live Connect test-mode smoke; full suite; roadmap + CLAUDE.md.

## Decisions
- **Destination charges** (`transfer_data.destination` + `application_fee_amount`), not
  separate charges + transfers — simpler, Vitta is merchant of record, the fee is
  automatic.
- **Payment record on `payments`, status mirror on `Consultation`** — the consultation
  is what the UI shows "unpaid/paid" against; `payments` is the ledger.
- **`/verify` mirrors `078`** — immediate client answer + webhook as the source of
  truth.
- Charge trigger deferred to the client specs — backend stays mechanism-only.
