# Tasks: Back Patients Module Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Module Foundation

- [x] T002 Crear `domain`, `application`, `infrastructure` y `presentation` para `patients`.
- [x] T003 Mover CRUD y ownership al `PatientsService`.
- [x] T004 Dejar `app/routers/patients.py` como wrapper delgado.
- [x] T005 Agregar test unitario del servicio.
- [x] T006 Actualizar docs y roadmap.

## Phase 3: Validation

- [x] T007 Ejecutar unittest y py_compile del slice.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest tests.test_patients_service`
- `python3 -m py_compile app/routers/patients.py app/modules/patients/domain/entities.py app/modules/patients/domain/repositories.py app/modules/patients/application/patients_service.py app/modules/patients/infrastructure/mongo_patients_repository.py app/modules/patients/presentation/router.py`
