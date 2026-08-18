# Implementation Plan: Nutritionist Profile

**Branch**: `017-back-nutritionist-profile` | **Date**: 2026-08-17 | **Spec**: `specs/017-back-nutritionist-profile/spec.md`

## Summary

New migrated-style module (`domain`/`application`/`infrastructure`/`presentation`), plus one new read endpoint added to the existing `me` module.

## Steps

1. `app/modules/nutritionist_profile/domain/entities.py`: `NutritionistProfile`, `SocialLink`.
2. `app/modules/nutritionist_profile/domain/repositories.py`: `NutritionistProfileRepository` Protocol (`get_for_owner`, `upsert_for_owner`, `count_patients_for_owner`).
3. `app/modules/nutritionist_profile/application/nutritionist_profile_service.py`: `get_my_profile`/`update_my_profile`/`get_profile_for_owner`, all attaching the computed `patient_count`.
4. `app/modules/nutritionist_profile/infrastructure/mongo_nutritionist_profile_repository.py`: upsert via `update_one(..., upsert=True)`.
5. `app/schemas/nutritionist_profile.py`: `NutritionistProfileUpdate`/`NutritionistProfileOut`.
6. `app/modules/nutritionist_profile/presentation/router.py` + `app/routers/nutritionist_profile.py` (thin wrapper) + `main.py` registration.
7. `app/db/init_indexes.py`: unique index on `nutritionist_profiles.owner_id`.
8. `me` module: `get_nutritionist_profile(owner_id)` added to `domain/repositories.py`, `mongo_me_repository.py` (queries `users`/`nutritionist_profiles`/`patients` directly, same cross-collection convention as `list_recipe_collections`), `me_service.py`, and a new `GET /me/nutritionist_profile` route.
9. `tests/test_nutritionist_profile_service.py` (4 tests) + 2 new tests in `tests/test_me_service.py` + `test_router_wrapper_guardrails.py`/`test_module_router_smoke.py` extended.

## Constraints

- No role check beyond what already exists elsewhere in this codebase (no endpoint anywhere enforces `role == "pro"` at the router layer; role gating happens client-side at login).
- `session_price_currency` defaults to `"MXN"` both in the entity and on a first-ever `PATCH` that omits it.
