# Implementation Plan: Body Compositions List (Owner)

**Branch**: `019-back-body-compositions-list` | **Date**: 2026-08-17 | **Spec**: `specs/019-back-body-compositions-list/spec.md`

## Summary

Extends the existing `patients` module with a read path mirroring the write path's ownership check.

## Steps

1. `app/modules/patients/domain/repositories.py`: add `list_body_compositions` to the `PatientsRepository` Protocol.
2. `app/modules/patients/infrastructure/mongo_patients_repository.py`: `list_body_compositions` — same ownership check as `add_body_composition`, then `body_compositions.find({"patient_id": ...}).sort("at", -1)`.
3. `app/modules/patients/application/patients_service.py`: `list_body_compositions`, raises `LookupError` when the repository returns `None`.
4. `app/modules/patients/presentation/router.py`: `GET /patients/{patient_id}/body_compositions`.
5. `tests/test_patients_service.py`: fake repository gains `body_compositions`/`list_body_compositions`; 2 new tests.

## Constraints

- No new Pydantic schema — reuses `response_model=list[dict]`, matching the existing `POST` endpoint's `response_model=dict` convention for this resource.
