# Tasks: Brand Recommendations Linked to Menu Equivalency Groups

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/entities.py`: `equivalency_group_id` en `Recommendation`.
- [x] T003 `app/schemas/recommendations.py`: campo agregado a `RecommendationOut`/`Create`/`Update`.
- [x] T004 `infrastructure/mongo_recommendations_repository.py`: persistencia + lectura del campo.
- [x] T005 `presentation/router.py`: `_serialize()` incluye el campo.
- [x] T006 `app/modules/me/infrastructure/mongo_me_repository.py`: serializador de `list_recommendations` incluye el campo.
- [x] T007 `tests/test_recommendations_service.py`: fake repo actualizado + test nuevo.

## Phase 3: Validation

- [x] T008 Suite de unittest completa → 237/237 verde.
- [x] T009 Verificación en vivo end-to-end: plan con item de menú (`equivalency_group_id: "aceites_sin_proteina"`) → `GET /me/plan/active` lo devuelve; recomendación de marca con el mismo group id asignada al paciente → `GET /me/recommendations?kind=brand` la devuelve con el campo correcto.
- [x] T010 Limpieza de datos QA, 24 recomendaciones de plataforma conservadas.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 237/237 verde.
- Curl en vivo contra `http://127.0.0.1:8000`: cadena completa confirmada (plan → `/me/plan/active` → item con `equivalency_group_id`; recomendación → `/recommendations/{id}/assign` → `/me/recommendations?kind=brand` con el mismo `equivalency_group_id`).
