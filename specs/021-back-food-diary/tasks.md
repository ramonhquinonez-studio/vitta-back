# Tasks: Food Diary Persistence

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `me/domain/repositories.py`: métodos nuevos.
- [x] T003 `mongo_me_repository.py`: `list_food_diary_entries`/`create_food_diary_entry`.
- [x] T004 `me_service.py`: orquestación + validación.
- [x] T005 `me/presentation/router.py`: `GET`/`POST /me/food_diary_entries`.
- [x] T006 `patients/` (domain/infrastructure/application/presentation): `list_food_diary_entries`, espejo de `list_body_compositions`.
- [x] T007 Índice en `init_indexes.py`.
- [x] T008 `tests/test_me_service.py` (4 tests) + `tests/test_patients_service.py` (2 tests).

## Phase 3: Validation

- [x] T009 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 54/54 verde.
- [x] T010 Manual: `curl POST /me/food_diary_entries` (paciente) → `201`; `curl GET /me/food_diary_entries` (mismo paciente) → aparece; `curl GET /patients/{id}/food_diary_entries` (nutriólogo dueño) → misma entrada.

## Evidence

- Suite completa de backend en verde (54 tests, antes 49).
- `curl POST /me/food_diary_entries -d '{"dish":"Tacos al pastor","meal_title":"Comida","restaurant":"...","kcal":450,"protein":22}'` → `201`.
- `curl GET /patients/{id}/food_diary_entries` (nutriólogo demo) → la misma entrada real del paciente demo.
