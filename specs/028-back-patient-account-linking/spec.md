# Feature Specification: Patient-Scoped Invite Codes (Account Linking)

**Feature Branch**: `028-back-patient-account-linking`
**Created**: 2026-08-19
**Status**: Draft
**Type**: Bugfix

## Objective

A nutritionist who creates a patient chart directly (`POST /patients`, `028-patients-direct-create` in `nutri_pro`) had no way to later let that same patient download the app and log in without ending up with a **duplicate** patient record — every invite code redemption unconditionally created a brand-new `patients` document, regardless of whether a chart already existed for that person. Let an invite code be scoped to a specific existing chart, so redemption links the account to it instead.

## In Scope

- `Patient.user_id` (nullable) — set once a chart is linked to a real login-capable account. `PatientOut` exposes it so clients can show linked/unlinked state.
- `invite_codes` documents gain an optional `patient_id`.
- `POST /patients/{patient_id}/invite-code` — generates a code scoped to that chart. Rejects with 404 if the patient doesn't belong to the caller, 400 if it's already linked (`user_id` already set).
- `AuthService.register()`: if the redeemed invite carries a `patient_id`, the new user is linked to that *existing* patient (`user_id` set on it) instead of a new patient document being created — preserving whatever name/age/sex/height/allergies/notes the nutritionist had already filled in. Falls back to the old create-a-new-patient behavior if the invite is unscoped, or defensively if the linked chart was deleted/already claimed between invite creation and redemption.
- The existing unscoped `POST /patients/invite-codes` is unchanged — still the right tool for "invite someone not in my roster yet."

## Out of Scope

- Un-linking an account from a patient, or re-scoping an invite after creation.
- Merging two already-separate patient records after the fact (this slice prevents the duplicate going forward; it doesn't clean up duplicates that already exist from before this change).

## Baseline Behavior

- `AuthService.register()` always called `create_patient_for_user(...)`, inserting a brand-new `patients` document on every redemption. A chart created via `POST /patients` and a chart created via invite redemption for the "same" person were always two disconnected records.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`
- **Cross-repo impact**: `nutri_pro` gains "Invitar a esta paciente" on patient detail (its own spec).

## Acceptance Criteria

1. Given a nutritionist creates a chart-only patient, generates a scoped invite code for them, and the patient redeems it, then that same patient record gets `user_id` set — no second record is created.
2. Given a nutritionist tries to generate another scoped invite for an already-linked patient, then the request is rejected with 400.
3. Given an unscoped invite code (no `patient_id`) is redeemed, then behavior is unchanged from before — a new patient record is created, exactly as today.
4. Given a scoped invite's linked patient somehow no longer exists at redemption time, then registration still succeeds by falling back to creating a new patient record — it never leaves the new user with no patient record at all.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 92/92 green (6 new tests across `test_auth_service.py` and `test_patients_service.py`).
- Manual: `curl` end-to-end against the live local backend — created a chart-only patient, generated a scoped invite, confirmed `user_id: null` beforehand, redeemed it, confirmed the *same* patient id now carries the new user's `user_id`, confirmed the roster still shows exactly one record (not two), confirmed a second invite attempt on that now-linked patient returns 400, confirmed the new account can actually log in, and confirmed the unscoped invite flow still creates a fresh patient as before.
