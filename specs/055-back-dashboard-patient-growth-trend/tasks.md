# Tasks: Practice Dashboard Patient Growth Trend

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `mongo_patients_repository.py`: helper `_add_months` + cómputo de `new_patients_by_month` en `get_dashboard`.

## Phase 3: Validation

- [x] T003 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 218/218 verde.
- [x] T004 Verificación en vivo por curl: 6 entradas cronológicas, mes actual coincide con `new_patients_this_month`. Limpieza de datos QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 218/218 verde, sin regresiones.
- curl en vivo: 2 pacientes creados → `new_patients_by_month` con 6 entradas cronológicas (2026-03…2026-08), última entrada `{"month": "2026-08", "count": 2}` coincidiendo con `new_patients_this_month: 2`. Datos de prueba limpiados con script directo de Motor.
