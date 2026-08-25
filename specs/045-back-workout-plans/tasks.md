# Tasks: Workout Plans

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `workout_plans/domain` + `infrastructure` + `application`.
- [x] T003 `schemas/workout_plan.py` + `workout_plans/presentation/router.py`.
- [x] T004 `routers/workout_plans.py` wrapper + wiring en `main.py`.
- [x] T005 Índices en `workout_plans`/`workout_plan_assignments`/`workout_logs`.
- [x] T006 `me` module: `get_active_workout_plan`/`list_workout_logs`/`toggle_workout_log` + endpoints.
- [x] T007 `patients` module: `list_workout_plan_assignments`/`list_workout_logs` + endpoints.
- [x] T008 Tests: `test_workout_plans_service.py` (8 casos), `test_me_service.py` (+6), `test_patients_service.py` (+3).

## Phase 3: Validation

- [x] T009 Suite completa → 197/197 verde.
- [x] T010 Verificación en vivo end-to-end (crear plan de 2 días, asignar, ver plan activo, alternar completado/incompleto, ver adherencia desde el nutriólogo, aislamiento entre tenants).

## Evidence

- Suite completa: 197/197 verde.
- Verificación en vivo: plan de entrenamiento con ejercicios de fuerza y timed creado y asignado; `GET /me/workout-plan/active` del paciente lo devuelve completo; toggle de ejercicio confirmado en ambas direcciones (paciente y nutriólogo) y en ambos sentidos (completado → incompleto); lecturas cruzadas entre tenants (plan y logs) devuelven 404. Cuentas y datos de prueba limpiados al final.
