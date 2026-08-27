# Implementation Plan: Per-Set Workout Authoring

**Branch**: `050-back-per-set-workout-authoring` | **Date**: 2026-08-26 | **Spec**: `specs/050-back-per-set-workout-authoring/spec.md`

## Summary

A pure Pydantic-schema-shape change — one new nested schema, one field replaced — with zero repository or service code touched, since both already operate on raw/opaque dicts for `days`/`exercises`.

## Steps

1. `app/schemas/workout_plan.py`: new `WorkoutSetIn{reps_min: int|None (ge=0), reps_max: int|None (ge=0), weight_kg: float|None, duration_seconds: int|None (ge=0), rpe: int|None (ge=1, le=10), rest_seconds: int|None (ge=0)}`. `WorkoutExerciseIn` drops `sets/reps/weight_kg/duration_seconds/rest_seconds` as scalars, gains `sets: List[WorkoutSetIn] = Field(default_factory=list)`.
2. No other file changes — verified `mongo_workout_plans_repository.py::create_for_owner`/`update_for_owner` pass `payload.get("days", [])` straight through with no per-field mapping, and `workout_plans_service.py::_validate_payload` only inspects `exercise.get("name")`.
3. Tests: `tests/test_workout_plans_service.py`'s `_SAMPLE_DAYS` fixture and the blank-name-rejection test's inline payload updated to the new `sets: [...]` shape (cosmetic — the fake repository and service logic don't inspect set contents either).

## Constraints

- `WorkoutSetIn`'s fields are all optional with no cross-field validation (e.g. `reps_min <= reps_max` isn't enforced) — kept simple, matching how this codebase doesn't cross-validate `plans`' per-item macros either.
