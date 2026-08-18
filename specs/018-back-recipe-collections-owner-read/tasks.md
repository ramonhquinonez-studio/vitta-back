# Tasks: Recipe Collections — Owner Read

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `recipes/domain/`: entidades y protocolo de repositorio.
- [x] T003 `recipes/application/recipes_service.py`.
- [x] T004 `recipes/infrastructure/mongo_recipes_repository.py`.
- [x] T005 `app/schemas/recipes.py`.
- [x] T006 `recipes/presentation/router.py` + wrapper + registro en `main.py`.
- [x] T007 `tests/test_recipes_service.py` (2 tests) + guardrails/smoke actualizados.

## Phase 3: Validation

- [x] T008 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 41/41 verde.
- [x] T009 Manual `curl GET /recipe_collections` (nutriólogo demo) → recetas reales sembradas.

## Evidence

- Suite completa de backend en verde (41 tests, antes 39).
- `curl GET /recipe_collections` → `200`, colecciones reales con recetas anidadas (ej. "Sopitas con huevo", "Avocado toast", "Omelette").
