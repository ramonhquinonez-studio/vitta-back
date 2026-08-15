# Tasks: Back Me Profile Update

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `MeRepository`/`MongoMeRepository`: `update_patient_profile`.
- [x] T003 `MeService.update_profile` + `PATCH /me/profile`.
- [x] T004 Tests: éxito, payload vacío, sin patient ligado.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 27/27 verde.
