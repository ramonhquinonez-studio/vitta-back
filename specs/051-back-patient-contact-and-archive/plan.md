# Implementation Plan: Patient Contact Info + Archive Instead of Hard Delete

**Branch**: `051-back-patient-contact-and-archive` | **Date**: 2026-08-26 | **Spec**: `specs/051-back-patient-contact-and-archive/spec.md`

## Summary

Additive fields on `Patient` plus a repository-level behavior swap: `delete_for_owner` (hard `delete_one`) becomes `archive_for_owner`/`unarchive_for_owner` (`update_one` setting/clearing `archived_at`). No migration needed — dev DB has no production data, and the fields are nullable/optional throughout.

## Steps

1. `app/modules/patients/domain/entities.py`: add `email: str | None`, `phone: str | None`, `archived_at: datetime | None` to `Patient`.
2. `app/schemas/patients.py`: add `email: Optional[EmailStr]`, `phone: Optional[str]` to `PatientIn`/`PatientUpdate`; add `email`, `phone`, `archived_at` to `PatientOut`.
3. `app/modules/patients/domain/repositories.py`: `list_for_owner` gains `include_archived: bool = False`; `delete_for_owner` → `archive_for_owner(...) -> Patient | None`; add `unarchive_for_owner(...) -> Patient | None`.
4. `app/modules/patients/infrastructure/mongo_patients_repository.py`: `_to_entity` maps the 3 new fields; `list_for_owner` filters `archived_at: None` unless `include_archived`; `count_for_owner` also excludes archived; `archive_for_owner`/`unarchive_for_owner` implemented via `update_one` + refetch (mirrors `update_for_owner`'s shape); `get_dashboard`'s patient-count queries add `archived_at: None`.
5. `app/modules/patients/application/patients_service.py`: `delete_patient` → `archive_patient` (raises `LookupError`), add `unarchive_patient`; `list_patients` passes `include_archived` through.
6. `app/modules/patients/presentation/router.py`: `_serialize` includes the 3 new fields; `list_patients` gains `include_archived: bool = Query(False)`; `DELETE /{patient_id}` now calls `archive_patient` and returns `PatientOut`; new `POST /{patient_id}/unarchive`.
7. `tests/test_patients_service.py`: `_FakePatientsRepository` updated to match (archive/unarchive, `include_archived`, `email`/`phone` on create/update); new tests for archive/unarchive visibility and email/phone round-trip.

## Constraints

- `DELETE /{patient_id}`'s route path/verb is unchanged — only its underlying behavior (archive vs. hard-delete) and response shape (now `PatientOut` instead of `{"ok": true}`) change.
- No cascading changes to a patient's appointments/plans/logs when archived — they remain queryable by id, just the patient no longer shows in the default roster.
