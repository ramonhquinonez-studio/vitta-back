# Feature Specification: Carbs/Fat on Eating-Out Options and Diary Entries

**Feature Branch**: `064-back-eating-out-macros`
**Created**: 2026-08-27
**Status**: Draft
**Type**: Feature

## Objective

Closes a gap flagged in the roadmap: `EatingOutOption` (nutritionist-authored "comer fuera" suggestions on a plan meal) and `food_diary_entries` (the patient's actual log of what they ate out) only ever carried `kcal`/`protein` — `PlanMealItem` got `carbs`/`fat` back in `036-back-plan-item-macros`, but eating-out never did. Investigating for this fix also surfaced a bigger client-side bug (see `nutri_app`'s `063-front-eating-out-macro-totals`): eating-out diary entries weren't counted in the patient's daily macro totals *at all*, regardless of which fields existed.

## In Scope

- `carbs`/`fat` on `EatingOutOption` (`app/schemas/plan.py`) — `PlanMeal.eating_out_options` round-trips through the same `PlanOut`/`PlanCreate`/`PlanUpdate` models used for `PlanMealItem`, and the `me` module's active-plan read returns the stored `meals` dict as-is, so this single field addition covers create/update/read on both the `plans` and `me` sides with no other backend change.
- `carbs`/`fat` on `food_diary_entries` — `create_food_diary_entry`/`_serialize_food_diary_entry` in `me/infrastructure/mongo_me_repository.py`, and the coach-facing duplicate serializer in `patients/infrastructure/mongo_patients_repository.py`'s `list_food_diary_entries`.

## Out of Scope

- No typed Pydantic schema for `POST /me/food_diary_entries`'s body — it already accepts a raw `dict[str, Any]` (pre-existing, not introduced here); adding request validation there is a separate, larger change unrelated to this fix.
- No backfill of existing `food_diary_entries`/`eating_out_options` documents — both are always-optional fields, missing data simply reads as `null`.

## Baseline Behavior

`EatingOutOption` and `food_diary_entries` documents only ever had `kcal`/`protein`.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro`'s `071-front-eating-out-option-macros` (authoring) and `nutri_app`'s `063-front-eating-out-macro-totals` (patient display + the totals bug fix) both consume this.

## Acceptance Criteria

1. Given a nutritionist authors an eating-out option with `carbs`/`fat` set, then it round-trips through `GET /plans/{id}` and the patient's `GET /me/workout-plan/active`-equivalent (`get_active_plan`).
2. Given a patient logs a diary entry with `carbs`/`fat`, then `GET /me/food_diary_entries` and the coach's `GET /patients/{id}/food_diary_entries` both return them.
3. Given neither field is set, both serialize as `null`, not absent keys.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 green (additive optional fields, no existing fixture broken).
- Live verification against the running local server: created a throwaway plan with an eating-out option carrying `carbs`/`fat`, confirmed the round-trip via `GET`, posted a food diary entry with `carbs`/`fat`, confirmed it via `GET /me/food_diary_entries`, then deleted the throwaway plan and diary entry.
