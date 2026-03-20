# Tasks: Back Auth Module Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Module Foundation

- [x] T002 Crear `domain`, `application`, `infrastructure` y `presentation` para `auth`.
- [x] T003 Mover registro/login/refresh al `AuthService`.
- [x] T004 Dejar `app/routers/auth.py` como wrapper delgado.
- [x] T005 Agregar test unitario de `AuthService`.
- [x] T006 Actualizar docs y roadmap.

## Phase 3: Validation

- [x] T007 Ejecutar unittest y py_compile del slice.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest tests.test_auth_service`
- `python3 -m py_compile app/routers/auth.py app/modules/auth/domain/entities.py app/modules/auth/domain/repositories.py app/modules/auth/application/auth_service.py app/modules/auth/infrastructure/mongo_auth_repository.py app/modules/auth/presentation/router.py`
