# Tasks: Body Compositions List (Owner)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `patients/domain/repositories.py`: `list_body_compositions` en el protocolo.
- [x] T003 `mongo_patients_repository.py`: `list_body_compositions`.
- [x] T004 `patients_service.py`: `list_body_compositions`.
- [x] T005 `patients/presentation/router.py`: `GET /patients/{patient_id}/body_compositions`.
- [x] T006 `tests/test_patients_service.py`: 2 tests nuevos.

## Phase 3: Validation

- [x] T007 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 45/45 verde.
- [x] T008 Manual `curl GET /patients/{id}/body_compositions` (paciente demo) → 5 escaneos reales, más recientes primero.

## Evidence

- Suite completa de backend en verde (45 tests, antes 43).
- `curl GET /patients/{id}/body_compositions` → `200`, 5 escaneos reales ordenados por fecha descendente, incluyendo uno con `attachment_url` real de una prueba manual anterior.
