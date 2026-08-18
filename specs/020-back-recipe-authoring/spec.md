# Feature Specification: Recipe Authoring

**Feature Branch**: `020-back-recipe-authoring`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Feature

## Objective

Let the nutritionist create, edit, and delete their own recipe collections and the recipes inside them. `018-back-recipe-collections-owner-read` only added the owner-facing read; content could only be seeded by hand until now.

## In Scope

- `POST /recipe_collections` — create a collection (title, description).
- `PATCH /recipe_collections/{id}` / `DELETE /recipe_collections/{id}` — update/delete a collection (ownership-checked).
- `POST /recipe_collections/{id}/recipes` — add a recipe to a collection (title + optional meal_type/minutes/portions/kcal/ingredients/steps/url). Recipe ids are `uuid4().hex`, matching the existing seeded data's id shape (32 hex chars, no dashes).
- `PATCH /recipe_collections/{id}/recipes/{recipe_id}` / `DELETE /recipe_collections/{id}/recipes/{recipe_id}` — update/delete a recipe within a collection, via Mongo array-filter/`$pull` operations (recipes are embedded in the collection document, not a separate collection).

## Out of Scope

- Any change to the patient-facing read path (`GET /me/recipe_collections`) — untouched, automatically reflects whatever the nutritionist authors here.
- Recipe images/photos — text/structured fields only, matching the existing seeded shape.

## Baseline Behavior

- `recipe_collections` could only be populated by directly inserting documents via a seed script — no API write path existed.

## Target Design

- `POST /recipe_collections {"title": "Postres saludables", "description": "..."}` → `201`, empty `recipes: []`.
- `POST /recipe_collections/{id}/recipes {"title": "Gelatina de fruta", "meal_type": "Postre", ...}` → `201`, the collection with the new recipe appended, given a generated `id`.
- `PATCH .../recipes/{recipe_id} {"kcal": 95}` → `200`, only `kcal` changed on that recipe, everything else untouched.
- `DELETE .../recipes/{recipe_id}` → `200`, the collection with that recipe removed.
- Any of the above against a collection/recipe not owned by the caller → `404`.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a new collection, when created, then it starts with an empty `recipes` list.
2. Given a collection, when a recipe is added, then it appears in the collection's `recipes` with a generated id and only the provided fields set.
3. Given a recipe within a collection, when updated with a partial payload, then only the provided fields change.
4. Given a recipe, when deleted, then it's removed from the collection's `recipes` list, the collection itself is untouched.
5. Given a collection/recipe not owned by the caller, when any write is attempted, then it's `404`, not silently succeeding or leaking another owner's data.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 49/49 green (7 new tests in `test_recipes_service.py`).
- Manual: full `curl` cycle against the live backend — create collection → add recipe → update recipe → delete recipe → delete collection — each step's response verified, test collection cleanly removed afterward (no orphaned data).
