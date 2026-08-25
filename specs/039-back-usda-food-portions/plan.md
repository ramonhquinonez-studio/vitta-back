# Implementation Plan: USDA Food Portion Weights

**Branch**: `039-back-usda-food-portions` | **Date**: 2026-08-24 | **Spec**: `specs/039-back-usda-food-portions/spec.md`

## Summary

Extend the `nutrition_lookup` module with a second USDA call (food detail → portions) and add the field that stores a picked portion's gram weight on a plan item.

## Steps

1. `app/schemas/plan.py`: `PlanMealItem.unit_gram_weight: Optional[float] = None`.
2. `nutrition_lookup/domain/entities.py`: `FoodPortion` dataclass.
3. `nutrition_lookup/domain/repositories.py`: `get_portions(fdc_id) -> list[FoodPortion]` on the Protocol.
4. `nutrition_lookup/infrastructure/usda_fdc_repository.py`: factor the retry logic into a shared `_get_with_retry` helper (used by both `search` and the new `get_portions`); `get_portions` calls `/food/{fdcId}`, builds each portion's description from `amount` + `modifier` (skipping USDA's literal `"undetermined"` placeholder), skips entries with no `gramWeight`.
5. `application/nutrition_lookup_service.py`: `get_portions(fdc_id)` passthrough.
6. `app/schemas/nutrition_lookup.py`: `FoodPortionOut`.
7. `presentation/router.py`: `GET /nutrition/food/{fdc_id}/portions`.
8. `tests/test_nutrition_lookup_service.py`: extend the fake repository and add a `get_portions` delegation test.

## Constraints

- No unit-matching logic server-side — the endpoint returns the raw portion list; matching a nutritionist's chosen unit to one of them is a client-side, human-confirmed step (`nutri_pro`).
