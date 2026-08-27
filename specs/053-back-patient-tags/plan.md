# Implementation Plan: Patient Tags (Client Groups)

**Branch**: `053-back-patient-tags` | **Date**: 2026-08-26 | **Spec**: `specs/053-back-patient-tags/spec.md`

## Summary

Additive `tags: list[str]` field on `Patient`, following the exact shape/plumbing already established for `allergies` — no filtering, no new endpoint.

## Steps

1. `app/modules/patients/domain/entities.py`: `tags: list[str] = field(default_factory=list)`.
2. `app/schemas/patients.py`: `tags: Optional[List[str]] = None` on `PatientIn`/`PatientUpdate`; `tags: List[str] = []` on `PatientOut`.
3. `app/modules/patients/infrastructure/mongo_patients_repository.py`: `_to_entity` maps `tags` (`list(document.get("tags") or [])`).
4. `app/modules/patients/presentation/router.py`: `_serialize` includes `tags`.
5. `tests/test_patients_service.py`: `_FakePatientsRepository.create_for_owner`/`update_for_owner` accept `tags`; new test asserting create+update round-trip.

## Constraints

- No query param, no filter logic, no dashboard changes — purely a persist-and-round-trip field, matching `allergies`.
