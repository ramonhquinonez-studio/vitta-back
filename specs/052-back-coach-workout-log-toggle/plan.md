# Implementation Plan: Coach-Side Workout Log Toggle

**Branch**: `052-back-coach-workout-log-toggle` | **Date**: 2026-08-26 | **Spec**: `specs/052-back-coach-workout-log-toggle/spec.md`

## Summary

Mirrors `MeService.toggle_workout_log`/`MongoMeRepository.toggle_workout_log` (`app/modules/me/...`), moved into the `patients` module and ownership-scoped like `list_workout_logs`, instead of patient-identity-scoped like the `me` original.

## Steps

1. `app/modules/patients/domain/repositories.py`: add `toggle_workout_log(owner_id, patient_id, *, workout_plan_id, day_index, exercise_index, details=None) -> dict | None` (`None` = patient not found/not owned).
2. `app/modules/patients/infrastructure/mongo_patients_repository.py`: `toggle_workout_log` — same owned-patient guard as `list_workout_logs`, then the identical toggle-by-key logic from `MongoMeRepository.toggle_workout_log` (delete existing `workout_logs` doc → `{"completed": False}`, else insert → `{"completed": True}`).
3. `app/modules/patients/application/patients_service.py`: `toggle_workout_log(owner_id, patient_id, payload)` — validates required fields (mirrors `MeService.toggle_workout_log`), raises `LookupError` on `None`.
4. `app/modules/patients/presentation/router.py`: `POST /{patient_id}/workout-logs/toggle`, mirrors `me` router's `toggle_my_workout_log` handler shape.
5. `tests/test_patients_service.py`: `_FakePatientsRepository.toggle_workout_log` (in-memory dict keyed by patient/plan/day/exercise); tests for toggle-on, toggle-off, missing fields, unowned patient.

## Constraints

- Writes to the same `workout_logs` collection/shape as the patient-facing endpoint — no schema divergence, no dual-write.
- Uses the calling nutritionist's own `owner_id` (from the auth token), never a client-supplied one.
