# Implementation Plan: Recipe Collections — Owner Read

**Branch**: `018-back-recipe-collections-owner-read` | **Date**: 2026-08-17 | **Spec**: `specs/018-back-recipe-collections-owner-read/spec.md`

## Summary

New migrated-style module, read-only. No changes to the existing `me`-module patient-facing path.

## Steps

1. `app/modules/recipes/domain/entities.py`: `Recipe`, `RecipeCollection`.
2. `app/modules/recipes/domain/repositories.py`: `RecipesRepository` Protocol (`list_for_owner` only — write methods deliberately deferred to the future authoring slice, not stubbed speculatively).
3. `app/modules/recipes/application/recipes_service.py`: `list_my_collections`.
4. `app/modules/recipes/infrastructure/mongo_recipes_repository.py`: queries `recipe_collections` by `owner_id` directly (no patient lookup), same field-mapping as `mongo_me_repository.list_recipe_collections`.
5. `app/schemas/recipes.py`: `RecipeOut`/`RecipeCollectionOut`.
6. `app/modules/recipes/presentation/router.py` + `app/routers/recipes.py` (thin wrapper) + `main.py` registration.
7. `tests/test_recipes_service.py` (2 tests) + `test_router_wrapper_guardrails.py`/`test_module_router_smoke.py` extended.

## Constraints

- Router prefix is `/recipe_collections` (top-level, like `/patients`/`/plans`/`/appointments`), not `/recipes/...` — the resource being listed is collections, matching the existing patient-facing `/me/recipe_collections` naming.
- Kept the repository Protocol to exactly what this slice needs (`list_for_owner`) rather than pre-declaring write methods for the not-yet-built authoring feature.
