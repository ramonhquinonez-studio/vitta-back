# Feature Specification: Workout Plans

**Feature Branch**: `045-back-workout-plans`
**Created**: 2026-08-25
**Status**: Draft
**Type**: Feature

## Objective

Phase 2 of the TrainerStudio gap analysis (following the four completed Phase 1 engagement slices — chat, progress photos, trend graphs, check-in forms). A nutritionist can author a day-structured workout plan and assign it to a patient; the patient can see their active plan and mark exercises complete, with completion visible back to the nutritionist as an adherence signal. Fully greenfield — no `exercise`/`workout`/`training` concept existed anywhere in this codebase before this spec.

## In Scope

- New `workout_plans` module, structurally mirroring the existing `plans` (meal plan) module's shape and conventions exactly (dict-based repository, `require_role("nutritionist")`-gated router, `LookupError`→404/`ValueError`→400): `WorkoutExercise{name, sets, reps, weight_kg, duration_seconds, rest_seconds, notes, video_url}`, `WorkoutDay{label, exercises}`, `WorkoutPlan{id, owner_id, name, goal, days, created_at, updated_at}`.
- Nutritionist CRUD under `/workout-plans`: create, list, get, full-replace update, delete, plus `POST /workout-plans/{id}/assign` — an append-only `workout_plan_assignments` collection (`{owner_id, plan_id, patient_id, assigned_at}`), same shape as `plan_assignments`, "active plan" always meaning the most recent assignment.
- Patient-side, extending `me` (matching the established `me`-duplicates-read/write-against-shared-collections precedent): `GET /me/workout-plan/active`, `GET /me/workout-logs`, `POST /me/workout-logs/toggle`.
- **Deliberate deviation from the meal-plan pattern**: exercise completion is server-persisted in a new `workout_logs` collection (`{owner_id, patient_id, workout_plan_id, day_index, exercise_index, completed_at}`), not on-device-only like meal-plan completion (`PlanCompletionLocalDataSource` in `nutri_app`, which never syncs to the backend or reaches the nutritionist at all). A single toggle endpoint creates the log if absent / deletes it if present.
- Nutritionist-side adherence reading, extending `patients` (mirrors `list_measurements`/`list_checkin_responses`): `GET /patients/{patient_id}/workout-plan-assignments`, `GET /patients/{patient_id}/workout-logs`.

## Out of Scope

- No flat-list/day-rotation fallback (unlike `plans`' `duration_days`-driven rotation) — `WorkoutPlan.days` is the direct, explicit schema; a training split is inherently day-shaped in a way a repeating meal structure isn't.
- No video upload/hosting — `video_url` is a plain string field for a patient to paste an existing YouTube/Vimeo link.
- No numeric rollups (total volume, 1RM tracking, etc.) over logged exercises — a natural future extension, not built here.

## Baseline Behavior

No workout/training concept existed anywhere in the stack. The closest adjacent feature, `nutri_app`'s `my_progress` module, is a patient-typed, ad-hoc, on-device-only exercise checklist with no nutritionist involvement — unrelated to this spec and left untouched.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `043-front-workout-plans` (authoring, assignment, adherence view) and `nutri_app` spec `051-front-workout-plan-detail` (viewing, completion toggling).

## Acceptance Criteria

1. Given a nutritionist creates a 2-day workout plan and assigns it to a patient, when the patient calls `GET /me/workout-plan/active`, then the full day/exercise structure is returned.
2. Given the patient toggles an exercise via `POST /me/workout-logs/toggle`, then it appears in their own `GET /me/workout-logs` and the nutritionist's `GET /patients/{patient_id}/workout-logs`.
3. Given the same exercise is toggled again, then it's removed from both — an idempotent complete/incomplete switch, not an accumulating log.
4. Given a nutritionist who doesn't own that patient, then reading their workout plan/logs is refused with `404`.
5. Given a nutritionist reads a workout plan they don't own directly by id, then `GET /workout-plans/{id}` is refused with `404`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 197/197 green (8 new `test_workout_plans_service.py` cases, 6 new `test_me_service.py` cases, 3 new `test_patients_service.py` cases).
- Live verification against the running backend: created a 2-day plan (strength + rest day) with real sets/reps/weight/duration/rest fields, assigned it, confirmed the patient's active-plan endpoint returns it, toggled one exercise complete then incomplete and confirmed both the patient's and nutritionist's log views reflect each state change, confirmed cross-tenant reads of both the plan and the logs are refused with `404`. Test accounts/data cleaned up after.
