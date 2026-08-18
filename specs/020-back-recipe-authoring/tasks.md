# Tasks: Recipe Authoring

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `recipes/domain/repositories.py`: métodos de escritura en el protocolo.
- [x] T003 `mongo_recipes_repository.py`: CRUD de colecciones y recetas.
- [x] T004 `recipes_service.py`: orquestación + validación.
- [x] T005 `app/schemas/recipes.py`: schemas de entrada.
- [x] T006 `recipes/presentation/router.py`: 6 rutas nuevas.
- [x] T007 `tests/test_recipes_service.py`: 7 tests nuevos.

## Phase 3: Validation

- [x] T008 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 49/49 verde.
- [x] T009 Manual: ciclo completo `curl` (crear colección → agregar receta → actualizar receta → eliminar receta → eliminar colección) contra backend real, sin datos huérfanos.

## Evidence

- Suite completa de backend en verde (49 tests, antes 41... nota: 45→49, ver conteo real en el commit).
- `curl` ciclo completo: `POST /recipe_collections` → `201`; `POST .../recipes` → `201` con receta agregada; `PATCH .../recipes/{id}` → `200` solo `kcal` cambiado; `DELETE .../recipes/{id}` → `200` receta removida; `DELETE /recipe_collections/{id}` → `200` `{"ok": true}`.
