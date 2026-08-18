# Implementation Plan: Food Equivalency (SMAE) Catalog

**Branch**: `026-back-equivalencies-catalog` | **Date**: 2026-08-19 | **Spec**: `specs/026-back-equivalencies-catalog/spec.md`

## Summary

A new module mirroring the `recommendations` module's shape exactly (domain/application/infrastructure/presentation, `Protocol`-based repository), plus a pure additive extension to the existing `plan` schema.

## Steps

1. `equivalencies/domain/entities.py`: `EquivalencyGroup` (string `id` — a stable slug like `cereales_sin_grasa`, not an `ObjectId`, since groups are a small fixed taxonomy referenced by key) and `EquivalencyFood` (`ObjectId`-backed `id`, `group_id` string reference, `owner_id: str | None` — `None` means global/seeded).
2. `equivalencies/domain/repositories.py`: `EquivalenciesRepository` protocol.
3. `equivalencies/infrastructure/mongo_equivalencies_repository.py`: `list_foods` queries `{"$or": [{"owner_id": None}, {"owner_id": owner_oid}]}` to merge global + owned foods in one query.
4. `equivalencies/application/equivalencies_service.py`: validates `name`/`group_id` required on create; `delete_food` scoped to `owner_id` (can't delete another nutritionist's custom food, and can't delete global foods since they have no matching `owner_id`).
5. `app/schemas/equivalencies.py` + `equivalencies/presentation/router.py`: `GET /groups`, `GET/POST /foods`, `DELETE /foods/{id}`.
6. `app/routers/equivalencies.py` thin wrapper; registered in `main.py`; added to both router guardrail tests (`test_router_wrapper_guardrails.py`, `test_module_router_smoke.py`).
7. `app/schemas/plan.py`: `PlanMealItem` gains `equivalency_group_id`/`equivalency_food_id`/`equivalents`, all optional — no service/repository changes needed since plans already pass the full payload through untouched (`013-back-plan-days-passthrough`).
8. `app/scripts/seed_equivalencies.py`: 16 `GROUPS` + a `FOODS` dict keyed by group with ~3–6 foods each (57 total) — idempotent via `update_one(..., upsert=True)` for groups and a existence-check-before-insert for foods.
9. Tests: `test_equivalencies_service.py` (6 tests), 1 new test in `test_plans_service.py`.

## Constraints

- Group macro values are the standard published SMAE reference figures (Kaufer-Horwitz et al.) — not something to recompute or vary per-nutritionist.
- Seeded the catalog with a real but intentionally partial food list (57 foods, ~3–6 per group) rather than the full traditional SMAE tables (which run into the hundreds) — enough for real plans to be authored immediately; nutritionists can extend it with their own foods, and the catalog itself can grow later without any schema change.
