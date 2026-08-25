# Implementation Plan: Per-Tenant Branding Upload + Exercise Library + Logged Session Details

**Branch**: `046-back-branding-and-session-logging` | **Date**: 2026-08-24 | **Spec**: `specs/046-back-branding-and-session-logging/spec.md`

## Summary

A logo-upload endpoint plus a small `me` read-path fix on `nutritionist_profile`, `workout_logs` schema/endpoint extension for logged performance details, and a new `exercise_library` module mirroring `equivalencies`' exact shape.

## Steps

1. `nutritionist_profile/presentation/router.py`: `POST /me/logo` (`File`/`UploadFile`, `save_upload(file, subfolder=f"nutritionist_profile/{owner_id}")`) → `service.update_my_profile(owner_id, {"logo_url": logo_url})`.
2. `me/infrastructure/mongo_me_repository.py`: `get_nutritionist_profile`'s returned dict gains `practice_name`/`logo_url`/`brand_color` (already present on the underlying Mongo document, just not projected through).
3. `me/infrastructure/mongo_me_repository.py`: `toggle_workout_log` gains `details: dict | None = None`; inserts `sets_completed/reps_completed/weight_kg/rpe/comment` from `details` on create; returns `{"completed": bool}` (was a bare `bool`). New `_serialize_workout_log` helper reused by `list_workout_logs`.
4. `me/domain/repositories.py`: `toggle_workout_log` Protocol signature updated to match (`details` param, `-> dict` return).
5. `me/application/me_service.py`: `toggle_workout_log` passes `payload.get("details")` through and returns the repository's dict directly.
6. `patients/infrastructure/mongo_patients_repository.py`: `list_workout_logs` serializes the new fields alongside the existing ones.
7. New `exercise_library` module: `domain/repositories.py` (`ExerciseLibraryRepository` Protocol — `list_for_owner, create_for_owner, delete_for_owner`), `application/exercise_library_service.py` (validates `name` required), `infrastructure/mongo_exercise_library_repository.py` (collection `exercise_library`), `presentation/router.py` (`prefix="/exercise-library"`, nutritionist-only).
8. `app/schemas/exercise_library.py`: `ExerciseLibraryItemCreate`/`ExerciseLibraryItemOut`.
9. `app/routers/exercise_library.py` wrapper + `main.py` wiring.
10. `app/db/init_indexes.py`: index on `exercise_library` (`owner_id`, `name`).
11. Tests: `tests/test_exercise_library_service.py` (new, fake-repo pattern), `tests/test_me_service.py` extension (`toggle_workout_log` details round-trip).

## Constraints

- `logo_url` stays a plain string field end-to-end — the upload endpoint is the only new surface; no schema migration needed since the field already existed on `NutritionistProfile`.
- `exercise_library` mirrors `equivalencies`' shape exactly (same CRUD verbs, same ownership-scoping pattern) rather than inventing a new convention.
