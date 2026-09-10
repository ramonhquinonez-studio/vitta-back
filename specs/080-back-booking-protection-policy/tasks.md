# Tasks: Booking protection — Phase 1

- [x] T1 — `app/modules/booking_policy/domain/` — `BookingPolicy` entity + `default_policy`; `BookingPolicyRepository` Protocol.
- [x] T2 — `application/booking_policy_service.py` — get (default fallback) / upsert (validated) / `resolve_for_patient` + `resolve_for_owner` (+ auto `_auto_policy_text`).
- [x] T3 — `infrastructure/mongo_booking_policy_repository.py` — `booking_policies` collection.
- [x] T4 — `presentation/router.py` (`GET`/`PUT /booking-policy/me`, `require_role("nutritionist")`, resolved-preview payload) + `app/routers/booking_policy.py` shim + mount in `app/main.py`.
- [x] T5 — `me`: `booking_policy` key on `GET /me/nutritionist_profile`; new `GET /me/booking-policy`; `MeService` takes an optional `booking_policy_service`, wired in `get_me_service`.
- [x] T6 — `me.request_appointment` consent gate (400 without `policy_accepted` when `needs_consent`) + `policy_snapshot` + `policy_accepted_at`; `MongoMeRepository.create_patient_appointment` + `_serialize_appointment` carry them.
- [x] T7 — `app/db/init_indexes.py` — `booking_policies` unique `owner_id`.
- [x] T8 — `tests/test_booking_policy_service.py` (10) + `tests/test_me_appointment_consent.py` (6); full suite 308 green.
- [x] T9 — Roadmap + `CLAUDE.md` + `docs/modules/architecture.md`.

## Notes
- Consent rejection is **400** (`ValueError` → the `me` router's existing handler), not
  422 as the spec draft wrote — matches the repo's validation-error convention.
- `Appointment` domain entity (owner-scoped module) was **not** touched — Phase 1's
  snapshot lives only on the patient-created path (`MongoMeRepository`). The owner-side
  `appointments` module gains policy/payment fields in Phase 2/3.
