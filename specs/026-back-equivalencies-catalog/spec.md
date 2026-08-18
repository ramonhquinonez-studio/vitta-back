# Feature Specification: Food Equivalency (SMAE) Catalog

**Feature Branch**: `026-back-equivalencies-catalog`
**Created**: 2026-08-19
**Status**: Draft
**Type**: Feature

## Objective

Give the backend a real SMAE (Sistema Mexicano de Alimentos Equivalentes) food-exchange catalog, and let `PlanMealItem` reference it, so plan authoring can move from purely freeform text to real, macro-backed food equivalents. This is the foundation for `nutri_pro`'s "modo equivalentes" plan editor and, eventually, real substitute suggestions on `nutri_app`'s (currently hardcoded) `equivalences_page.dart`.

## In Scope

- New `equivalencies` module: `equivalency_groups` (seeded, global, 16 groups covering the standard SMAE taxonomy — cereales, leguminosas, verduras, frutas, 4 AOA tiers, 3 leche tiers, 2 aceites tiers, 2 azúcares tiers — each with `kcal`/`carbs_g`/`protein_g`/`fat_g` per equivalent) and `equivalency_foods` (a food catalog: seeded globally, 57 common Mexican foods across all 16 groups at launch, plus nutritionist-owned custom additions).
- `GET /equivalencies/groups` — the full group catalog.
- `GET /equivalencies/foods?group_id=` — global foods + the requesting nutritionist's own custom foods, merged.
- `POST /equivalencies/foods` — a nutritionist adds a custom food to a group.
- `DELETE /equivalencies/foods/{id}` — a nutritionist removes their own custom food (global foods can't be deleted this way).
- `PlanMealItem` gains three optional fields: `equivalency_group_id`, `equivalency_food_id`, `equivalents` — additive, so every existing plan stays valid untouched.
- `app/scripts/seed_equivalencies.py` — idempotent seed script for the 16 groups + 57 starter foods.

## Out of Scope

- Auto-calculating a suggested equivalent distribution from a patient's calorie/macro targets — a later phase once the manual authoring flow (`nutri_pro`) and consumption flow (`nutri_app`) both exist.
- Patient-facing substitute suggestions — this slice is the data foundation only; the read side on `nutri_app` is tracked separately.
- Editing/deleting global (seeded) foods — only a nutritionist's own custom additions are mutable via the API; the base catalog is maintained via the seed script.

## Baseline Behavior

- No food-exchange concept existed anywhere in the backend. `PlanMealItem` was `{name, qty, unit, recipe_id}` only — completely freeform, no macro data, nothing a patient could see as "equivalent" to something else.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given any authenticated user, when they call `GET /equivalencies/groups`, then all 16 groups are returned with their macro values.
2. Given a nutritionist requests foods for a group, then both global foods and their own previously-added custom foods appear, merged.
3. Given a different nutritionist requests the same group, then they see the global foods but not the first nutritionist's custom additions.
4. Given a nutritionist creates a plan with a meal item carrying `equivalency_group_id`/`equivalency_food_id`/`equivalents`, then those fields round-trip exactly on read.
5. Given a plan created before this change (no equivalency fields), then it still loads and validates correctly — the fields are simply absent/null.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 76/76 green (6 new tests in `test_equivalencies_service.py`, 1 new in `test_plans_service.py`, both router guardrail/smoke tests extended for the new module).
- `python app/scripts/seed_equivalencies.py` → 16 groups + 57 foods seeded (idempotent — re-running updates groups and skips existing foods).
- Manual: `curl GET /equivalencies/groups` → 16 groups; `curl GET /equivalencies/foods?group_id=cereales_sin_grasa` → 6 real foods; created a custom food, confirmed it appeared merged with the global list, deleted it (`204`); created a real plan with equivalency fields on a meal item, confirmed exact round-trip, deleted the test plan.
