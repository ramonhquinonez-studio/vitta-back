# Implementation Plan: Invite Code Preview (Unauthenticated)

**Branch**: `029-back-invite-code-preview` | **Date**: 2026-08-19 | **Spec**: `specs/029-back-invite-code-preview/spec.md`

## Summary

Additive, read-only slice on the already-migrated `auth` module: one new repository read (`get_patient_name`), one new service method reusing `register()`'s existing validity checks, one new unauthenticated router endpoint placed ahead of `/register`.

## Steps

1. `app/schemas/auth.py`: `InvitePreviewOut{valid, scoped=False, patient_name=None, nutritionist_name=None}`.
2. `auth/domain/repositories.py`: `AuthRepository.get_patient_name(patient_id) -> str | None`.
3. `auth/infrastructure/mongo_auth_repository.py`: implement `get_patient_name` (reads `patients.name` by ObjectId).
4. `auth/application/auth_service.py`: `preview_invite_code(code) -> dict` — same existence/used/expired checks as `register()`; resolves `patient_name` when `invite.patient_id` is set, `nutritionist_name` via the existing `get_user_by_id`.
5. `auth/presentation/router.py`: `GET /invite-codes/{code}`, registered before `/register` so the static path doesn't shadow it.
6. `tests/test_auth_service.py`: extend `_FakeAuthRepository` with `get_patient_name`; add unscoped/scoped/invalid preview tests.

## Constraints

- Reuses `register()`'s exact validity rules (used_at/expires_at) rather than a parallel copy, so the two never drift out of sync.
- Returns `{valid: false}` for every invalid case instead of distinguishing 404/used/expired — the client only needs a boolean to gate UI, and a more granular error surface isn't worth the extra states for now.
