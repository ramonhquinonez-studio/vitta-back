# Tasks: Back Test Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Test Foundation

- [x] T002 Agregar guardrail para wrappers legacy en `app/routers/`.
- [x] T003 Agregar smoke tests para routers modulares.
- [x] T004 Actualizar docs y roadmap.

## Phase 3: Validation

- [x] T005 Ejecutar `unittest discover`.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`
