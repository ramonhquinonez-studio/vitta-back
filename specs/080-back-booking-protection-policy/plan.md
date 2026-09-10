# Implementation Plan: Booking protection — Phase 1

**Branch**: `080-back-booking-protection-policy` | **Spec**: `specs/080-back-booking-protection-policy/spec.md`

## Phase 1 steps
1. `app/modules/booking_policy/domain/entities.py` — `BookingPolicy` frozen dataclass +
   `DEFAULT_POLICY` factory. `domain/repositories.py` — `BookingPolicyRepository` Protocol.
2. `application/booking_policy_service.py` — `BookingPolicyService`:
   - `get_for_owner(owner_id)` → saved or `DEFAULT_POLICY`.
   - `upsert_for_owner(owner_id, payload)` → validate (bounds table in spec), persist,
     return the entity.
   - `resolve_for_patient(owner_id, session_price, currency)` → resolved dict incl.
     `amount_due_cents` and an auto `policy_text` when the stored one is null.
   - `_auto_policy_text(resolved)` — Spanish summary builder.
3. `infrastructure/mongo_booking_policy_repository.py` — `booking_policies` collection,
   keyed by bare `owner_id` string (same as `stripe_customers`).
4. `presentation/router.py` — `GET /booking-policy/me`, `PUT /booking-policy/me`
   (`require_role("nutritionist")`); `app/routers/booking_policy.py` shim; mount in
   `app/main.py`.
5. `me` integration:
   - `MeService`/`MongoMeRepository`: resolve the owner's policy in
     `get_nutritionist_profile` (add `booking_policy` key) and a new
     `get_booking_policy(user_id)` → `GET /me/booking-policy`.
   - `request_appointment`: consent gate + snapshot + `policy_accepted_at`.
   - Wire a `BookingPolicyService` (or just the repo + a small resolver) into
     `MeService` construction — mirror how the appointments-repo / patients-repo
     optional deps were injected in `076`.
6. `Appointment` entity + `mongo_appointments_repository` + `mongo_me_repository`
   create/serialize paths: carry `policy_snapshot`, `policy_accepted_at`.
7. `app/db/init_indexes.py` — `booking_policies` unique `owner_id`.
8. Tests: `tests/test_booking_policy_service.py`, `tests/test_me_appointment_consent.py`.
9. Docs: roadmap, `CLAUDE.md`, `docs/modules/architecture.md`.

## Decisions
- **Own module, not `nutritionist_profile` fields** — keeps the appointments/me
  services depending on a small focused service, and mirrors how `079` kept
  `stripe_connect_accounts` out of the profile.
- **Default returned, not persisted on first read** — no write on a GET.
- **Snapshot is a plain dict on the appointment**, not a typed sub-entity — it's an
  audit record, never queried by field, and its shape is the resolved-policy shape.
- **Phase 1 adds no Stripe import anywhere.**
