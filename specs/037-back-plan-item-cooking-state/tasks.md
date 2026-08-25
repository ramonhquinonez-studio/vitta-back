# Tasks: Plan Meal Item Cooking State

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/plan.py`: `cooking_state`/`equivalent_qty` en `PlanMealItem`.

## Phase 3: Validation

- [x] T003 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 124/124.
- [x] T004 Round-trip en vivo vía curl.
- [x] T005 Backfill del plan real asignado (pollo/salmón), verificado vía `PlanOut.model_validate()`.

## Evidence

- Suite completa de nutri_back verde: 124/124.
- Curl round-trip confirmado.
- Plan real backfillado y verificado.
