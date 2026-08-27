# Implementation Plan: Practice-Wide Analytics Dashboard

**Branch**: `048-back-practice-dashboard` | **Date**: 2026-08-25 | **Spec**: `specs/048-back-practice-dashboard/spec.md`

## Summary

One new aggregate endpoint on the existing `patients` router, built from plain `count_documents`/`find`/`distinct` calls (no aggregation pipeline), plus a `created_at` field completing `Patient`'s creation paths.

## Steps

1. `app/modules/patients/domain/entities.py`: `Patient.created_at: datetime | None = None`.
2. `app/modules/patients/infrastructure/mongo_patients_repository.py`: `create_for_owner` sets `created_at=datetime.utcnow()`; `_to_entity` maps it. New `get_dashboard(owner_id) -> dict`:
   - `total_patients`, `new_patients_this_month`, `upcoming_appointments_this_week`, `completed_appointments_this_month` via `count_documents`.
   - Fetch all of the owner's `{_id, name}` patient docs.
   - For each of `measurements.at`, `food_diary_entries.at`, `checkin_responses.submitted_at`, `workout_logs.completed_at`, `appointments.start`, run `collection.distinct("patient_id", {"patient_id": {"$in": ids}, field: {"$gte": cutoff_14d}})` and union into an `active_ids` set.
   - `inactive_patients` = patients not in `active_ids`, as `[{id, name}]`.
3. `app/modules/patients/domain/repositories.py`: `PatientsRepository.get_dashboard(owner_id) -> dict` Protocol method.
4. `app/modules/patients/application/patients_service.py::get_dashboard`: pure pass-through to the repository (no LookupError — a nutritionist with zero patients just gets zeros).
5. `app/modules/patients/presentation/router.py`: `GET /dashboard`, registered right after `POST ""` — **before** `GET /{patient_id}` (line ~151) to avoid the path param swallowing it. Calls `get_nutritionist_profile_service` (imported directly from `nutritionist_profile`'s router, mirroring how `get_billing_service` is already imported the same way in this file) to resolve `session_price`/`session_price_currency`, merges `estimated_revenue_this_month`/`revenue_currency` into the response.
6. `app/db/init_indexes.py`: `patients` gains `(owner_id, created_at)`; new `checkin_responses` section with `(patient_id, submitted_at)`.
7. Tests: `tests/test_patients_service.py`'s `_FakePatientsRepository` gains `dashboard_data`/`get_dashboard`; one pass-through test.

## Constraints

- No aggregation pipeline — matches the rest of this module's plain-query style.
- `get_dashboard`'s router handler is the one place in `patients`' presentation layer that reaches into another module's service directly for composition (same established pattern as the existing billing-quota wiring), not a new convention.
