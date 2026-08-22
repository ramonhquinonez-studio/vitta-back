# Implementation Plan: Plan Meal `dish_name` Field

**Branch**: `035-back-plan-meal-dish-name` | **Date**: 2026-08-22 | **Spec**: `specs/035-back-plan-meal-dish-name/spec.md`

## Summary

One-field schema addition. `PlanMeal` is a pydantic model nested inside `PlanCreate`/`PlanUpdate`/`PlanOut`; adding an optional field to it is sufficient for it to flow through create, update, and read, since `mongo_plans_repository.py` persists meals as whatever dict the router passes in (`payload.model_dump()`) and returns them the same way (`PlanOut.model_validate(doc)` downstream in the router/service layer). No repository or service code changes needed.

## Steps

1. `app/schemas/plan.py`: add `dish_name: Optional[str] = None` to `PlanMeal`, placed right after `title` (mirrors the conceptual pairing: slot + dish).
2. No changes to `app/modules/plans/infrastructure/mongo_plans_repository.py` — verified `create_for_owner`/`update_for_owner`/`_serialize` all pass `meals` through as opaque dicts; the new key rides along automatically in both directions.
3. No changes to `app/modules/plans/application/plans_service.py` or `presentation/router.py` — they operate on the dict payload/response, never referencing individual `PlanMeal` fields by name.

## Constraints

- Field name is `dish_name` (snake_case), matching the existing convention for every other multi-word field in this schema (`recipe_id`, `equivalency_group_id`, `eating_out_options`) — no camelCase alias needed, since `nutri_pro`'s `plan_model.dart` already sends/expects snake_case keys for meal fields (confirmed: `'eating_out_options'`, `'title'`).
- Must stay fully optional/nullable — the overwhelming majority of existing plans have no dish name and must keep working unchanged until Phase 2 gives nutritionists a UI to set one.
