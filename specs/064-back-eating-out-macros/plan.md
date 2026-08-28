# Implementation Plan: Carbs/Fat on Eating-Out Options and Diary Entries

**Feature Branch**: `064-back-eating-out-macros`

## Summary

Two small, independent field additions mirroring `PlanMealItem`'s existing `carbs`/`fat` shape.

## Steps

1. **`app/schemas/plan.py`**: `EatingOutOption` gains `carbs: Optional[float] = None`, `fat: Optional[float] = None`. No other schema change needed — `PlanOut.meals: List[PlanMeal]` reuses the same class for both write and read, and `me/infrastructure/mongo_me_repository.py`'s `get_active_plan` returns `plan.get("meals", [])` as a raw dict pass-through.
2. **`app/modules/me/infrastructure/mongo_me_repository.py`**: `create_food_diary_entry`'s stored document and `_serialize_food_diary_entry`'s returned dict both gain `carbs`/`fat`.
3. **`app/modules/patients/infrastructure/mongo_patients_repository.py`**: `list_food_diary_entries`'s inline dict (the coach-facing read, a separate serializer from `me`'s) gains the same two fields.
4. **Live verification**: throwaway plan + diary entry round-trip against the running server, then cleanup.

## Constraints

- No test fixture changes needed — both are optional fields defaulting to `None`.
