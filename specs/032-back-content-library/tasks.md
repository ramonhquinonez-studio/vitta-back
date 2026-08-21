# Tasks: Nutrition Education Content Library

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `content_library/domain/`: entidades + repositorio protocol.
- [x] T003 `mongo_content_library_repository.py`: implementación (sort por `order`).
- [x] T004 `content_library_service.py`: pass-through de solo lectura.
- [x] T005 `app/schemas/content_library.py` + `presentation/router.py`.
- [x] T006 `app/routers/content_library.py` + registro en `main.py`.
- [x] T007 `app/scripts/seed_content_library.py`: 5 artículos transcritos verbatim del cliente Flutter.
- [x] T008 Test nuevo + guardrails de router actualizados.

## Phase 3: Validation

- [x] T009 Suite completa → 104/104 verde.
- [x] T010 Seed listo para ejecutarse (`python app/scripts/seed_content_library.py`) — idempotente por `_id` estable.

## Evidence

- Suite completa: 104/104, verde (103 previos + 1 nuevo en `test_content_library_service.py`).
- Endpoint registrado: `GET /content/articles`, confirmado en `test_module_router_smoke.py`.
