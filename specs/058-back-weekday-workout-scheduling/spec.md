# Feature Specification: Weekday-Based Workout Scheduling (Backend)

**Feature Branch**: `058-back-weekday-workout-scheduling`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

A workout plan's "days" are just an ordered, labeled list (`WorkoutDayIn{label, exercises}`) with no calendar association — a "day" really means "session N in the plan's sequence." This lets a coach optionally tag each day with the actual weekday(s) it should run on (e.g. "Día 1" on Monday and Thursday), enabling the frontends to surface "today's workout."

Research note: nutrition plans do **not** have an existing weekday-rotation pattern to mirror — `MyDayController` hardcodes "today" as day-index 0, and the plan-detail calendar strip is date-labels-only. This is a genuinely new concept for the codebase, not an extension of an existing one.

## In Scope

- `WorkoutDayIn.weekdays: List[int]` — ISO weekday integers (1=Mon…7=Sun, matching Dart's own `DateTime.weekday`), defaulting to an empty list (unscheduled).
- Validation: no weekday integer may be assigned to more than one day within the same plan (a `422` from the field-level range check, or a `400` from the service-level uniqueness check).

## Out of Scope

- No "today's workout" computation on the backend — that's purely a frontend read of `weekdays` against the current date, same division of responsibility as everything else in this opaque-passthrough `days` field.
- No assignment-level weekday override — weekday scheduling is baked into the plan's `days` themselves, applying identically to every patient the plan is assigned to.
- No repository code changes — `mongo_workout_plans_repository.py` stores `days` as an opaque passthrough dict, so this is a pure schema-and-validation change (same precedent as `050-back-per-set-workout-authoring` and `056-back-multi-media-exercises`).

## Baseline Behavior

`WorkoutDayIn` had no weekday concept at all — a day was purely positional.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `063-front-weekday-workout-scheduling` (authoring UI) and `nutri_app` spec `060-front-weekday-workout-scheduling` (detail-page display + Home tab card) both consume this.

## Acceptance Criteria

1. Given a plan with two days assigned distinct weekdays, when created, then it succeeds and the weekdays round-trip on `GET`.
2. Given a plan with two days both assigned the same weekday, when created, then it's rejected with `400` ("weekday N is assigned to more than one day").
3. Given a day is assigned a weekday integer outside `1..7`, then it's rejected with `422` at the schema level.

## Validation

- Full backend unittest suite green (219/219 — 2 new tests added, no regressions).
- Live-curl verification against the running local server: created a plan with 2 days on distinct weekdays (succeeded, round-tripped), attempted the same with a shared weekday (400), attempted an out-of-range weekday (422). Test data cleaned up afterward via a direct Motor script.
