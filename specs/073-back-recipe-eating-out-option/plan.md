# Implementation Plan: Recipe-Level Eating-Out Alternative

**Branch**: `073-back-recipe-eating-out-option` | **Date**: 2026-08-30 | **Spec**: `specs/073-back-recipe-eating-out-option/spec.md`

## Summary

A single additive nullable nested field threaded through the existing `recipes` module — no new collection, no new endpoint, no changes to `me`'s already-generic serializer.

## Steps

1. `app/schemas/recipes.py`: new `RecipeEatingOutOption` (restaurant, dish, kcal, protein, carbs, fat — mirrors `app.schemas.plan.EatingOutOption`), added to `RecipeOut`, `RecipeIn`, `RecipeUpdate`.
2. `app/modules/recipes/domain/entities.py`: `Recipe.eating_out_option: dict | None = None` (kept as a plain dict, matching this entity's existing `ingredients: list[dict]` looseness).
3. `infrastructure/mongo_recipes_repository.py`: `add_recipe` includes `payload.get("eating_out_option")`; `update_recipe`'s existing generic `{f"recipes.$[r].{key}": value for key, value in payload.items()}` already handles it with no special-casing; `_recipe_from_dict` reads `recipe.get("eating_out_option")`.
4. `presentation/router.py`: `_serialize_recipe` includes `recipe.eating_out_option`.
5. Live verification: add/update round-trip via curl with a throwaway QA account.

## Constraints

- No FK/reference validation against the `eating_out_options` library — a deliberate snapshot, same precedent as `PlanMeal.eating_out_options` itself.
