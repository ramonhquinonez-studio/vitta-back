# Tasks: Patient Contact Info + Archive Instead of Hard Delete

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/entities.py`: `email`, `phone`, `archived_at` en `Patient`.
- [x] T003 `schemas/patients.py`: `email`/`phone` en `PatientIn`/`PatientUpdate`; +3 campos en `PatientOut`.
- [x] T004 `domain/repositories.py`: `include_archived` en `list_for_owner`; `archive_for_owner`/`unarchive_for_owner`.
- [x] T005 `mongo_patients_repository.py`: filtros de `archived_at` en `list_for_owner`/`count_for_owner`/`get_dashboard`; implementación de archive/unarchive.
- [x] T006 `patients_service.py`: `archive_patient`/`unarchive_patient`; `include_archived` en `list_patients`.
- [x] T007 `router.py`: `DELETE /{id}` archiva y devuelve `PatientOut`; nuevo `POST /{id}/unarchive`; `include_archived` query param.
- [x] T008 `tests/test_patients_service.py`: fake repo actualizado + nuevos tests.

## Phase 3: Validation

- [x] T009 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 217/217 verde.
- [x] T010 Verificación en vivo por curl: crear paciente con email/phone, archivar, listar con/sin `include_archived`, desarchivar, toggle de workout log ajeno (ver `052-back-coach-workout-log-toggle`). Limpieza de datos QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 217/217 verde, sin regresiones.
- curl en vivo contra servidor local: create → archive (`archived_at` set, desaparece de `GET /patients`) → `include_archived=true` (reaparece) → unarchive (`archived_at` null, reaparece en default). Datos de prueba limpiados con script directo de Motor.
