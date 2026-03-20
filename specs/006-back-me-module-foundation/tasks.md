# Tasks: Back Me Module Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Module Foundation

- [x] T002 Crear `domain`, `application`, `infrastructure` y `presentation` para `me`.
- [x] T003 Mover perfil, citas, mediciones y progreso al `MeService`.
- [x] T004 Dejar `app/routers/me.py` como wrapper delgado.
- [x] T005 Agregar test unitario del servicio.
- [x] T006 Actualizar docs y roadmap.

## Phase 3: Validation

- [x] T007 Ejecutar unittest y py_compile del slice.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest tests.test_me_service`
- `python3 -m py_compile app/routers/me.py app/modules/me/domain/repositories.py app/modules/me/application/me_service.py app/modules/me/infrastructure/mongo_me_repository.py app/modules/me/presentation/router.py`
