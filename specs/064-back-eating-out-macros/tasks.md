# Tasks: Carbs/Fat on Eating-Out Options and Diary Entries

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/plan.py`: `carbs`/`fat` en `EatingOutOption`.
- [x] T003 `me/infrastructure/mongo_me_repository.py`: `carbs`/`fat` en `create_food_diary_entry`/`_serialize_food_diary_entry`.
- [x] T004 `patients/infrastructure/mongo_patients_repository.py`: `carbs`/`fat` en `list_food_diary_entries`.

## Phase 3: Validation

- [x] T005 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 verde.
- [x] T006 Verificación en vivo (plan desechable + entrada de diario desechable), con limpieza posterior.

## Evidence

- Suite completa: 225/225 verde.
- Verificación en vivo: plan con `eating_out_options[0].carbs=40, fat=8` confirmado en la respuesta de creación; entrada de diario con `carbs=40, fat=8` confirmada vía `GET /me/food_diary_entries`. Plan y entrada de diario eliminados tras la verificación.
