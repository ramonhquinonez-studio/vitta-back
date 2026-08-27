# Tasks: Filtered Platform Articles Endpoint (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/repositories.py`: `list_platform_articles` en el `Protocol`.
- [x] T003 `mongo_content_library_repository.py`: `list_platform_articles`.
- [x] T004 `content_library_service.py`: passthrough.
- [x] T005 `presentation/router.py`: `GET /content/articles/platform`.
- [x] T006 `tests/test_content_library_service.py`: test nuevo.

## Phase 3: Validation

- [x] T007 Suite de unittest completa → 225/225 verde.
- [x] T008 Verificación en vivo por curl: `GET /content/articles/platform` (110 reales), `GET /content/articles/mine` (vacío para cuenta nueva), copia vía `POST /content/articles` existente confirmada.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 225/225 verde.
- Curl en vivo contra `http://127.0.0.1:8000`: los tres criterios de aceptación confirmados. Cuenta de nutriólogo de prueba y su artículo copiado eliminados.
