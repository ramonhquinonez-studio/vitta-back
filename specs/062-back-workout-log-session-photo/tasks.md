# Tasks: Session Photo on a Logged Workout Entry

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/workout_log.py`: `photo_url`/`photo_content_type` en `WorkoutExerciseLogIn`.
- [x] T003 `POST /me/workout-logs/photo` nuevo en `me/presentation/router.py`.
- [x] T004 `me_service.py`/`me/domain/repositories.py`/`mongo_me_repository.py`: paso de los nuevos campos y serialización.
- [x] T005 `mongo_patients_repository.py` (`list_workout_logs`): campos nuevos en la lectura del coach.
- [x] T006 Tests: `test_me_service.py` actualizado (fake repo + kwargs nuevos).

## Phase 3: Validation

- [x] T007 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 verde.
- [x] T008 Verificación en vivo end-to-end (upload → PUT → GET paciente → GET coach → fetch directo del archivo), con limpieza posterior.

## Evidence

- Suite completa: 225/225 verde.
- Verificación en vivo: cuentas demo sembradas (`app/scripts/seed_dev.py`), plan de rutina desechable creado/asignado, ronda completa `POST /me/workout-logs/photo` → `PUT /me/workout-logs/exercise` (con `photo_url`) → `GET /me/workout-logs` → `GET /patients/{id}/workout-logs` → fetch directo del archivo (`200 image/jpeg`). Limpieza: plan eliminado, documento `workout_logs` eliminado, archivo subido eliminado.
- Seguimiento (a pedido del usuario, no parte del alcance original de este slice): `seed_dev.py` ahora crea la cuenta demo del nutriólogo con `role="nutritionist"` en vez de `"pro"` (que no pasaba el gate `require_role`); la cuenta ya sembrada en la DB de dev también se corrigió directamente (upserts no actualizan registros existentes) y se verificó en vivo (`GET /patients` → `200`).
