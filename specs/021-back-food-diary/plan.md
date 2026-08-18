# Implementation Plan: Food Diary Persistence

**Branch**: `021-back-food-diary` | **Date**: 2026-08-17 | **Spec**: `specs/021-back-food-diary/spec.md`

## Summary

Extends the `me` module (patient read/write, mirroring `measurements` exactly) and the `patients` module (owner read, mirroring `body_compositions` exactly).

## Steps

1. `me/domain/repositories.py`: `list_food_diary_entries`/`create_food_diary_entry`.
2. `me/infrastructure/mongo_me_repository.py`: same `at`-parsing + `owner_id`-optional pattern as `create_measurement`; `_serialize_food_diary_entry` helper.
3. `me/application/me_service.py`: `list_food_diary_entries` (empty list for a patient-less user), `add_food_diary_entry` (`dish` required, resolves `owner_id` via `_require_patient`).
4. `me/presentation/router.py`: `GET`/`POST /me/food_diary_entries`, reusing the `payload: dict[str, Any]` raw-body convention already used by `/me/measurements` (no new Pydantic schema).
5. `patients/domain/repositories.py` + `infrastructure/mongo_patients_repository.py` + `application/patients_service.py` + `presentation/router.py`: `list_food_diary_entries`, verbatim mirror of `list_body_compositions` (`019`).
6. `app/db/init_indexes.py`: `food_diary_entries` compound index on `(patient_id, at)`.
7. `tests/test_me_service.py`: fake gains `food_diary_entries`/`create_food_diary_entry`; 4 new tests. `tests/test_patients_service.py`: fake gains `food_diary_entries`; 2 new tests.

## Constraints

- Reused the raw-`dict` payload convention from `/me/measurements` rather than adding a new Pydantic schema — this module already established that pattern for patient-self-log endpoints, and the field set here is exactly as simple.
- This models "eating out" logging specifically (the one real patient-facing flow that exists), not a broader free-text diary — see spec's Out of Scope.
