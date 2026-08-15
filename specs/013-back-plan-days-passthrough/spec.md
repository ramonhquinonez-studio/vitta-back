# Bugfix Specification: Plan Days Passthrough + Real Weekly Plan Data

**Feature Branch**: `013-back-plan-days-passthrough`
**Created**: 2026-08-15
**Status**: Draft
**Type**: Bugfix + Data

## Objective

`GET /me/plan/active` (`mongo_me_repository.get_active_plan`) silently dropped the `days` field from the plan document. The frontend (`PlanActive.days` → `PlanDetailPlan.days` → `mealsForDay()`) has supported real per-day meals since `011-front-plan-detail-typed-meals`, but no plan document had ever populated `days`, so the bug was invisible until this session's plan actually needed it: only `Desayuno`/`Comida` were visible for the demo/assigned plan because (a) the seeded plan only had 2 meal blocks and (b) even if `days` had been set, the endpoint wasn't returning it.

## In Scope

- `mongo_me_repository.py#get_active_plan`: include `"days": plan.get("days", [])` in the returned dict.
- `app/scripts/seed_ramon_real_plan.py` (new, one-off): replaces the synthetic plan assigned to `rhq.castro@gmail.com` with the patient's real 7-day plan (transcribed from the nutritionist-issued PDF) — all 5 meal slots per day (Desayuno, Snack, Comida, Snack, Cena), and 25 new cookbook recipes (18 real dishes + 7 deduplicated snack combos) so every meal with a dish links to a real cookbook entry.
- Día 7's "Comida libre con moderación" and "Elige una opción de la semana" are stored as meals with empty `items` and a `notes` string (patient's free choice, no specific dish to link).

## Out of Scope

- Any change to `PlanOut`/`PlanCreate`/`PlanUpdate` schemas — `days` already flows through `update_for_owner`'s free-form `$set` payload; no Pydantic model change was needed for the script to write it.
- Backfilling `days` for the generic seed plan (`seed_dev.py`) — this fixes the specific patient's real assigned plan; the generic 2-meal demo plan used elsewhere is untouched.

## Baseline Behavior

- `GET /me/plan/active` for the affected patient only ever returned `Desayuno`/`Comida`, identical on every day (synthetic item rotation, no real `days`).

## Target Design

- `GET /me/plan/active` returns the same `days` structure the plan document stores, mirroring `meals`/`attachment_url` which already pass through unmodified.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a plan document with a populated `days` array, when `GET /me/plan/active` is called, then the response includes that `days` array unchanged.
2. Given the patient `rhq.castro@gmail.com` (patient_id `6a7d79ea71f440e8e09421d6`), when the active plan is fetched, then all 7 days each show exactly 5 meals (Desayuno, Snack, Comida, Snack, Cena).
3. Given any meal with `items`, when inspected, then every item carries a `recipe_id` resolvable via `GET /me/recipes/{id}`.
4. Given día 7's Comida/Cena, when inspected, then `items` is empty and `notes` carries the free-choice text.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 29/29 green (no behavior covered by existing fakes changed).
- Manual: ran `python -m app.scripts.seed_ramon_real_plan`, then verified via `MongoMeRepository.get_active_plan` directly — 7 days × 5 meals, all non-free-choice meals' items resolve `recipe_id` to a real recipe via `get_recipe_for_owner`.
