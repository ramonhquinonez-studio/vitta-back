# Implementation Plan: Plan Assignment History

**Branch**: `024-back-plan-assignment-history` | **Date**: 2026-08-18 | **Spec**: `specs/024-back-plan-assignment-history/spec.md`

## Summary

Mirrors the existing `list_body_compositions`/`list_food_diary_entries` pattern in the `patients` module exactly: ownership check via `patients.find_one`, then a sorted cursor over a related collection.

## Steps

1. `patients/domain/repositories.py`: `list_plan_assignments(owner_id, patient_id) -> list[dict] | None` on the `PatientsRepository` protocol.
2. `patients/infrastructure/mongo_patients_repository.py`: query `plan_assignments` filtered by `patient_id`, sorted by `assigned_at` desc; for each, look up `plans.find_one({"_id": plan_id})` to embed a `plan_name` snapshot (`None` if the plan no longer exists).
3. `patients/application/patients_service.py`: `list_plan_assignments` — same `LookupError` on `None` (patient not owned) convention as the other list methods.
4. `patients/presentation/router.py`: `GET /{patient_id}/plan_assignments`.
5. `tests/test_patients_service.py`: fake repository gains `plan_assignments` dict + `list_plan_assignments`; 2 new tests (returns history, rejects non-owned patient).

## Constraints

- Read-only history — does not touch `get_active_plan`'s "most recent wins" resolution, which stays exactly as-is.
