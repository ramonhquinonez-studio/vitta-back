# Feature Specification: Invite Code Preview (Unauthenticated)

**Feature Branch**: `029-back-invite-code-preview`
**Created**: 2026-08-19
**Status**: Draft
**Type**: Feature

## Objective

`028-back-patient-account-linking` let an invite code be scoped to an existing patient chart, but the register screen had no way to know *before submission* whether a typed code was valid, scoped, or whose chart it would link to. Add a read-only, unauthenticated preview endpoint so the client can react while the patient is still typing — show who invited them, and for scoped codes, which existing patient they're about to become — instead of only finding out after `POST /auth/register` completes.

## In Scope

- `GET /auth/invite-codes/{code}` — unauthenticated. Returns `{valid, scoped, patient_name, nutritionist_name}`.
- `AuthService.preview_invite_code(code)`: validates existence/used/expired (same rules `register()` already enforces), resolves `patient_name` via the linked chart when scoped, resolves `nutritionist_name` via the invite's `owner_id`.
- `AuthRepository.get_patient_name(patient_id)` — new narrow read, added to the Protocol and implemented in `MongoAuthRepository`.

## Out of Scope

- Any change to `POST /auth/register`'s own validation or linking behavior (unchanged from `028-back-patient-account-linking`).
- Rate-limiting the new endpoint — it's read-only and leaks no more than an invite code's holder already learns by attempting registration.

## Baseline Behavior

- The only way to learn anything about an invite code was to redeem it via `POST /auth/register`, which requires a full name/email/password and actually creates the account.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`
- **Cross-repo impact**: `nutri_app`'s register screen consumes this endpoint (`034-front-invite-aware-registration` there).

## Acceptance Criteria

1. Given an unscoped, unused, unexpired code, when previewed, then `{valid: true, scoped: false, nutritionist_name: <owner's name>}` is returned.
2. Given a scoped code linking to an existing patient, when previewed, then `{valid: true, scoped: true, patient_name: <chart's name>, nutritionist_name: <owner's name>}` is returned.
3. Given an unknown, already-used, or expired code, when previewed, then `{valid: false}` is returned (never a 404/500) — the field is meant to drive inline UI feedback, not error handling.
4. Given a code typed in a different case than it was generated, when previewed, then it still resolves correctly (codes are normalized to uppercase on both write and read).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 95/95 green (3 new tests in `test_auth_service.py`).
- Manual: `curl` against the live local backend covering unscoped, scoped, unknown, used, expired, and case-insensitive lookups — all returned exactly the expected shape.
