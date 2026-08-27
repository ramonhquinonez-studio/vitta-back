# Implementation Plan: Per-Set Patient Workout Logging (Backend)

**Branch**: `057-back-per-set-workout-logging` | **Date**: 2026-08-26 | **Spec**: `specs/057-back-per-set-workout-logging/spec.md`

## Summary

Replaces the flat toggle-flip `workout_logs` document with a real per-set upsert, and separates the coach's bare completion flag (`coach_marked_done`) from the patient's detailed `sets` data so the two write paths can never clobber each other.

## Steps

1. New `app/schemas/workout_log.py`: `WorkoutSetLogIn{set_index, completed=True, reps_completed, weight_kg, rpe: Field(ge=1,le=10)}`, `WorkoutExerciseLogIn{workout_plan_id, day_index, exercise_index, sets: List[WorkoutSetLogIn]=[], comment}`.
2. `app/modules/me/presentation/router.py`: `POST /workout-logs/toggle` → `PUT /workout-logs/exercise`, body typed as `WorkoutExerciseLogIn`, calls `service.upsert_workout_log`.
3. `app/modules/me/application/me_service.py`: `toggle_workout_log` → `upsert_workout_log(user_id, payload: WorkoutExerciseLogIn)`.
4. `app/modules/me/domain/repositories.py` / `infrastructure/mongo_me_repository.py`: `toggle_workout_log` → `upsert_workout_log(..., sets, comment)` using `update_one(key, {"$set": {...}, "$setOnInsert": {"coach_marked_done": False}}, upsert=True)`, then re-fetch and serialize (`sets`, `comment`, `coach_marked_done`, `updated_at`).
5. `app/modules/patients/domain/repositories.py` / `infrastructure/mongo_patients_repository.py`: `toggle_workout_log` → `toggle_coach_workout_log(...)`, flips only `coach_marked_done` via `$set`+upsert (with `$setOnInsert` for `sets: []`/`comment: None` on first touch); `list_workout_logs`'s serializer updated to the new field shape.
6. `app/modules/patients/application/patients_service.py`: `toggle_workout_log` (public method, name unchanged) now calls `repository.toggle_coach_workout_log`, drops the `details` payload field entirely (coach path never sent per-set data).
7. `mongo_patients_repository.py`'s dashboard inactivity check: `(self._db.workout_logs, "completed_at")` → `(self._db.workout_logs, "updated_at")` (the old field no longer exists).
8. `tests/test_me_service.py`: fake repository's `toggle_workout_log` → `upsert_workout_log`; toggle-flip tests replaced with upsert/replace tests.
9. `tests/test_patients_service.py`: fake repository's `toggle_workout_log` → `toggle_coach_workout_log`, toggles a plain boolean instead of add/remove.

## Constraints

- No repository changes needed for the *workout plan* side (`WorkoutExerciseIn.sets` authoring) — this plan only touches the separate `workout_logs` collection.
- Coach-side write stays intentionally bare (no per-set detail) — matches `052-back-coach-workout-log-toggle`'s original scope.
