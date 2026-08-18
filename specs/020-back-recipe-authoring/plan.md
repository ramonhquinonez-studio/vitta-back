# Implementation Plan: Recipe Authoring

**Branch**: `020-back-recipe-authoring` | **Date**: 2026-08-17 | **Spec**: `specs/020-back-recipe-authoring/spec.md`

## Summary

Extends the `recipes` module (`018`) with write methods, deliberately deferred at the time since only the read was needed then.

## Steps

1. `recipes/domain/repositories.py`: add `create_collection`/`update_collection`/`delete_collection`/`add_recipe`/`update_recipe`/`delete_recipe` to the Protocol.
2. `recipes/infrastructure/mongo_recipes_repository.py`: collection CRUD via standard `insert_one`/`update_one`/`delete_one`; recipe CRUD via `$push` (add), `update_one(..., array_filters=[{"r.id": recipe_id}])` with `recipes.$[r].<field>` dot-paths (update), `$pull` (delete) — recipes stay embedded, no new Mongo collection.
3. `recipes/application/recipes_service.py`: orchestration + validation (`title` required on create; `LookupError` when the repository returns `None`/`False` for an unowned id).
4. `app/schemas/recipes.py`: `RecipeCollectionCreate`/`Update`, `RecipeIn`/`Update`.
5. `recipes/presentation/router.py`: 6 new routes.
6. `tests/test_recipes_service.py`: fake repository extended with the same CRUD semantics; 7 new tests.

## Constraints

- New recipe ids are `uuid4().hex` (32 hex chars, no dashes) — matches the existing seeded recipes' id shape exactly, so no client-side parsing assumption breaks.
- `delete_recipe` on an id that doesn't exist in the collection is a no-op `$pull` (still returns the collection, not a 404) — matches typical idempotent-delete semantics; only an unowned/missing *collection* is a 404.
