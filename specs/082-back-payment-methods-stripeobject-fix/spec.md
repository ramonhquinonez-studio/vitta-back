# Feature Specification: Payment-methods StripeObject fix + on-device verification round

**Feature Branch**: `082-back-payment-methods-stripeobject-fix`
**Created**: 2026-09-09
**Status**: Done (2026-09-09)
**Type**: Bugfix (found running the Flutter clients on a real emulator against the live test backend)

## Context

`081` fixed the `StripeObject.get()` → `AttributeError` bug in the subscription /
webhook / connect / consultation-charges paths, but **missed `payment_methods`**.
Running `nutri_pro` on an Android emulator against the live test-mode backend, the
billing page's `GET /billing/payment-methods` call 500'd on first load (swallowed
client-side, but a real 500).

## Bug 1 — `payment_methods_service` StripeObject.get() (500)

`PaymentMethodsService.list_cards` / `add_card` / `_assert_owned` called `.get()` on
`PaymentMethod.list`, `Customer.retrieve`, `PaymentMethod.retrieve` results — the same
class of bug as `081`. **Fix**: `as_dict()` at every SDK boundary in the service.
`_to_card` already receives plain dicts (from the now-`as_dict`'d list/retrieve), so it
needed no change. `FakeStripe`-based tests still pass unchanged.

## Findings on the Flutter side (fixed in the client repos, noted here for the record)

- **`nutri_pro` + `nutri_app` `stripe_card_sheet.dart`** — the `CardField` bottom sheet
  overflowed ("BOTTOM OVERFLOWED BY 209 PIXELS") when the keyboard opened, because the
  sheet body wasn't scrollable. Wrapped in `SingleChildScrollView`.
- **`nutri_pro` `BillingController.currentPlan`** — opening the subscription card sheet
  calls `POST /billing/subscription-sheet`, which creates the Stripe subscription
  `default_incomplete` and **upserts the local `subscriptions` record immediately**
  (status `incomplete`). `currentPlan` matched by `plan_id` only, so the billing page
  showed "Pro — Plan actual" for a subscription the nutritionist never paid for.
  Fixed: `currentPlan` only honours an `active`/`trialing` subscription, else falls
  back to the default (free) plan. (The backend upsert is intentional — `verify` needs
  the record to reconcile — so the fix is client-side.)

## On-device verification (Android emulator, live test backend, `stripe listen`)

`nutri_pro`:
- Login → billing page: all `GET /billing/*` calls 200 (after the fix above) ✅
- "Cambiar de plan → Pro" → confirm → **native `flutter_stripe` `CardField` sheet
  renders**, field focuses, numeric keyboard appears ✅
- `POST /billing/subscription-sheet` → 200 with real `pi_…` / `ek_test_…` / `pk_test_…` ✅
- **Not completed**: the final `confirmPayment` tokenization — Stripe's `CardNumberEditText`
  rejects `adb shell input` synthetic events (a known SDK behaviour), so the last step
  (typing `4242…` + tapping Pagar) needs a human. Everything up to and including the SDK
  sheet is verified.

`nutri_app`: launches + patient login against the live backend ✅.

## Bug 2 — `POST /payments/consultations/{id}/sheet` 404 on every `nutri_app` payment

`nutri_app`'s "Historial de consultas" (`GET /me/consultations`) actually lists **past
appointments** — the `id` on each row is an appointment id, not a `consultations`-collection
id. But `ConsultationChargesService`'s resolver only looked up the `consultations`
collection → **404 "Consulta no encontrada"** for every "Pagar consulta" tap, and the
client showed a bare "El pago no se completó." with no sheet.

**Fix** — `consultation_charges_router.get_charges_service`'s `get_consultation` closure
falls back to `MongoAppointmentsRepository.get_for_owner(owner_id, ref_id)` when the
consultations lookup misses, returning `{patient_id, appointment_id: ref_id}`. The
`Payment` is then linked by `appointment_id`. Also `PatientPaymentsController` now
surfaces the backend `detail` message instead of a generic string, and stays silent
when the user simply closes the card sheet. Verified live: `POST
/payments/consultations/{appointment_id}/sheet` for `patient_demo` (linked to
`pro_demo`, who has Connect + `session_price`) → **200** with real PI credentials.

(Separately: the user's first attempt failed because they were logged in as their own
account whose nutritionist has no Connect account — the endpoint correctly 400s
"Este nutriólogo aún no puede recibir pagos" for that case once the id resolves.)

## Acceptance Criteria
1. `GET /billing/payment-methods` returns 200 against a real test account.
2. Full backend suite green (309).
3. The card sheet doesn't overflow with the keyboard open; an incomplete subscription
   shows the free plan as current.

## Validation
- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 309.
- Live: the emulator run above.
