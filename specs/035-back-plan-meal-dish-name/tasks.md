# Tasks: Plan Meal `dish_name` Field

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/plan.py`: agregar `dish_name: Optional[str] = None` a `PlanMeal`.

## Phase 3: Validation

- [x] T003 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 124/124, sin regresiones.
- [x] T004 Round-trip manual con pydantic: meal nuevo con `dish_name`, doc legado sin la llave, doc con forma del seed script — los tres se comportan según lo esperado.

## Evidence

- Suite completa de nutri_back verde: 124/124 (sin cambio de conteo — este slice no agrega tests nuevos, es un campo opcional puramente aditivo).
- Round-trip manual confirmado:
  - `PlanCreate(...).model_dump()` con `dish_name` seteado → la llave aparece intacta en el dict listo para persistir.
  - `PlanOut.model_validate(doc)` sobre un doc legado sin `dish_name` → `meals[0].dish_name is None`, sin error.
  - `PlanOut.model_validate(doc)` sobre un doc con la forma del seed script (`dish_name` ya presente en Mongo) → se parsea correctamente por primera vez a través del schema real.
