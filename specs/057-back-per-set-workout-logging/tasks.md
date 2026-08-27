# Tasks: Per-Set Patient Workout Logging (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/workout_log.py`: `WorkoutSetLogIn`, `WorkoutExerciseLogIn`.
- [x] T003 `me/presentation/router.py`: `PUT /me/workout-logs/exercise`.
- [x] T004 `me/application/me_service.py`, `me/domain/repositories.py`, `me/infrastructure/mongo_me_repository.py`: `upsert_workout_log` (upsert real, no delete/insert).
- [x] T005 `patients/domain/repositories.py`, `patients/infrastructure/mongo_patients_repository.py`, `patients/application/patients_service.py`: `toggle_coach_workout_log` (flip `coach_marked_done` solamente).
- [x] T006 `mongo_patients_repository.py`: dashboard de inactividad usa `updated_at` en vez de `completed_at`.
- [x] T007 `tests/test_me_service.py`, `tests/test_patients_service.py` actualizados.

## Phase 3: Validation

- [x] T008 Suite de unittest completa → 217/217 verde.
- [x] T009 Verificación en vivo por curl: upsert reemplaza (no duplica); coach-toggle no borra `sets` del paciente y flipea `coach_marked_done` en ambos sentidos.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 217/217 verde.
- Curl en vivo contra `http://127.0.0.1:8000`: los cuatro criterios de aceptación confirmados; datos de prueba limpiados vía script Motor directo.
