# Tasks: Back Appointments Module Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Module Foundation

- [x] T002 Crear `domain`, `application`, `infrastructure` y `presentation` para `appointments`.
- [x] T003 Mover CRUD, overlap y serialización al módulo.
- [x] T004 Encapsular sync de Google Calendar fuera del router.
- [x] T005 Dejar `app/routers/appointments.py` como wrapper delgado.
- [x] T006 Agregar test unitario del servicio.
- [x] T007 Actualizar docs y roadmap.

## Phase 3: Validation

- [x] T008 Ejecutar unittest y py_compile del slice.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest tests.test_appointments_service`
- `python3 -m py_compile app/routers/appointments.py app/modules/appointments/domain/entities.py app/modules/appointments/domain/repositories.py app/modules/appointments/application/appointments_service.py app/modules/appointments/infrastructure/mongo_appointments_repository.py app/modules/appointments/infrastructure/google_calendar_gateway.py app/modules/appointments/presentation/router.py`
