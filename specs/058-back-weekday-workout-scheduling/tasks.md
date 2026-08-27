# Tasks: Weekday-Based Workout Scheduling (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/workout_plan.py`: `WorkoutDayIn.weekdays` + validador de rango.
- [x] T003 `workout_plans_service.py`: `_validate_payload` rechaza weekdays repetidos entre días.
- [x] T004 `tests/test_workout_plans_service.py`: 2 tests nuevos.

## Phase 3: Validation

- [x] T005 Suite de unittest completa → 219/219 verde.
- [x] T006 Verificación en vivo por curl: weekdays distintos (200), weekday repetido (400), weekday fuera de rango (422).

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 219/219 verde.
- Curl en vivo contra `http://127.0.0.1:8000`: los tres criterios de aceptación confirmados; datos de prueba limpiados vía script Motor directo.
