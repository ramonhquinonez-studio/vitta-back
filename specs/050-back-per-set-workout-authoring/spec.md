# Feature Specification: Per-Set Workout Authoring

**Feature Branch**: `050-back-per-set-workout-authoring`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

A screen-by-screen audit of TrainerStudio's coach app (32 screenshots checked against the actual `nutri_pro` code) surfaced the single biggest real authoring gap: `WorkoutExercise` was flat — one `sets` count, one `reps` count, one `weight_kg`, one `rest_seconds`, uniform across the whole exercise. A real coach workflow needs each set authored independently (a rep range, weight, RPE, and rest per set, any number of sets per exercise), and RPE didn't exist at all as an authoring target — only after the fact, on the patient's own log.

## In Scope

- `WorkoutExercise.sets` becomes a list of `WorkoutSet` objects, replacing the five flat fields. Each set: `reps_min, reps_max, weight_kg, duration_seconds, rpe (1–10), rest_seconds` — all optional, so a set can be reps-based (leaves `duration_seconds` null) or timed (leaves reps null).
- `name`, `notes`, `video_url` stay at the exercise level — unchanged.

## Out of Scope

- No repository or service code changes — `mongo_workout_plans_repository.py` already stores `days` as the raw request-body dict with no field-by-field mapping, and `workout_plans_service.py::_validate_payload` only ever checked `name` presence, never `sets`/`reps` content. Both keep working unmodified against the new shape.
- No migration — the dev database had zero `workout_plans` documents when this shipped; this is a clean shape change, not a versioned/backward-compatible one.
- `exercise_library`'s flat `default_sets/default_reps/default_weight_kg/default_duration_seconds/default_rest_seconds` are untouched — they represent "one representative set × a count," consumed by the frontend to seed `N` identical sets when inserting from the library, not a full multi-set prescription.
- `WorkoutLog` (the patient's logged performance) is unchanged — it stays a single overall summary per exercise. Per-set *logging* is a separate, larger follow-up not requested here.

## Baseline Behavior

`WorkoutExerciseIn`/`Out` had `sets: int | None`, `reps: int | None`, `weight_kg`, `duration_seconds`, `rest_seconds` — one value each, applying uniformly to however many sets the coach mentally intended. No RPE field existed anywhere on the authoring path.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `048-front-per-set-workout-authoring` (authoring UI) and `nutri_app` spec `054-front-per-set-workout-display` (patient-facing display).

## Acceptance Criteria

1. Given a coach creates an exercise with three differently-configured sets (a rep-range set, a fixed-reps set, and a timed set), then all three round-trip through `GET` exactly as submitted.
2. Given an RPE value outside 1–10 is submitted, then the request is rejected with `422`.
3. Given an exercise has zero sets, then it's still accepted (a coach can add the exercise first, fill in sets after) — only the exercise `name` is required, matching the pre-existing validation.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 210/210 green (fixture-only updates to `test_workout_plans_service.py`; no service logic changed, so no new test cases were needed beyond updating existing fixtures to the new shape).
- Live verification against the running backend: created a plan with one exercise carrying a rep-range set, a fixed-reps set, and a timed set — confirmed the exact structure round-trips through `POST` then `GET`; confirmed `rpe: 11` is rejected with `422`. Test account/data cleaned up after.
