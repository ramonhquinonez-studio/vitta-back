# Feature Specification: Recipe Collections — Owner Read

**Feature Branch**: `018-back-recipe-collections-owner-read`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Feature

## Objective

Let the nutritionist read their own `recipe_collections` directly (`GET /recipe_collections`), so `nutri_pro` can offer a recipe picker when linking a recipe to a plan meal item. Before this slice, `recipe_collections` only had a patient-facing read path (`GET /me/recipe_collections`, resolved through the patient's `owner_id`) — there was no way for the owning nutritionist to read their own collections directly.

## In Scope

- New `recipes` module (`domain`/`application`/`infrastructure`/`presentation`), read-only for this slice.
- `GET /recipe_collections` — the current user's own collections, scoped directly by their id (no patient-resolution indirection, unlike the `/me/*` read path).

## Out of Scope

- Any write endpoint (`POST`/`PATCH`/`DELETE`) for collections or recipes — content is still seed-only for now. A future slice (`nutri_pro`'s "biblioteca nutricional" authoring feature) will need this and should extend this same module rather than duplicating it.
- Changing the existing patient-facing `GET /me/recipe_collections` path — untouched.

## Baseline Behavior

- `recipe_collections` documents existed (seeded) and were served to patients via `GET /me/recipe_collections`, but nothing let the owning nutritionist list their own collections directly.

## Target Design

- `GET /recipe_collections` (as the nutritionist) → the same collections their own patients would see via `/me/recipe_collections`, same shape (`id`, `title`, `description`, nested `recipes`).

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a nutritionist with seeded recipe collections, when `GET /recipe_collections` is called, then it returns those collections with their nested recipes.
2. Given a nutritionist with no collections, when called, then it returns an empty list, not an error.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 41/41 green (new: `test_recipes_service.py`).
- Manual: `curl GET /recipe_collections` as the demo nutritionist against the live backend → `200`, real seeded recipes returned (matching what patients already see via `/me/recipe_collections`).
