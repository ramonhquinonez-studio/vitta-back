# Implementation Plan: Patient Self-Registration + Nutritionist Claim by Connection Code

**Branch**: `030-back-patient-self-registration` | **Date**: 2026-08-19 | **Spec**: `specs/030-back-patient-self-registration/spec.md`

## Summary

`Patient.owner_id` loses its "always present" invariant — the single biggest structural change, since every existing repository method in the `patients` module is named/typed around an owner always existing. Registration branches on whether an invite code was given; the unowned-patient creation path and the claim-by-code path are new, narrow additions that don't touch the owner-scoped query surface at all (an unclaimed patient simply never matches any `owner_id` filter, so it can't leak into any existing roster/detail endpoint).

## Steps

1. `patients/domain/entities.py`: `Patient.owner_id: str | None = None`, reordered after `name` (both `id`/`name` stay required, non-default).
2. `patients/infrastructure/mongo_patients_repository.py`: `_to_entity` reads `owner_id` via the existing `_stringify_maybe_oid` helper (was unconditional `str(...)`, would coerce `None` into the literal string `"None"`); new `claim_patient(owner_id, code)` — `find_one_and_update` matching `{"connection_code": CODE, "owner_id": None}`, setting `owner_id` and unsetting `connection_code` atomically (same null-guard pattern as `link_user_to_patient`, preventing two nutritionists racing on one code).
3. `patients/domain/repositories.py` + `application/patients_service.py`: `claim_patient` Protocol method + service wrapper raising `LookupError` on a `None` result.
4. `app/schemas/patients.py`: `PatientOut.owner_id` → `Optional[str]`; new `ClaimPatientIn{code}`.
5. `patients/presentation/router.py`: `POST /patients/claim`.
6. `auth/domain/repositories.py` + `infrastructure/mongo_auth_repository.py`: `create_unowned_patient_for_user(user_id, name) -> str` — inserts a patient doc with `owner_id: None` (explicit key, not omitted — the claim query above depends on it being present as `None` to match) and a freshly generated `connection_code`, returns the code.
7. `auth/application/auth_service.py`: `register()`'s `invite_code` becomes `str | None`; blank/whitespace normalizes to "not provided." When absent, skips the whole invite-lookup/link/create-patient-for-invite block and calls `create_unowned_patient_for_user` instead.
8. `app/schemas/auth.py`: `RegisterIn.invite_code: str | None = Field(None, max_length=40)`.
9. `me/infrastructure/mongo_me_repository.py`: `get_patient_for_user` passes through `connection_code`.
10. `app/db/init_indexes.py`: sparse unique index on `patients.connection_code` (sparse because most patients never have this field).

## Constraints

- `create_unowned_patient_for_user` and the invite-based `create_patient_for_user` stay as two separate repository methods rather than one parameterized method — they insert genuinely different shapes (one gets `owner_id` + no code, the other gets no `owner_id` + a code), and conflating them would need an awkward "sometimes-required" parameter pair.
- The connection code is deliberately **not** given an expiry, unlike invite codes (`_INVITE_CODE_EXPIRE_DAYS`) — it's the patient's own standing identifier until claimed, not a time-boxed one-time invitation, so there's no natural TTL to attach.
- Reused the exact alphabet/length/`secrets.choice` generator already in `mongo_patients_repository.py` rather than inventing a second one, so both code families read the same at a glance.
