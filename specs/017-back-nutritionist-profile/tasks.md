# Tasks: Nutritionist Profile

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `nutritionist_profile/domain/`: entidades y protocolo de repositorio.
- [x] T003 `nutritionist_profile/application/nutritionist_profile_service.py`.
- [x] T004 `nutritionist_profile/infrastructure/mongo_nutritionist_profile_repository.py`.
- [x] T005 `app/schemas/nutritionist_profile.py`.
- [x] T006 `nutritionist_profile/presentation/router.py` + wrapper + registro en `main.py`.
- [x] T007 Índice único `nutritionist_profiles.owner_id` en `init_indexes.py`.
- [x] T008 `me` module: `get_nutritionist_profile` en repositorio/servicio/router.
- [x] T009 `tests/test_nutritionist_profile_service.py` (4 tests) + 2 tests nuevos en `test_me_service.py` + guardrails/smoke actualizados.

## Phase 3: Validation

- [x] T010 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 39/39 verde.
- [x] T011 Manual `curl PATCH /nutritionist_profile/me` (nutriólogo) → `curl GET /me/nutritionist_profile` (paciente vinculado) → mismos valores.

## Evidence

- Suite completa de backend en verde (39 tests, antes 33).
- `curl PATCH /nutritionist_profile/me -d '{"role_label":"Nutrióloga clínica",...}'` → `200`, valores guardados.
- `curl GET /me/nutritionist_profile` (paciente vinculado a ese nutriólogo) → mismos valores, `patient_count` real.
