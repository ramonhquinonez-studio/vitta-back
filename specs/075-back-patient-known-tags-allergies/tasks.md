# Tasks: Distinct Tags & Allergies Endpoints

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/repositories.py`: métodos `list_distinct_tags`/`list_distinct_allergies` en el Protocol.
- [x] T003 `application/patients_service.py`: `list_known_tags`/`list_known_allergies`.
- [x] T004 `infrastructure/mongo_patients_repository.py`: implementación vía `.distinct()`.
- [x] T005 `presentation/router.py`: `GET /patients/tags`, `GET /patients/allergies` (antes de `/{patient_id}`).
- [x] T006 `tests/test_patients_service.py`: fake repo + 2 tests nuevos.

## Phase 3: Validation

- [x] T007 Suite completa del backend → verde (249 tests).

## Evidence

- `PYTHONPATH=. python -m unittest discover -s tests -p "test_*.py"`: "OK" (249 tests).
