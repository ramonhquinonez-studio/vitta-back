# Feature Specification: Nutritionist Onboarding — Backend Foundation

**Feature Branch**: `025-back-nutritionist-onboarding`
**Created**: 2026-08-19
**Status**: Draft
**Type**: Feature

## Objective

Give `nutri_pro` a real self-serve nutritionist signup path, and extend `NutritionistProfile` with the fields a 5-step onboarding wizard needs to collect (professional profile, specialization, workflow defaults). Before this slice, every nutritionist account was seeded directly — `POST /auth/register` was hardcoded to `role="patient"` and required an invite code, so there was no way for a nutritionist to create their own account at all.

## In Scope

- `POST /auth/register-nutritionist` — `name`, `email`, `password`, no invite code, creates `role="nutritionist"`. Mirrors `POST /auth/register`'s validation/duplicate-email handling but skips invite-code lookup and patient-record creation entirely.
- `NutritionistProfile` gains three new field groups, all optional (every onboarding step past account creation is skippable):
  - Professional profile: `cedula`, `practice_name`, `logo_url`, `brand_color`, `city`.
  - Specialization: `specializations: list[str]`.
  - Workflow defaults: `energy_equation` (`mifflin` | `harris_benedict` | `fao_oms`), `portions_mode` (`equivalentes` | `gramos` | `ambos`), `macro_split` (`{protein_pct, carbs_pct, fat_pct}`), `units` (`metric` | `imperial`), `meals_per_day`.
  - Tracking: `onboarding_completed_at`.
- `POST /nutritionist_profile/me/complete-onboarding` — sets `onboarding_completed_at` to the current server time. A dedicated action rather than letting the client PATCH the timestamp directly, so completion time can't be spoofed/skewed by the client and the wizard's last step is a single unconditional call regardless of which earlier steps were skipped.

## Out of Scope

- The wizard UI itself (`nutri_pro`, tracked separately).
- Forcing existing (pre-onboarding) nutritionist accounts through the wizard — `onboarding_completed_at` will be `null` for all of them; deciding what the client does with that is a client-side concern.
- Logo file storage specifics — `logo_url` is just a string field here; upload mechanics reuse the existing generic file-storage pattern already used for InBody/plan attachments when the client-side work lands.

## Baseline Behavior

- No nutritionist self-registration path existed at all.
- `NutritionistProfile` had five fields total (`role_label`, `bio`, `years_experience`, `session_price(+currency)`, `social_links`) — nothing about professional credentials, specialization, or workflow preferences.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a `POST /auth/register-nutritionist` with valid fields, then a `role="nutritionist"` user is created and no patient record is created.
2. Given the same email is used twice, then the second call returns `400`.
3. Given a nutritionist `PATCH`es their profile with any subset of the new fields, then only those fields change — everything else (including fields from a previous PATCH) is preserved.
4. Given a nutritionist calls `POST /nutritionist_profile/me/complete-onboarding`, then `onboarding_completed_at` is set server-side, regardless of what other fields are or aren't populated.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 68/68 green (4 new tests: 2 in `test_auth_service.py`, 2 in `test_nutritionist_profile_service.py`).
- Manual: `curl POST /auth/register-nutritionist` → `200` with a real nutritionist account created; logged in as that account; `PATCH /nutritionist_profile/me` with the full new field set → all fields echoed back correctly; `POST /nutritionist_profile/me/complete-onboarding` → `onboarding_completed_at` populated with a real server timestamp. Test account (`test.onboarding.verify@nutri.app`) left in place — no delete-user endpoint exists, and it doesn't touch any real patient/nutritionist data.
