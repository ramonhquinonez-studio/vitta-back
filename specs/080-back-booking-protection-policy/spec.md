# Feature Specification: Booking protection — policy, deposits, cancellation rules

**Feature Branch**: `080-back-booking-protection-policy`
**Created**: 2026-09-09
**Status**: Phase 1 Done (2026-09-09); Phases 2–5 designed, not built
**Type**: Feature (large, multi-phase, cross-repo)

## Objective

Protect the nutritionist's calendar: money changes hands **at booking time** (deposit
or full prepayment), and a pre-accepted, per-nutritionist policy governs what happens
to it on reschedule / cancellation / no-show. Builds on `079-back-payments-connect-consultations`
(Connect destination charges, `Payment` ledger, refund path, webhook idempotency).

Pairs with `nutri_pro` `111` (nutritionist configures the policy, refunds, marks no-show)
and `nutri_app` `068` (patient sees + accepts the policy, pays, reschedules/cancels).
Partially supersedes the drafted `nutri_app` `067` (which charges an *existing*
consultation; this charges a *booking*).

## Design decisions (from the user, 2026-09-09)

1. Confirmation flow is **per-nutritionist** (`requires_approval` toggle).
2. **Deposit** is the default payment mode.
3. Within-policy refunds are **100%** — the platform absorbs the Stripe processing fee
   (Stripe does not return it on refunds).
4. On a forfeit (late cancel / no-show), the nutritionist keeps their share and the
   **platform keeps its application fee**.
5. Reschedule limit is **nutritionist-configurable** (count + minimum notice).
6. Slot-hold window during checkout is **nutritionist-configurable**.

## The policy (per nutritionist)

A `BookingPolicy` document keyed by `owner_id`. A sensible default is returned when the
nutritionist hasn't saved one.

| Field | Type | Default | Notes |
|---|---|---|---|
| `payment_mode` | `none` \| `deposit` \| `full` | `none` | `deposit`/`full` require Connect `charges_enabled` |
| `deposit_type` | `percentage` \| `fixed` | `percentage` | |
| `deposit_value` | float | `30` | percent (0–100) or a fixed amount in the profile currency |
| `requires_approval` | bool | `false` | true = request → approve → pay-link → confirmed |
| `reschedule_limit` | int | `1` | 0 = no self-reschedule; `-1` sentinel = unlimited |
| `reschedule_notice_hours` | int | `24` | self-reschedule must be ≥ this before current start |
| `cancellation_cutoff_hours` | int | `24` | cancel ≥ this before start → full refund; inside → forfeit |
| `slot_hold_minutes` | int | `15` | unpaid `pending_payment` appointments expire after this |
| `policy_text` | str \| null | null | editable override; when null the API returns an auto-generated Spanish summary |
| `updated_at` | datetime | | |

Validation: `deposit_value` in `[0, 100]` for percentage / `> 0` for fixed;
`reschedule_limit >= -1`; hour/minute fields `>= 0`; `slot_hold_minutes` in `[5, 120]`.

### Resolved (patient-facing) policy

Computed from `BookingPolicy` + `nutritionist_profile.session_price`:
`{ payment_mode, amount_due_cents, currency, deposit_type, deposit_value,
requires_approval, reschedule_limit, reschedule_notice_hours,
cancellation_cutoff_hours, policy_text }` where `amount_due_cents` is the deposit
(or full price) in cents, or `0` when `payment_mode == none` or the profile has no price.

## Scope — Phase 1 (this spec's initial ship): policy + disclosure + consent

No money moves. Ships the config, the patient-visible disclosure, and immutable consent
capture — the foundation every later phase builds on, fully testable without Stripe.

- **New module `app/modules/booking_policy/`** — `domain` (`BookingPolicy` entity +
  repo Protocol), `application` (`BookingPolicyService`: `get_for_owner` with default
  fallback, `upsert_for_owner` with validation, `resolve_for_patient(owner_id)` →
  resolved dict + auto `policy_text`), `infrastructure` (`MongoBookingPolicyRepository`,
  `booking_policies` collection, unique `owner_id`), `presentation`
  (`GET /booking-policy/me`, `PUT /booking-policy/me` — `require_role("nutritionist")`).
- **Router shim** `app/routers/booking_policy.py`; mount in `app/main.py`.
- **Patient read** — `GET /me/nutritionist_profile` response gains a `booking_policy`
  key (the resolved policy) so the app can show terms before booking. Add
  `GET /me/booking-policy` too (thin, same resolved payload) for the booking screen.
