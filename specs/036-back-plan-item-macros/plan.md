# Implementation Plan: Plan Meal Item Macros

**Branch**: `036-back-plan-item-macros` | **Date**: 2026-08-24 | **Spec**: `specs/036-back-plan-item-macros/spec.md`

## Summary

Same shape as `035-back-plan-meal-dish-name`: a purely additive, optional field set on an already-schema-validated nested model. No repository/service code changes — meal items are stored and returned as opaque dicts, so the new keys ride along automatically once the schema accepts them.

## Steps

1. `app/schemas/plan.py`: add `kcal: Optional[float] = None`, `protein: Optional[float] = None`, `carbs: Optional[float] = None`, `fat: Optional[float] = None` to `PlanMealItem`.
2. No changes to `mongo_plans_repository.py`, `plans_service.py`, or `presentation/router.py` — all operate on the dict payload/response without referencing individual `PlanMealItem` fields by name.

## Constraints

- Field names (`kcal`, `protein`, `carbs`, `fat`) match exactly what `nutri_app`'s `plan_detail_plan_model.dart` already parses from the raw item JSON — no aliasing needed, and no `nutri_app` change required.
- Fully optional — every existing item with no macro data must keep working unchanged.
