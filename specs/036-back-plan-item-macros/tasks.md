# Tasks: Plan Meal Item Macros

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/plan.py`: agregar `kcal`/`protein`/`carbs`/`fat` a `PlanMealItem`.

## Phase 3: Validation

- [x] T003 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 124/124, sin regresiones.
- [x] T004 Round-trip en vivo vía curl (`POST /plans` → `GET` → `DELETE`).
- [x] T005 Backfill de macros reales en el plan ya asignado a la cuenta real, verificado vía `PlanOut.model_validate()`.

## Evidence

- Suite completa de nutri_back verde: 124/124 (campo puramente aditivo, sin tests nuevos — mismo patrón que `035`).
- Curl round-trip confirmado: item con `kcal`/`protein`/`carbs`/`fat` se crea y se lee sin cambios.
- Plan real ("Plan de ganancia muscular") backfillado con macros estimados por ingrediente y verificado vía `PlanOut.model_validate()`.