- **`Appointment`** gains `policy_snapshot: dict | None` and `policy_accepted_at:
  datetime | None`. `POST /me/appointments` payload gains `policy_accepted: bool`.
  `MeService.request_appointment`: when the owner's resolved policy is not a plain
  `none`/no-approval nothing-burger (i.e. `payment_mode != none` **or**
  `requires_approval`), require `policy_accepted is True` (422 with a clear message
  otherwise), then snapshot the resolved policy and stamp `policy_accepted_at = now`.
- **No enforcement** of reschedule/cancel limits, no charge, no approval state machine
  yet — those are Phases 2–3. Phase 1's `policy_snapshot` is already the audit record
  they'll read.
- `app/db/init_indexes.py`: `booking_policies` unique `owner_id`.

### Phase 1 tests
- `tests/test_booking_policy_service.py` — defaults, validation bounds, `resolve_for_patient`
  math (percentage + fixed + no-price), auto `policy_text` generation.
- `tests/test_me_appointment_consent.py` — request rejected without consent when the
  policy needs it; accepted + snapshot stored when consent given; still works with no
  policy / `none` mode and no consent field.

## Scope — later phases (design, not built here)

### Phase 2 — deposit at booking
- `POST /appointments/{id}/deposit/sheet` (or `/me/appointments/{id}/deposit/sheet`) —
  destination charge for `amount_due_cents`, reusing `ConsultationChargesService`'s PI
  construction (`application_fee_amount` = `PLATFORM_FEE_BPS`, `transfer_data.destination`).
  Reuse `POST /payments/{id}/verify`.
- `Appointment` status `pending_payment` → `confirmed`; `payment_id`, `payment_kind`
  (`deposit`|`full`), `amount_paid_cents`, `hold_expires_at`.
- A sweeper (cron in `app/scripts/` or a TTL-ish periodic task) expires unpaid
  `pending_payment` appointments past `hold_expires_at` and releases the slot.
- `requires_approval`: request (free, `pending_approval`) → nutritionist
  `POST /appointments/{id}/approve` → `pending_payment` + a pay link valid N hours →
  patient pays → `confirmed`; else `expired`.
- Nutritionist refund action already exists (`POST /payments/{id}/refund`); extend to
  set the appointment status.

### Phase 3 — cancellation / reschedule engine
- `GET /me/appointments/{id}/cancellation-preview` → `{ outcome: refund|forfeit,
  refund_cents, reason }` from the snapshot + `cancellation_cutoff_hours` vs now.
- `POST /me/appointments/{id}/cancel` enforces: before cutoff → refund
  (`Refund.create(payment_intent, reverse_transfer=True, refund_application_fee=True)`);
  inside cutoff / no-show → **no refund**, status `canceled`/`no_show`.
- `POST /me/appointments/{id}/reschedule` enforces `reschedule_limit` +
  `reschedule_notice_hours`; `reschedule_count` on the appointment; moves the same
  `payment_id`, no new charge.
- Nutritionist-initiated cancel → always full refund; reschedule → never counts, never
  forfeits. `POST /appointments/{id}/no-show` (owner, only after start time).
- Webhook reconciliation for `charge.refunded` already exists (`079`).

### Phase 4 — deposit → balance credit
- `deposit` mode: consultation Cierre step collects `session_price − deposit` via the
  existing `ConsultationChargesService`. `full` mode: consultation charge step is
  skipped (already paid). Link both `Payment`s to the appointment/consultation.

### Phase 5 — polish
- Dispute-evidence export (policy snapshot + consent + slot + amount as a packet).
- "Cancela gratis hasta <fecha>" reminders. No-show / forfeited-revenue analytics on
  the dashboard.

## Out of scope (all phases)
- Packages / multi-session prepay; wallet balance; tipping.
- Web payments for bookings (patients pay on their phone — matches `067`).
- Insurance / third-party billing.

## Documentation Impact
- `nutri_back` `specs/SPEC_ROADMAP.md`, `CLAUDE.md`, `docs/modules/architecture.md`.
- Cross-repo: `nutri_pro` `111`, `nutri_app` `068` (+ supersession note on `067`).

## Acceptance Criteria — Phase 1
1. A nutritionist can `GET`/`PUT` their booking policy; invalid values are rejected;
   an unsaved policy returns the documented defaults.
2. `GET /me/nutritionist_profile` and `GET /me/booking-policy` return the resolved
   policy with `amount_due_cents` correct for percentage, fixed, and no-price cases.
3. `POST /me/appointments` is rejected (422) without `policy_accepted` when the owner's
   policy requires payment or approval; on success the appointment carries an immutable
   `policy_snapshot` and `policy_accepted_at`.
4. A nutritionist with a `none` / no-approval policy books exactly as today — no consent
   field needed, no snapshot.
5. Full suite green; every new payment-adjacent path stays free of Stripe (Phase 1
   touches no Stripe SDK).

## Validation
- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`.
- Manual `curl`: set a policy, read it as a patient, book with/without consent.
