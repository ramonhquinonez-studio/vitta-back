# Implementation Plan: Plan Meal Item Cooking State

**Branch**: `037-back-plan-item-cooking-state` | **Date**: 2026-08-24 | **Spec**: `specs/037-back-plan-item-cooking-state/spec.md`

## Summary

Same shape as `036-back-plan-item-macros`, shipped in the same session: two more purely additive, optional fields on `PlanMealItem`.

## Steps

1. `app/schemas/plan.py`: add `cooking_state: Optional[Literal['raw', 'cooked']] = None` and `equivalent_qty: Optional[float] = None` to `PlanMealItem`.
2. No changes to repository/service/router code — meal items are stored and returned as opaque dicts.

## Constraints

- `equivalent_qty` has no unit of its own — it's implicitly the same `unit` as the item's `qty`, since raw/cooked comparisons only make sense for the same unit of measure (typically grams).
