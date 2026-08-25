# Implementation Plan: Workout Plans

**Branch**: `045-back-workout-plans` | **Date**: 2026-08-25 | **Spec**: `specs/045-back-workout-plans/spec.md`

## Summary

A new `workout_plans` module mirroring `plans`' exact dict-based shape, plus small `me`/`patients` extensions for the patient-side active-plan/completion-toggle and nutritionist-side adherence read — following the same extension pattern used for `043-back-progress-photos` and `044-back-checkin-forms`.

## Steps

1. `workout_plans/domain/repositories.py`: `WorkoutPlansRepository` Protocol (`create_for_owner, list_for_owner, get_for_owner, update_for_owner, delete_for_owner, patient_exists_for_owner, assign_plan`) — same shape as `PlansRepository` minus the attachment methods (not needed here).
2. `workout_plans/application/workout_plans_service.py`: CRUD + validation (name required, ≥1 day, every exercise has a name) + `assign_plan` (same not-found/patient-ownership checks as `PlansService.assign_plan`).
3. `workout_plans/infrastructure/mongo_workout_plans_repository.py`: same owner-scoped CRUD pattern as `MongoPlansRepository`, collections `workout_plans`/`workout_plan_assignments`.
4. `app/schemas/workout_plan.py`: `WorkoutExerciseIn/WorkoutDayIn/WorkoutPlanCreate/WorkoutPlanUpdate/WorkoutPlanOut`.
5. `workout_plans/presentation/router.py` (`prefix="/workout-plans"`, nutritionist-only): `POST/GET /`, `GET/PATCH/DELETE /{id}`, `POST /{id}/assign`.
6. `app/routers/workout_plans.py` wrapper + `main.py` wiring.
7. `app/db/init_indexes.py`: indexes on `workout_plans`, `workout_plan_assignments`, `workout_logs` mirroring `plans`/`plan_assignments`' existing index set.
8. `me/domain/repositories.py` + `infrastructure/mongo_me_repository.py`: `get_active_workout_plan` (same most-recent-assignment resolution as `get_active_plan`), `list_workout_logs`, `toggle_workout_log` (find-or-create-or-delete against `workout_logs`, scoped by the exact `(owner_id, patient_id, workout_plan_id, day_index, exercise_index)` tuple).
9. `me/application/me_service.py`: `get_active_workout_plan`, `list_workout_logs`, `toggle_workout_log` (resolves `owner_id` from the patient's linked record, same `LookupError`-if-unassigned pattern as `submit_checkin_response`).
10. `me/presentation/router.py`: `GET /workout-plan/active`, `GET /workout-logs`, `POST /workout-logs/toggle`.
11. `patients/domain/repositories.py` + `infrastructure`/`application`/`presentation`: `list_workout_plan_assignments` (mirrors `list_plan_assignments`'s plan-name-join pattern), `list_workout_logs` (mirrors `list_measurements`).
12. Tests: `tests/test_workout_plans_service.py` (fake repository), extensions to `tests/test_me_service.py` and `tests/test_patients_service.py`.

## Constraints

- `WorkoutPlan.days` is an explicit, required array (`WorkoutPlanCreate.days: List[WorkoutDayIn]`) — no `duration_days`-driven flat-list rotation like `plans` uses; a training split doesn't repeat the way meal slots do.
- `toggle_workout_log` is a single idempotent switch (create-if-absent/delete-if-present), not an append-only log — re-toggling the same exercise removes the earlier completion rather than stacking entries.
