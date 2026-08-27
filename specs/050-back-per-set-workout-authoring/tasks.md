# Tasks: Per-Set Workout Authoring

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/workout_plan.py`: `WorkoutSetIn` + `WorkoutExerciseIn.sets` como lista.
- [x] T003 Verificado: sin cambios en repositorio/servicio (pass-through de dict crudo).
- [x] T004 Fixtures actualizados en `test_workout_plans_service.py`.

## Phase 3: Validation

- [x] T005 Suite completa → 210/210 verde.
- [x] T006 Verificación en vivo (3 sets distintos por ejercicio, round-trip exacto; RPE fuera de rango rechazado con 422).

## Evidence

- Suite completa: 210/210 verde.
- Verificación en vivo: ejercicio con set de rango de reps, set de reps fijas, y set por tiempo — los tres confirmados idénticos entre `POST` y `GET`; `rpe: 11` rechazado con `422`. Cuenta y datos de prueba limpiados al final.
