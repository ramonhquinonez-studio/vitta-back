# Implementation Plan: Plan Meal Eating-Out Options

**Branch**: `023-back-plan-eating-out-options` | **Date**: 2026-08-18 | **Spec**: `specs/023-back-plan-eating-out-options/spec.md`

## Summary

A pure schema addition. Because `plans_service` treats the whole plan payload as an opaque dict (`013-back-plan-days-passthrough`), adding a field to the Pydantic `PlanMeal` model is sufficient — no service, repository, or router changes.

## Steps

1. `app/schemas/plan.py`: add `EatingOutOption` (`restaurant`, `dish`, `kcal?`, `protein?`) and `eating_out_options: List[EatingOutOption] = Field(default_factory=list)` on `PlanMeal`.
2. `tests/test_plans_service.py`: new `PlanSchemaTest` verifying `PlanCreate(**payload).model_dump()` round-trips the nested field correctly, including defaulting to `[]` for a meal that omits it.

## Constraints

- Kept `kcal`/`protein` optional (`float`) rather than required — a nutritionist may want to note just "Subway: cualquier ensalada" without committing to exact macros.
- Deliberately did not add a "compatibility" field (the old client-side fake generator had one) — that was a fabricated number with no real meaning once the data is genuinely curated.
