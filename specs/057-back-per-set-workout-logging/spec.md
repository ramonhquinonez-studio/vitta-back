# Feature Specification: Per-Set Patient Workout Logging (Backend)

**Feature Branch**: `057-back-per-set-workout-logging`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

Workout exercises are authored per-set (`050-back-per-set-workout-authoring`: each set has its own rep range/weight/RPE/rest), but a patient's logged performance was still a single flat summary per exercise (`sets_completed`/`reps_completed`/`weight_kg`/`rpe`/`comment`), not one entry per authored set. This closes that gap: logging now happens per set, matching authored targets one-for-one.

This also fixes a latent bug: the old `workout_logs` write path was a pure delete-then-insert "toggle," so every edit produced a new `completed_at` and (had it existed) a coach-side per-set write would have silently wiped a patient's logged data on the same key. The new path is a real upsert, and the coach's own toggle now flips one boolean field instead of touching the whole document.

## In Scope

- `workout_logs` documents restructured: `sets: [{set_index, completed, reps_completed, weight_kg, rpe}]`, `comment`, `coach_marked_done: bool`, `updated_at` — replacing the old flat `sets_completed/reps_completed/weight_kg/rpe/comment/completed_at` fields.
- `POST /me/workout-logs/toggle` replaced by `PUT /me/workout-logs/exercise` — patient-side upsert of a whole exercise's `sets` list + `comment` in one call.
- `POST /patients/{patient_id}/workout-logs/toggle` (coach-side) keeps its path/semantics as a toggle, but now flips only `coach_marked_done` via `$set`+upsert instead of delete/insert-whole-doc — preserves any `sets`/`comment` the patient already logged.
- `GET /me/workout-logs` and `GET /patients/{patient_id}/workout-logs` unchanged in path/method, new document shape.
- Practice dashboard's inactivity query (`mongo_patients_repository.py`'s `_db.workout_logs` activity check) updated from `completed_at` to `updated_at` to match the new field.

## Out of Scope

- No per-set completion from the coach side — `coach_marked_done` stays a single bare flag per exercise, matching `052-back-coach-workout-log-toggle`'s original "bare completion record, no details" scoping.
- No migration of existing `workout_logs` documents — dev DB confirmed empty of real log data, same precedent as every prior breaking schema change this session.
- No change to `WorkoutExerciseIn`'s authored-sets shape (`050-back-per-set-workout-authoring`) — this only changes how *logged* performance is stored.

## Baseline Behavior

`workout_logs` was one flat document per `(owner_id, patient_id, workout_plan_id, day_index, exercise_index)`, written via a delete-then-insert toggle on both the patient and coach paths — an "edit" cleared and recreated the whole document, losing the original `completed_at`.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `062-front-per-set-workout-logging-display` (coach-side stats/log display) and `nutri_app` spec `059-front-per-set-workout-logging` (patient-side per-set checkboxes) both consume this.

## Acceptance Criteria

1. Given a patient upserts a partial `sets` list for an exercise, when they `GET /me/workout-logs`, then the full list round-trips.
2. Given a patient upserts a second time with a different `sets` list, then the document is replaced, not duplicated (one document per exercise key, same as before).
3. Given a coach toggles their bare-completion flag on an exercise a patient has already logged sets for, then the patient's `sets`/`comment` survive unchanged and only `coach_marked_done` flips.
4. Given a coach toggles again, then `coach_marked_done` flips back.

## Validation

- Full backend unittest suite green (217/217 — one legacy toggle-flip test removed, two new upsert tests added).
- Live-curl verification against the running local server: upserted 1 set, then 2 sets (confirmed replace-not-duplicate), coach-toggled twice around the patient's data (confirmed `sets`/`comment` untouched, `coach_marked_done` flipped both ways). Test data cleaned up afterward via a direct Motor script.
