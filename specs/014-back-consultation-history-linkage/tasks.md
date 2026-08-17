# Tasks: Consultation History Linkage

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `appointments/domain/entities.py`: agregar `body_composition_id`.
- [x] T003 `appointments/domain/repositories.py`: agregar `body_composition_id` al Protocol.
- [x] T004 `appointments/infrastructure/mongo_appointments_repository.py`: create/update/serialize.
- [x] T005 `appointments/application/appointments_service.py`: create/update.
- [x] T006 `appointments/presentation/router.py`: schemas + `_serialize` + handlers.
- [x] T007 `tests/test_appointments_service.py`: fake repo + call sites.
- [x] T008 `me/domain/repositories.py`: `get_plan_summary` + `get_body_composition_by_id`.
- [x] T009 `me/infrastructure/mongo_me_repository.py`: implementar los dos metodos + `_serialize_appointment`.
- [x] T010 `me/application/me_service.py`: `list_consultations`.
- [x] T011 `me/presentation/router.py`: `GET /consultations`.
- [x] T012 `tests/test_me_service.py`: fake repo + 2 tests de `list_consultations`.
- [x] T013 `app/scripts/seed_ramon_consultation_history.py`: 4 consultas reales + ejecutar contra Mongo dev.

## Phase 3: Validation

- [x] T014 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 31/31 verde.
- [x] T015 Manual: `MeService.list_consultations` contra Mongo dev → 4 consultas, mas reciente primero, plan/body_composition resueltos.
- [x] T016 Manual: `GET /me/consultations` responde 401 sin auth (ruta registrada en OpenAPI).

## Evidence

- `unittest discover` → Ran 31 tests, OK.
- Script: "Seeded 4 consultations (appointments + linked body_compositions) for Ramon."
- Verificacion directa: 3/4 consultas con `plan` resuelto ("Plan Semanal Demo"), 4/4 con `body_composition` resuelto (peso 75.0 → 68.0 kg a lo largo de las 4 consultas).
