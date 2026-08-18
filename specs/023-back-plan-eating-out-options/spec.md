# Feature Specification: Plan Meal Eating-Out Options

**Feature Branch**: `023-back-plan-eating-out-options`
**Created**: 2026-08-18
**Status**: Draft
**Type**: Feature

## Objective

Let a nutritionist attach one or more real "eating out" suggestions (restaurant + dish + macros) to each meal of a plan, so `nutri_app`'s "Comer fuera" screen can show curated options instead of an entirely fabricated Subway/Starbucks generator. Before this slice, `EatingOutPage` in `nutri_app` invented four options per meal from hardcoded restaurant/dish templates scaled off the meal's own macros — none of it came from the nutritionist or the backend.

## In Scope

- `PlanMeal` schema gains `eating_out_options: List[EatingOutOption]` (`restaurant: str`, `dish: str`, `kcal: Optional[float]`, `protein: Optional[float]`), defaulting to `[]`.
- No service/router/repository changes needed: `plans_service` already passes the full `payload.model_dump()` through to Mongo untouched (`013-back-plan-days-passthrough`), so the new field round-trips through `POST/PATCH /plans` and appears in `GET /plans`, `GET /plans/{id}`, and `GET /me/plan/active` automatically once present in a stored document.

## Out of Scope

- A separate "eating out options" collection or CRUD endpoints — these are nested data on the meal itself, authored as part of normal plan create/update, matching how `PlanMealItem.recipe_id` already works.
- Any ranking/compatibility score — the old fake generator computed a fabricated "compatibility %"; real nutritionist-curated options don't need one.

## Baseline Behavior

- Plans stored before this change simply don't have the `eating_out_options` key in Mongo — reads of old plans return meals without the field, which every consumer must treat as "no options" (both `nutri_pro`'s and `nutri_app`'s parsers default to an empty list when the key is absent).

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a nutritionist creates a plan with `eating_out_options` on a meal, when they then `GET` that plan, then the options are returned exactly as sent.
2. Given that plan is assigned to a patient, when the patient calls `GET /me/plan/active`, then the same options appear on the same meal.
3. Given a meal with no `eating_out_options` in the request, then the field defaults to `[]` in the response (never omitted, never `null`).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 62/62 green (1 new test in `test_plans_service.py` validating `PlanCreate` parses the nested field).
- Manual: `curl POST /plans` with `eating_out_options` on one meal → `201` with the field echoed back correctly; assigned the plan to a patient via `POST /plans/{id}/assign`; `curl GET /me/plan/active` (that patient) → same options on the same meal, confirming the full nutritionist-author → patient-read loop end-to-end.
