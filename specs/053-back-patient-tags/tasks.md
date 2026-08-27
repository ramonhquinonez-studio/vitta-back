# Tasks: Patient Tags (Client Groups)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/entities.py`: campo `tags`.
- [x] T003 `schemas/patients.py`: `tags` en `PatientIn`/`PatientUpdate`/`PatientOut`.
- [x] T004 `mongo_patients_repository.py`: `_to_entity` mapea `tags`.
- [x] T005 `router.py`: `_serialize` incluye `tags`.
- [x] T006 `tests/test_patients_service.py`: fake repo actualizado + test de round-trip.

## Phase 3: Validation

- [x] T007 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 218/218 verde.
- [x] T008 Verificación en vivo por curl: crear paciente con tags, actualizar tags, confirmar en `GET`. Limpieza de datos QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 218/218 verde, sin regresiones.
- curl en vivo: create con `tags: ["VIP","Grupo A"]` → confirmado en respuesta; PATCH con `tags: ["VIP"]` → confirmado en `GET` posterior. Datos de prueba limpiados con script directo de Motor.
