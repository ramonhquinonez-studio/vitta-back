# Tasks: Recommendations (Supplements/Brands)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `recommendations/domain/`: entidad y protocolo de repositorio.
- [x] T003 `recommendations/application/recommendations_service.py`.
- [x] T004 `recommendations/infrastructure/mongo_recommendations_repository.py`.
- [x] T005 `app/schemas/recommendations.py`.
- [x] T006 `recommendations/presentation/router.py` + wrapper + registro en `main.py`.
- [x] T007 `me` module: `list_recommendations` en repositorio/servicio/router (`GET /me/recommendations`).
- [x] T008 Índice en `init_indexes.py`.
- [x] T009 `tests/test_recommendations_service.py` (5 tests) + 2 tests nuevos en `test_me_service.py` + guardrails/smoke actualizados.

## Phase 3: Validation

- [x] T010 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 61/61 verde.
- [x] T011 Manual: ciclo `curl` completo (crear suplemento + marca, listar filtrado por `kind`, leer como paciente vinculado, eliminar ambos).

## Evidence

- Suite completa de backend en verde (61 tests, antes 54).
- `curl POST /recommendations` (suplemento y marca) → `201` cada uno.
- `curl GET /me/recommendations?kind=supplement` (paciente vinculado) → mismo suplemento creado por el nutriólogo.
- `curl DELETE /recommendations/{id}` × 2 → `{"ok": true}`, sin datos huérfanos.
