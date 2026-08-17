# Tasks: Overlap-Conflict 409 Returns 500

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `conflict_detail()`: serializar `conflict_start`/`conflict_end` a ISO 8601.
- [x] T003 `tests/test_appointments_service.py`: test de regresión `test_conflict_detail_is_json_serializable`.

## Phase 3: Validation

- [x] T004 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 33/33 verde.
- [x] T005 Manual: reproducido el 500 en vivo, aplicado el fix, mismo request contra servidor dev real → 409 limpio.

## Evidence

- Antes del fix: `curl -X PATCH .../appointments/{id}` con horario ocupado → `HTTP_STATUS:500`, `"Internal Server Error"`.
- Después del fix: mismo request → `HTTP_STATUS:409`, `{"detail":{"code":"OVERLAP","message":"Ya existe una cita en ese horario.","conflict_id":"...","conflict_start":"2026-08-16T17:53:18.214000","conflict_end":"2026-08-16T18:38:18.214000"}}`.
- `unittest discover` → Ran 33 tests, OK.
