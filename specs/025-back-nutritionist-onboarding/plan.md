# Implementation Plan: Nutritionist Onboarding — Backend Foundation

**Branch**: `025-back-nutritionist-onboarding` | **Date**: 2026-08-19 | **Spec**: `specs/025-back-nutritionist-onboarding/spec.md`

## Summary

Two independent additions to existing modules: a new registration entry point in `auth`, and an extension of the existing `nutritionist_profile` entity/schema/endpoints — no new module, no breaking changes to either.

## Steps

1. `app/schemas/auth.py`: `RegisterNutritionistIn` (name/email/password, no invite_code).
2. `auth/application/auth_service.py`: `register_nutritionist` — duplicate-email check + `create_user(role="nutritionist")`, skipping every invite-code/patient-creation step `register` does.
3. `auth/presentation/router.py`: `POST /auth/register-nutritionist`, same error mapping as `/auth/register` minus the `LookupError` (invite-code) case.
4. `nutritionist_profile/domain/entities.py`: `MacroSplit` dataclass; `NutritionistProfile` gains the three new field groups + `onboarding_completed_at`, all defaulting to `None`/`[]`.
5. `nutritionist_profile/domain/repositories.py` + `mongo_nutritionist_profile_repository.py`: `mark_onboarding_completed(owner_id)` — thin wrapper over the existing `upsert_for_owner`, setting `onboarding_completed_at` to `datetime.utcnow()` server-side; `_to_entity` extended to hydrate the new fields (including nested `macro_split`).
6. `nutritionist_profile/application/nutritionist_profile_service.py`: `_serialize` extended; new `complete_onboarding` method.
7. `app/schemas/nutritionist_profile.py`: `NutritionistProfileUpdate`/`Out` extended; `energy_equation`/`portions_mode`/`units` constrained via `Literal` so invalid values `400` at the schema layer rather than reaching the database.
8. `nutritionist_profile/presentation/router.py`: `POST /me/complete-onboarding`.
9. Tests: `test_auth_service.py` fake already supported arbitrary roles — 2 new tests. `test_nutritionist_profile_service.py` fake extended to round-trip the new fields (including a sentinel for "macro_split not present in payload" vs "explicitly cleared to null") + `mark_onboarding_completed`; 2 new tests.

## Constraints

- `complete-onboarding` is a dedicated `POST` action, not a client-settable field on the `PATCH` payload — keeps completion timestamping server-authoritative and gives the wizard's last step one unconditional call regardless of which earlier steps were skipped.
- Reused the existing `if x is not None` partial-update semantics on `PATCH /nutritionist_profile/me` (already established) rather than introducing new update semantics for the new fields.
