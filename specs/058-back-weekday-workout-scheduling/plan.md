# Implementation Plan: Weekday-Based Workout Scheduling (Backend)

**Branch**: `058-back-weekday-workout-scheduling` | **Date**: 2026-08-26 | **Spec**: `specs/058-back-weekday-workout-scheduling/spec.md`

## Summary

Pure schema-plus-validation change — `days` opaque passthrough storage means zero repository code is touched.

## Steps

1. `app/schemas/workout_plan.py`: `WorkoutDayIn.weekdays: List[int] = Field(default_factory=list)`, `@field_validator("weekdays")` rejecting values outside `1..7`.
2. `app/modules/workout_plans/application/workout_plans_service.py`, `_validate_payload`: collect every `weekdays` entry across a plan's `days` into a `set`; raise `ValueError` on the first repeat (surfaced as `400` by the router, matching the existing exercise-name-required error path).
3. `tests/test_workout_plans_service.py`: `test_create_plan_accepts_days_with_distinct_weekdays`, `test_create_plan_rejects_a_weekday_assigned_to_two_days`.

## Constraints

- No "today" computation here — purely a data field and a uniqueness constraint; frontends own the date logic.
