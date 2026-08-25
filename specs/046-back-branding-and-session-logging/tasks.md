# Tasks: Per-Tenant Branding Upload + Exercise Library + Logged Session Details

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `nutritionist_profile`: `POST /me/logo`.
- [x] T003 `me`: `get_nutritionist_profile` incluye `practice_name`/`logo_url`/`brand_color`.
- [x] T004 `me`/`patients`: `toggle_workout_log` + `list_workout_logs` con `details` (sets/reps/weight/rpe/comment).
- [x] T005 Nuevo módulo `exercise_library` (domain/application/infrastructure/presentation).
- [x] T006 `schemas/exercise_library.py` + `routers/exercise_library.py` wrapper + wiring en `main.py`.
- [x] T007 Índice en `exercise_library`.
- [x] T008 Tests: `test_exercise_library_service.py` (5 casos), `test_me_service.py` (+1 caso).

## Phase 3: Validation

- [x] T009 Suite completa → 203/203 verde.
- [x] T010 Verificación en vivo end-to-end (logo, biblioteca de ejercicios, toggle con detalles).

## Evidence

- Suite completa: 203/203 verde.
- Verificación en vivo: logo subido y confirmado accesible (`200 image/png`) y visible en el perfil que ve el paciente; ítem de biblioteca de ejercicios creado/listado/eliminado; toggle de log con `details` confirmado idéntico en la lectura del paciente y del nutriólogo. Cuentas y datos de prueba limpiados al final.
