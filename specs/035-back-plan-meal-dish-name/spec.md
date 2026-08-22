# Feature Specification: Plan Meal `dish_name` Field

**Feature Branch**: `035-back-plan-meal-dish-name`
**Created**: 2026-08-22
**Status**: Draft
**Type**: Feature — Phase 1 of 4 (backend contract)

## Objective

Patients reported that "Mi Plan" and "Mi día" show the same text twice per meal (e.g. "Desayuno" as both the card title and the pill beneath it). Root cause: `PlanMeal.title` is meant to be the meal *slot* ("Desayuno"/"Comida"), but there was never a real place for a nutritionist to record the actual dish ("Chilaquiles verdes") — `dish_name` existed only inside one hand-written seed script (`app/scripts/seed_ramon_real_plan.py`) writing directly to Mongo, bypassing the schema entirely. Every plan created through the real API/UI has no dish name to show, so the frontend's dish-name-or-fallback-to-slot logic always falls back to the slot, which is already shown separately as a pill — hence the duplicate.

This is Phase 1 of a 4-phase fix (full proposal covers `nutri_back` → `nutri_pro` → `nutri_app`): making `dish_name` a first-class, optional field on the real `PlanMeal` contract so it round-trips through create/update/read like any other field, instead of only existing for one demo record.

## In Scope

- `PlanMeal.dish_name: Optional[str] = None` in `app/schemas/plan.py` — accepted on `PlanCreate`/`PlanUpdate`, returned on `PlanOut`.
- Backward compatibility: existing Mongo plan documents with no `dish_name` key at all still validate cleanly (defaults to `None`).
- No change to storage/persistence code (`mongo_plans_repository.py`) — meals are already stored as raw dicts mirroring whatever the pydantic model dumps, so adding the field to the schema is sufficient; Mongo requires no migration.

## Out of Scope

- Any UI change in `nutri_pro` (meal-type dropdown + dish-name field in the plan editor) — Phase 2, separate spec.
- Any change to `nutri_app`'s rendering (`PlanDetailMeal`/`DayMeal`, the duplicate-label fix itself) — Phases 3–4, separate specs.
- Deleting or migrating `seed_ramon_real_plan.py`'s hand-written `dish_name` — it already writes a value compatible with this field's shape; left as-is.

## Baseline Behavior

`PlanMeal` had `title`, `time`, `items`, `eating_out_options` only. A `dish_name` key present on a Mongo document (only true for one seeded demo plan) was invisible to `PlanCreate`/`PlanUpdate`/`PlanOut` — silently dropped by any code path that went through the pydantic schema, and never accepted as API input at all.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: enables `nutri_pro` (meal editor UI) and `nutri_app` (duplicate-label fix) follow-up phases; both are separate specs once implemented.

## Acceptance Criteria

1. Given a `POST /plans` payload with a meal containing `"dish_name": "Chilaquiles verdes"`, when created, then `GET /plans/{id}` returns that same `dish_name` for the meal.
2. Given a `POST /plans` payload with a meal that omits `dish_name`, when created, then the returned meal has `dish_name: null` and no other field is affected.
3. Given a pre-existing Mongo plan document with no `dish_name` key on any meal, when read via `GET /plans/{id}` or `GET /plans`, then it still validates and returns `dish_name: null` for those meals (no 500, no dropped meals).
4. Given the one seeded demo plan (`seed_ramon_real_plan.py`) whose meals already carry a raw `dish_name` in Mongo, when read via the API, then `dish_name` now comes through the real schema instead of only the `/me/plan/active` raw-dict bypass.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 124/124 green, no regressions.
- Manual pydantic round-trip check (`PlanCreate` → `model_dump()` → simulated Mongo doc → `PlanOut.model_validate()`) for: a new meal with `dish_name` set, a legacy doc with no `dish_name` key, and a doc matching the seed script's shape — all three behave as specified above.
