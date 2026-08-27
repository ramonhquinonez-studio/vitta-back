# Tasks: Multi-Media Exercises (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice (backfilled after implementation).

## Phase 2: Implementation

- [x] T002 `app/schemas/workout_plan.py`: `WorkoutMediaIn`, `WorkoutExerciseIn.media`.
- [x] T003 `app/modules/workout_plans/presentation/router.py`: endpoint `upload_exercise_media` renombrado a `POST /workout-plans/exercise-media`, gate de content-type ampliado.

## Phase 3: Validation

- [x] T004 Suite de unittest completa → 218/218 verde, sin cambios de test.
- [x] T005 Verificación en vivo por curl: imagen → `media_type: photo`; video → `media_type: video`; `text/plain` → 400; plan con 2 medios round-tripa correctamente.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 218/218 verde.
- Curl en vivo contra `http://127.0.0.1:8000`: los tres casos de aceptación confirmados; datos de prueba limpiados vía script Motor directo.
