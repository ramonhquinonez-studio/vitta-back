# Tasks: Plan Days Passthrough + Real Weekly Plan Data

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `mongo_me_repository.py#get_active_plan`: incluir `days`.
- [x] T003 `app/scripts/seed_ramon_real_plan.py`: 25 recetas + 7 días reales transcritos del PDF.
- [x] T004 Ejecutar el script contra Mongo dev.

## Phase 3: Validation

- [x] T005 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 29/29 verde.
- [x] T006 Manual: `MongoMeRepository.get_active_plan` devuelve 7 días × 5 comidas; todos los items con receta resuelven vía `get_recipe_for_owner`; día 7 Comida/Cena sin items, con `notes`.

## Evidence

- `python -m app.scripts.seed_ramon_real_plan` → "Recipes seeded: 25", "Plan ... updated with 7 real days."
- Verificación directa: 0 comidas con items sin `recipe_id`; receta de muestra ("Sopitas con huevo") resuelta con ingredientes y pasos.
