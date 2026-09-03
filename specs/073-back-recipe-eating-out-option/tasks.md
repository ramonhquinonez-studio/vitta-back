# Tasks: Recipe-Level Eating-Out Alternative

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/recipes.py`: `RecipeEatingOutOption` + campo en `RecipeOut`/`RecipeIn`/`RecipeUpdate`.
- [x] T003 `domain/entities.py`: `Recipe.eating_out_option`.
- [x] T004 `mongo_recipes_repository.py`: persistencia en `add_recipe`/`_recipe_from_dict` (update genérico ya lo soporta).
- [x] T005 `presentation/router.py`: `_serialize_recipe` incluye el campo.
- [x] T006 Confirmado (sin cambio de código): `me`'s `_serialize_recipes` ya pasa el campo por ser una copia genérica del documento.

## Phase 3: Validation

- [x] T007 Suite de unittest completa → 247/247 verde (sin tests nuevos — capa de servicio ya genérica).
- [x] T008 Verificación en vivo: agregar receta con `eating_out_option`, confirmar en `GET`; actualizar parcialmente, confirmar reemplazo completo.
- [x] T009 Limpieza de cuenta QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 247/247 verde.
- Curl en vivo contra `http://127.0.0.1:8000/recipe_collections/{id}/recipes`: creación con `eating_out_option` completo confirmada; `PATCH` con `{"restaurant","dish","kcal"}` confirma reemplazo completo (protein/carbs/fat en null).
