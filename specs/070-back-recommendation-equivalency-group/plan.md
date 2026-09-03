# Implementation Plan: Brand Recommendations Linked to Menu Equivalency Groups

**Branch**: `070-back-recommendation-equivalency-group` | **Date**: 2026-08-29 | **Spec**: `specs/070-back-recommendation-equivalency-group/spec.md`

## Summary

A single additive nullable field threaded through the existing `recommendations` entity/schema/repository/router and the `me` module's separate serializer — no new collection, no new endpoint.

## Steps

1. `domain/entities.py`: `Recommendation.equivalency_group_id: str | None = None`.
2. `app/schemas/recommendations.py`: add to `RecommendationOut`, `RecommendationCreate`, `RecommendationUpdate`.
3. `infrastructure/mongo_recommendations_repository.py`: `create_for_owner` persists `payload.get("equivalency_group_id")`; `_to_entity` reads `document.get("equivalency_group_id")`. `update_for_owner` needed no change — it already does a generic `{"$set": payload}`.
4. `presentation/router.py`: `_serialize()` includes `rec.equivalency_group_id`.
5. `app/modules/me/infrastructure/mongo_me_repository.py`: `list_recommendations`'s inline dict serializer (the separate patient-facing path, per this codebase's established duplicate-serialization pattern for `workout_logs`/`content_articles`/etc.) adds `equivalency_group_id`.
6. Tests: extend `test_recommendations_service.py`'s fake repository's `create_for_owner` to thread the field, add one test asserting it persists.
7. Live verification: full plan-item + brand-recommendation join round-trip against the running local server.

## Constraints

- No FK validation against `equivalency_groups` — deliberately mirrors `PlanMealItem.equivalency_group_id`'s existing looseness rather than introducing a stricter contract only on the brand side.
