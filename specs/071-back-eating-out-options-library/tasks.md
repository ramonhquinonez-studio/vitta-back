# Tasks: Eating-Out Options Library

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/entities.py`: `EatingOutOption`.
- [x] T003 `domain/repositories.py`: Protocol de 4 métodos.
- [x] T004 `infrastructure/mongo_eating_out_options_repository.py`: colección `eating_out_options`.
- [x] T005 `application/eating_out_options_service.py`: validación + passthroughs.
- [x] T006 `app/schemas/eating_out_options.py`.
- [x] T007 `presentation/router.py`: 4 endpoints.
- [x] T008 `app/routers/eating_out_options.py` + registro en `app/main.py`.
- [x] T009 `tests/test_eating_out_options_service.py` (6 tests).

## Phase 3: Validation

- [x] T010 Suite de unittest completa → 243/243 verde.
- [x] T011 Round-trip CRUD en vivo contra el servidor local con cuenta QA desechable.
- [x] T012 Limpieza de datos QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 243/243 verde.
- Curl en vivo contra `http://127.0.0.1:8000` (`qa-nutri-eating@example.com`, eliminada después): create → 200 con todos los campos; list → 1 item; update kcal → reflejado; delete → `{"ok": true}`; list posterior → `[]`.
