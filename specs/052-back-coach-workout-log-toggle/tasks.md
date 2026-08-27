# Tasks: Coach-Side Workout Log Toggle

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/repositories.py`: `toggle_workout_log` en el protocolo.
- [x] T003 `mongo_patients_repository.py`: implementación (guard de ownership + toggle por clave).
- [x] T004 `patients_service.py`: validación de campos requeridos + `LookupError`.
- [x] T005 `router.py`: `POST /{patient_id}/workout-logs/toggle`.
- [x] T006 `tests/test_patients_service.py`: fake repo + tests (toggle on/off, campos faltantes, paciente ajeno).

## Phase 3: Validation

- [x] T007 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 217/217 verde.
- [x] T008 Verificación en vivo por curl: crear rutina, asignar, toggle on/off, 404 paciente ajeno, 400 campo faltante. Limpieza de datos QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 217/217 verde, sin regresiones.
- curl en vivo: toggle on → `GET /patients/{id}/workout-logs` muestra 1 entrada → toggle off → lista vacía. 404 confirmado contra paciente de otro dueño (id inexistente). 400 confirmado con payload sin `day_index`/`exercise_index`. Datos de prueba limpiados con script directo de Motor.
