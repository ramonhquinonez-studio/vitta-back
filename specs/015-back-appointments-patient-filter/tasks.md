# Tasks: Appointments patient_id Filter

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `appointments/domain/repositories.py`: `patient_id` en el Protocol.
- [x] T003 `appointments/infrastructure/mongo_appointments_repository.py`: filtro en el `$match`.
- [x] T004 `appointments/application/appointments_service.py`: passthrough.
- [x] T005 `appointments/presentation/router.py`: query param `patientId`.
- [x] T006 `tests/test_appointments_service.py`: fake repo + test nuevo.

## Phase 3: Validation

- [x] T007 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 32/32 verde.
- [x] T008 Manual: `curl "GET /appointments?patientId=..."` contra servidor dev real → 4 citas de Ramon; id inexistente → `[]`.

## Evidence

- `unittest discover` → Ran 32 tests, OK.
- `curl` con `patientId` real → 4 resultados; con id inexistente → `[]`.
