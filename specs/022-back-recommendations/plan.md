# Implementation Plan: Recommendations (Supplements/Brands)

**Branch**: `022-back-recommendations` | **Date**: 2026-08-17 | **Spec**: `specs/022-back-recommendations/spec.md`

## Summary

New migrated-style module (mirrors `recipes`' shape exactly), plus one new read endpoint on the existing `me` module.

## Steps

1. `recommendations/domain/entities.py`: `Recommendation` — single entity covering both `kind`s (superset schema, see spec's Out of Scope).
2. `recommendations/domain/repositories.py`: `RecommendationsRepository` Protocol (`list_for_owner` with optional `kind` filter, `create_for_owner`, `update_for_owner`, `delete_for_owner`).
3. `recommendations/application/recommendations_service.py`: validates `title` required + `kind` in `{"supplement", "brand"}` on create.
4. `recommendations/infrastructure/mongo_recommendations_repository.py`: standard owner-scoped CRUD.
5. `app/schemas/recommendations.py`: `RecommendationOut`/`Create`/`Update`.
6. `recommendations/presentation/router.py` + `app/routers/recommendations.py` (thin wrapper) + `main.py` registration.
7. `me` module: `list_recommendations(owner_id, kind=)` added to `domain/repositories.py`, `mongo_me_repository.py` (queries `recommendations` directly, same cross-collection convention as recipes), `me_service.py`, new `GET /me/recommendations` route.
8. `app/db/init_indexes.py`: compound index on `(owner_id, kind)`.
9. `tests/test_recommendations_service.py` (5 tests) + 2 new tests in `tests/test_me_service.py` + guardrail/smoke tests extended.

## Constraints

- One entity/collection for both `kind`s rather than two separate modules — the two hardcoded pages this replaces (`supplements_page.dart`, `recommended_brands_page.dart`) have overlapping-but-not-identical shapes; a superset schema with a `kind` discriminator avoids duplicating nearly-identical CRUD twice, at the cost of some always-null fields per `kind` (acceptable, matches how e.g. `RecipeOut` already carries fields not every recipe uses).
