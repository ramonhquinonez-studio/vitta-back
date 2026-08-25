# Feature Specification: Plan Meal Item Macros

**Feature Branch**: `036-back-plan-item-macros`
**Created**: 2026-08-24
**Status**: Draft
**Type**: Feature

## Objective

`nutri_app`'s food detail page (`FoodDetailPage`) has always rendered per-item protein/carbs/fat/kcal bars, but `PlanMealItem` never had those fields — they only ever existed for one hand-written demo record seeded directly into Mongo, bypassing the API. Every plan created or edited through the real product showed 0g for every macro, on every item, always — not a display bug, a genuine data-model gap. This makes them real, optional, settable fields.

## In Scope

- `PlanMealItem` gains `kcal`, `protein`, `carbs`, `fat` (all `Optional[float] = None`) in `app/schemas/plan.py` — accepted on create/update, returned on read, exactly like every other optional item field (`recipe_id`, `equivalents`).
- Backward compatible: existing items with no macro keys validate cleanly (`None`).

## Out of Scope

- No automatic computation from a food/nutrition database — there isn't one in this system. Values are only ever as accurate as whatever a nutritionist enters by hand (`nutri_pro`, separate spec).
- No macro fields on `Recipe`/`RecipeIngredient` (Recetario) — a recipe only ever carried whole-dish `kcal`, never a protein/carbs/fat breakdown, and this phase doesn't change that; per-item macros in a plan are independent, hand-entered data.

## Baseline Behavior

`PlanMealItem` had `name`, `qty`, `unit`, `recipe_id`, `equivalency_group_id`, `equivalency_food_id`, `equivalents` — no macro fields at all. A `kcal`/`protein`/`carbs`/`fat` key present on a Mongo document (true only for one seeded demo plan) was invisible to `PlanCreate`/`PlanUpdate`/`PlanOut`, and never once settable through the real API.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: enables `nutri_pro`'s meal-item macro fields (separate spec) — `nutri_app` needs no changes, since it already parses `kcal`/`protein`/`carbs`/`fat` from the raw item JSON (`plan_detail_plan_model.dart`); it was only ever missing data to parse, not a missing parser.

## Acceptance Criteria

1. Given a `POST /plans` payload with an item containing `kcal`/`protein`/`carbs`/`fat`, when created, then `GET /plans/{id}` returns those same values for the item.
2. Given an item that omits those fields, then they come back `null` — no other field affected.
3. Given a pre-existing Mongo plan document with items that have none of these keys, then it still validates and returns `null` for all four — no 500, no dropped items.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 124/124 green, no regressions.
- Live verification against the running backend: `POST /plans` with an item carrying all four macro fields, `GET` back unchanged; test plan deleted afterward.
- Verified the already-live, real-account-assigned plan ("Plan de ganancia muscular") round-trips its (separately backfilled) macro data through `PlanOut.model_validate()`.
