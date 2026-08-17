# Implementation Plan: Consultation History Linkage

**Branch**: `014-back-consultation-history-linkage` | **Date**: 2026-08-16 | **Spec**: `specs/014-back-consultation-history-linkage/spec.md`

## Summary

Add `body_composition_id` to appointments (mirroring the existing `plan_id` field end-to-end), add a `/me/consultations` endpoint that resolves both linkage fields into nested summaries, and seed real linked data for the demo patient.

## Steps

1. `appointments` module: add `body_composition_id: str | None` to `Appointment` (domain entity), `AppointmentsRepository` Protocol, `MongoAppointmentsRepository` (create/update/serialize), `AppointmentsService` (create/update), and the presentation router's `AppointmentCreate`/`AppointmentUpdate`/`AppointmentOut` + `_serialize`. Update `tests/test_appointments_service.py`'s fake repository and call sites.
2. `me` module: add `get_plan_summary(plan_id)` and `get_body_composition_by_id(id)` to `MeRepository` Protocol + `MongoMeRepository`; include `plan_id`/`body_composition_id` in `_serialize_appointment`.
3. `MeService.list_consultations(user_id)`: lists the patient's appointments, resolves `plan`/`body_composition` per item via the two new repository methods, sorts newest-first.
4. `GET /consultations` route in `me/presentation/router.py`.
5. `app/scripts/seed_ramon_consultation_history.py`: 4 past appointments for Ramon, each with its own `body_compositions` doc; 3 of the 4 linked to the existing real plan (`PLAN_ID` from `seed_ramon_real_plan.py`). Guarded to skip if appointments already exist for the patient (not idempotent beyond that guard).

## Constraints

- No Pydantic schema change needed for `/me/consultations` — it returns `list[dict]`, consistent with the rest of the `me` module's raw-dict response pattern (`/me/appointments`, `/me/plan/active`).
- `body_composition_id` write path exists only via `PATCH /appointments/{id}` (nutritionist-facing) — no in-repo caller sets it yet; seeded directly via Mongo for the demo patient.
