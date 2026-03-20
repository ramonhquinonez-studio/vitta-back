# Tasks: Back Plans Module Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Module Foundation

- [x] T002 Crear `domain`, `application`, `infrastructure` y `presentation` para `plans`.
- [x] T003 Mover CRUD, grocery list y assign al `PlansService`.
- [x] T004 Dejar `app/routers/plans.py` como wrapper delgado.
- [x] T005 Agregar test unitario del servicio.
- [x] T006 Actualizar docs y roadmap.

## Phase 3: Validation

- [x] T007 Ejecutar unittest y py_compile del slice.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest tests.test_plans_service`
- `python3 -m py_compile app/routers/plans.py app/modules/plans/domain/repositories.py app/modules/plans/application/plans_service.py app/modules/plans/infrastructure/mongo_plans_repository.py app/modules/plans/presentation/router.py`
