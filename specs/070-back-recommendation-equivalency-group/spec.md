# Feature Specification: Brand Recommendations Linked to Menu Equivalency Groups

**Feature Branch**: `070-back-recommendation-equivalency-group`
**Created**: 2026-08-29
**Status**: Draft
**Type**: Feature

## Objective

User feedback on `069-back-recommendations-platform-and-assignment`: "the brand's goal is to give the patient the best brands for all the products of the menu." A brand recommendation today is a standalone card with no relationship to a patient's actual meal plan. This ties a brand recommendation to one of the 16 fixed SMAE equivalency-group ids (`equivalencies` module, `seed_equivalencies.py`) — the same taxonomy `PlanMealItem.equivalency_group_id` already uses when a nutritionist links a menu item to an equivalency. Once both share the same group id, a patient's plan can show "the best brand for this item" for any menu item whose group has an assigned brand.

## In Scope

- `Recommendation.equivalency_group_id: Optional[str]` — only meaningful for `kind="brand"`, nullable, no foreign-key validation against `equivalency_groups` (mirrors the existing looseness of `PlanMealItem.equivalency_group_id`, which is also just a free string matched against the fixed seeded ids by convention).
- Threaded through `RecommendationOut`/`RecommendationCreate`/`RecommendationUpdate`, `MongoRecommendationsRepository` (create/read), and `MongoMeRepository.list_recommendations`'s separate patient-facing serializer.
- No new endpoint — a patient's plan (`GET /me/plan/active`, already returning `equivalency_group_id` per meal item since `036-back-plan-item-macros`-era schema) and a patient's assigned brand recommendations (`GET /me/recommendations?kind=brand`, `069`) both now carry the group id; the join happens client-side.

## Out of Scope

- No automatic suggestion/validation that a chosen group id actually exists in `equivalency_groups` — same convention `PlanMealItem` already follows.
- No change to the sync script (`sync_recommendations_library.py`) — DSLD-sourced supplement brands aren't grocery products and don't map cleanly onto SMAE food-exchange groups; group linking is for nutritionist-authored/copied brand entries a nutritionist explicitly ties to a real menu category.

## Baseline Behavior

`Recommendation` had no relationship to `equivalencies` at all; `PlanMealItem.equivalency_group_id` already existed but had no consumer on the recommendations side.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` (`079-front-recommendation-equivalency-group` — group picker on the brand form) and `nutri_app` (`066-front-menu-item-recommended-brand` — patient-facing "marca recomendada" surfaced on the menu item that matches).

## Acceptance Criteria

1. Given a nutritionist creates or updates a brand recommendation with `equivalency_group_id` set, then it round-trips through `GET /recommendations` and `GET /recommendations/platform` unchanged.
2. Given that brand recommendation is assigned to a patient, then `GET /me/recommendations?kind=brand` includes `equivalency_group_id` for the patient to match against their own plan's meal items.
3. Given a supplement recommendation (not a brand), then `equivalency_group_id` is accepted but has no special meaning — no validation rejects it either way, consistent with every other optional field on this schema.

## Validation

- Full backend unittest suite green (237/237 — 1 new test: `test_create_brand_recommendation_persists_the_equivalency_group`).
- Live end-to-end verification against the running local server with throwaway QA accounts: created a plan with a meal item carrying `equivalency_group_id: "aceites_sin_proteina"`, assigned it to a QA patient, confirmed `GET /me/plan/active` returns that field on the item; separately created and assigned a brand recommendation tagged with the same group id, confirmed `GET /me/recommendations?kind=brand` returns it with the matching `equivalency_group_id` — the exact join `nutri_app`'s `PlanDetailController.brandForGroup` performs. QA accounts and data cleaned up afterward; the 24 real synced platform recommendations were kept.
