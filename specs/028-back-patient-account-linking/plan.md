# Implementation Plan: Patient-Scoped Invite Codes (Account Linking)

**Branch**: `028-back-patient-account-linking` | **Date**: 2026-08-19 | **Spec**: `specs/028-back-patient-account-linking/spec.md`

## Summary

Additive changes across two already-migrated modules (`patients` gains the scoped-invite endpoint and validation; `auth` gains the linking side of registration) plus a cross-module data dependency: `auth`'s registration flow needs to write `user_id` onto a `patients` document, which it already had a narrow capability for (`create_patient_for_user`) — this just adds a sibling `link_user_to_patient` for the "attach to existing" case instead of "always insert new."

## Steps

1. `patients/domain/entities.py`: `Patient.user_id: str | None = None`.
2. `patients/domain/repositories.py` + `infrastructure/mongo_patients_repository.py`: `create_invite_code(owner_id, patient_id=None)` stores `patient_id` on the invite doc; `_to_entity` reads `user_id`.
3. `patients/application/patients_service.py`: `create_invite_code` validates the patient when `patient_id` is given (404 if not owned, 400 if already linked) before delegating.
4. `app/schemas/patients.py` + `presentation/router.py`: `PatientOut.user_id`; new `POST /{patient_id}/invite-code`.
5. `auth/domain/repositories.py` + `infrastructure/mongo_auth_repository.py`: `get_invite_code` returns `patient_id`; new `link_user_to_patient(user_id, patient_id)` — a guarded `update_one` filtering on `{"_id": ..., "user_id": None}` so it can never silently overwrite an existing link (race-condition-safe, returns `False` if it didn't match).
6. `auth/application/auth_service.py`: `register()` tries `link_user_to_patient` first when the invite has a `patient_id`; only falls back to `create_patient_for_user` if that didn't apply or didn't succeed.

## Constraints

- `link_user_to_patient`'s filter includes `"user_id": None` specifically so two near-simultaneous redemption attempts (which shouldn't be possible given invite codes are single-use, but cheap to guard anyway) can't both "succeed" against the same chart.
- Deliberately did not touch `014-back-consultation-history-linkage`'s `GET /me/consultations` or anything else reading `patients.user_id` — this slice only adds the field and the one write path that sets it.
