# Feature Specification: Recipe-Level Eating-Out Alternative

**Feature Branch**: `073-back-recipe-eating-out-option`
**Created**: 2026-08-30
**Status**: Draft
**Type**: Feature

## Objective

Direct user request: "In each meal of recetario must be possible to assign comer fuera meal." Confirmed via `AskUserQuestion`: one optional eating-out alternative per recipe (each `Recipe` already has a `meal_type` — Desayuno, Comida, Cena, etc., representing which meal slot it's for), and when that recipe is later used in a patient's plan, the linked eating-out option should carry through automatically to that meal.

## In Scope

- `Recipe.eating_out_option: Optional[RecipeEatingOutOption]` — a plain snapshot (`restaurant`, `dish`, `kcal`, `protein`, `carbs`, `fat`), mirroring `app.schemas.plan.EatingOutOption`'s exact shape so it can be copied verbatim into a `PlanMeal.eating_out_options` entry when the recipe is used in a plan (`nutri_pro`'s carry-through logic, client-side).
- Threaded through `RecipeOut`/`RecipeIn`/`RecipeUpdate`, `MongoRecipesRepository` (`add_recipe`/`update_recipe`/`_recipe_from_dict`), and the router's `_serialize_recipe`.

## Out of Scope

- No relational reference to the `eating_out_options` library collection (`071-back-eating-out-options-library`) — a snapshot, same as how a plan's own meal-embedded eating-out options are already disconnected copies, not references.
- No `me` module changes — `mongo_me_repository.py`'s `_serialize_recipes` already does a generic `dict(recipe)` shallow copy per recipe, so the new field passes through to patients automatically with no code change.

## Baseline Behavior

`Recipe` had no relationship to eating-out options at all.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro`'s `082-front-recipe-eating-out-option` (assignment UI on the recipe form, plus the client-side auto-carry-through into a plan's meal when the recipe is linked/used).

## Acceptance Criteria

1. Given a nutritionist adds a recipe with `eating_out_option` set, then it round-trips through `GET /recipe_collections` unchanged.
2. Given a nutritionist updates a recipe's `eating_out_option` (full replacement, same as every other optional field on this schema), then the new value persists.
3. Given a patient reads their recipe collections (`GET /me/recipe_collections`), then the recipe's `eating_out_option` is included — no separate serialization fix needed, verified by inspecting `_serialize_recipes`' generic pass-through.

## Validation

- Full backend unittest suite green (247/247 — no new tests needed; `RecipesService`'s payload handling is already fully generic, exercised at the repository/router level instead).
- Live end-to-end verification against the running local server with a throwaway QA nutritionist account: added a recipe with `eating_out_option: {restaurant, dish, kcal, protein, carbs, fat}`, confirmed it round-trips through `GET`; updated it with a partial payload (restaurant/dish/kcal only), confirmed the full replacement persisted (protein/carbs/fat correctly nulled, matching this schema's existing full-replacement semantics for every other optional field). QA account cleaned up afterward.
