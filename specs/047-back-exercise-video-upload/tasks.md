# Tasks: Exercise Video Upload

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/core/storage.py`: `max_size_bytes` guard + mapeos de extensión de video.
- [x] T003 `workout_plans/presentation/router.py`: `POST /exercise-videos`.
- [x] T004 Tests: `test_storage.py` (3 casos).

## Phase 3: Validation

- [x] T005 Suite completa → 206/206 verde.
- [x] T006 Verificación en vivo (subida real, rechazo de no-video, rechazo de token de paciente).

## Evidence

- Suite completa: 206/206 verde.
- Verificación en vivo: video subido y confirmado accesible (`200 video/mp4`); archivo no-video rechazado (`400`); token de paciente rechazado (`403`). Cuentas y archivo de prueba limpiados al final.
