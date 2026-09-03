# Implementation Plan: Distinct Tags & Allergies Endpoints

**Branch**: `075-back-patient-known-tags-allergies` | **Date**: 2026-08-30 | **Spec**: `specs/075-back-patient-known-tags-allergies/spec.md`

## Summary

Add `list_distinct_tags`/`list_distinct_allergies` through the `patients` module's Protocol → service → Mongo repository → router, and register `GET /patients/tags`/`GET /patients/allergies` ahead of the existing `GET /patients/{patient_id}` route so the literal paths aren't swallowed by the path parameter.

## Steps

1. `domain/repositories.py`: `PatientsRepository` Protocol gains `list_distinct_tags(owner_id)` / `list_distinct_allergies(owner_id)`.
2. `application/patients_service.py`: `list_known_tags`/`list_known_allergies` passthroughs.
3. `infrastructure/mongo_patients_repository.py`: both implemented via `self._db.patients.distinct(field, {"owner_id": owner_oid})`, deduped/sorted, empty strings filtered.
4. `presentation/router.py`: `GET /patients/tags` and `GET /patients/allergies`, placed immediately before `GET /{patient_id}` (Starlette matches routes in registration order — a static route registered after a `{patient_id}` route would never be reached, since `"tags"`/`"allergies"` would already match the dynamic segment first).
5. `tests/test_patients_service.py`: fake repository gains both methods (derived from its own in-memory `patients` dict); 2 new tests.

## Constraints

- Reuses the exact `collection.distinct()` call shape already present in this file (`mongo_patients_repository.py`'s dashboard-inactivity query), not a new pattern.
- No new Pydantic schema needed — both endpoints return `list[str]` directly.
