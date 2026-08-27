# Feature Specification: Coach-Side Workout Log Toggle

**Feature Branch**: `052-back-coach-workout-log-toggle`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

From the "Coach App Screen Audit" punch list: today only the patient's own app can mark a workout-plan exercise as completed (`POST /me/workout-logs/toggle`). The nutritionist's `patient_detail_page` in `nutri_pro` can only display already-logged sets — there's no way for a coach to mark an exercise done on a client's behalf (useful during an in-person coaching session).

## In Scope

- New `POST /patients/{patient_id}/workout-logs/toggle`, nutritionist-facing, ownership-scoped (the calling nutritionist must own the patient), mirroring `POST /me/workout-logs/toggle`'s toggle-by-key semantics against the same `workout_logs` collection.

## Out of Scope

- No change to the patient-facing `/me/workout-logs/toggle` endpoint — both paths write to the same collection/shape, so a log made by either side is visible to both.
- No `nutri_app` (patient app) changes.
- No per-set completion (only per-exercise, matching the existing `WorkoutLog` shape — a single completion record per day/exercise index, not per set).

## Baseline Behavior

`patients_service.list_workout_logs` exists (read-only). No coach-facing write path to `workout_logs` existed before this.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `051-front-coach-workout-log-toggle` consumes this.

## Acceptance Criteria

1. Given a nutritionist owns a patient with an assigned workout plan, when they `POST /patients/{id}/workout-logs/toggle` with `workout_plan_id`/`day_index`/`exercise_index`, then a `workout_logs` document is created and `GET /patients/{id}/workout-logs` reflects it.
2. Given the same call is repeated with the same key, then the existing log is deleted (`{"completed": false}`) — a toggle, not an idempotent set.
3. Given the `patient_id` doesn't belong to the calling nutritionist, then the endpoint returns 404.
4. Given `workout_plan_id`, `day_index`, or `exercise_index` is missing from the payload, then the endpoint returns 400.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → full suite green.
- Live-curl verification: create a workout plan, assign it to a throwaway patient, toggle a log on then off via the new endpoint, confirm `GET /patients/{id}/workout-logs` reflects each state; confirm 404 on an unowned patient and 400 on a missing field. Test data cleaned up afterward.
