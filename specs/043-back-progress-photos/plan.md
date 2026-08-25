# Implementation Plan: Progress Photos and Nutritionist Visibility into Self-Logged Measurements

**Branch**: `043-back-progress-photos` | **Date**: 2026-08-25 | **Spec**: `specs/043-back-progress-photos/spec.md`

## Summary

Two small, independent additions to two existing modules: the `me` module's `POST /me/measurements` gains an attachment (multipart, mirroring `body_compositions`'s existing upload shape); the `patients` module gains a read-only `measurements` endpoint next to its existing `body_compositions`/`food_diary_entries`/`plan_assignments` sub-resources.

## Steps

1. `app/modules/me/presentation/router.py`: `POST /measurements` becomes multipart (`Form(...)` fields + optional `file: UploadFile`), calling `save_upload(file, subfolder=f"measurements/{user_id}")` on a file present, folding `attachment_url`/`attachment_type` into the existing `payload` dict passed to `MeService.add_measurement`.
2. `app/modules/me/infrastructure/mongo_me_repository.py`: `create_measurement` persists `attachment_url`/`attachment_type`; `_serialize_measurement` returns them.
3. `app/modules/patients/domain/repositories.py`: add `list_measurements(owner_id, patient_id)` to the `PatientsRepository` Protocol.
4. `app/modules/patients/infrastructure/mongo_patients_repository.py`: implement it — same ownership-check-then-query shape as `list_body_compositions`, querying the `measurements` collection (owned by the `me` module but read here, matching the pattern already used for the reverse direction).
5. `app/modules/patients/application/patients_service.py`: `list_measurements` — same `LookupError`-on-not-owned shape as every sibling list method on this service.
6. `app/modules/patients/presentation/router.py`: `GET /{patient_id}/measurements`, same pattern as `list_patient_body_compositions`.
7. Tests: extend `tests/test_me_service.py`'s fake repository to record the payload passed to `create_measurement`; extend `tests/test_patients_service.py`'s fake repository with a `measurements` dict.

## Constraints

- No change to the `messages`/`measurements` collection's write path from any other module — this only adds fields to an existing write and a new read.
- The nutritionist-read endpoint deliberately reuses the exact ownership-check pattern already established by `list_body_compositions`/`list_food_diary_entries`/`list_plan_assignments` on the same router, not a new pattern.
