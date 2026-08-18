# Feature Specification: Nutritionist Profile

**Feature Branch**: `017-back-nutritionist-profile`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Feature

## Objective

Give the nutritionist an editable professional profile (role, bio, years of experience, session price, social links), and let a linked patient read it. Before this slice, no such schema existed at all — `nutri_app`'s patient-facing profile screen showed 100% hardcoded fake data regardless of which nutritionist actually owned the patient.

## In Scope

- New `nutritionist_profiles` collection (one doc per owner, unique index on `owner_id`).
- `GET/PATCH /nutritionist_profile/me` — the nutritionist's own profile, upserted on first `PATCH`. Response includes a computed `patient_count` (live `count_documents` on `patients`, not stored).
- `GET /me/nutritionist_profile` (added to the existing `me` module) — the current patient's linked nutritionist's profile, resolved via `patient.owner_id`, joined with `users.name`.

## Out of Scope

- A review/rating system — the previous hardcoded patient-side profile showed fake "Reviews"/"Rating" stats; this slice doesn't replace them with a real backend, it just stops fabricating numbers (the client drops those two stat cards).
- Profile photo upload — text/structured fields only.

## Baseline Behavior

- No nutritionist-profile concept existed anywhere in the backend.

## Target Design

- `PATCH /nutritionist_profile/me` with `{"role_label": "...", "bio": "...", "years_experience": 12, "session_price": 650.0, "session_price_currency": "MXN", "social_links": [{"platform": "instagram", "handle": "@..."}]}` → `200` with the full profile including `patient_count`.
- `GET /me/nutritionist_profile` (as a linked patient) → the same saved fields plus the nutritionist's `name` from `users`.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a nutritionist with no saved profile yet, when `GET /nutritionist_profile/me` is called, then it returns all-`null` fields plus a real `patient_count` (not a 404).
2. Given a `PATCH` with new field values, when a subsequent `GET` is made (by the same nutritionist or a linked patient via `/me/nutritionist_profile`), then the same values round-trip.
3. Given a patient with no linked nutritionist, when `GET /me/nutritionist_profile` is called, then it returns `null`, not an error.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 39/39 green (new: `test_nutritionist_profile_service.py`, 2 new tests in `test_me_service.py`).
- Manual: `curl -X PATCH /nutritionist_profile/me` as the nutritionist, then `curl GET /me/nutritionist_profile` as a linked patient → same saved values round-trip live against the dev database.
