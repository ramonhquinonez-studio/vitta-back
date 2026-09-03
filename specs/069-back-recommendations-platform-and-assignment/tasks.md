# Tasks: Real Supplements/Brands Library + Per-Patient Assignment (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/entities.py`: `Recommendation.owner_id` → `str | None`.
- [x] T003 `domain/repositories.py`: nuevos métodos del Protocol (`list_platform_recommendations`, `assign_to_patients`, `unassign_from_patient`, `list_assigned_patient_ids`).
- [x] T004 `infrastructure/mongo_recommendations_repository.py`: implementación de los 4 métodos nuevos + colección `recommendation_assignments` + `_to_entity` null-safe para `owner_id`.
- [x] T005 `application/recommendations_service.py`: passthroughs + validación de `patient_ids` no vacío.
- [x] T006 `presentation/router.py`: `GET /recommendations/platform`, `POST /recommendations/{id}/assign`, `DELETE /recommendations/{id}/assign/{patient_id}`, `GET /recommendations/{id}/assignments`; `owner_id` agregado a `RecommendationOut`/`_serialize`.
- [x] T007 `app/modules/me/`: `MeRepository.list_recommendations` gana `patient_id`; `MeService.list_recommendations` lo pasa; `MongoMeRepository.list_recommendations` reescrito para unir con `recommendation_assignments`.
- [x] T008 Nuevo `app/scripts/sync_recommendations_library.py` (14 suplementos vía MedlinePlus, 10 marcas vía DSLD).
- [x] T009 `tests/test_recommendations_service.py` extendido (5 tests nuevos: plataforma, assign→list→unassign, assign vacío, assign no-owned, unassign inexistente).
- [x] T010 `tests/test_me_service.py` extendido (firma nueva de `list_recommendations` en el fake repo + test de threading del `patient_id`).

## Phase 3: Validation

- [x] T011 Suite de unittest completa → 236/236 verde.
- [x] T012 Ejecución en vivo del script de sync: 21/24 en el primer intento; 2 fallos de diagnóstico en vivo (`sync_recommendations_library.py` reparado): "NOW Foods" reemplazado por "Jarrow Formulas" (DSLD trata "NOW" como token no buscable), apóstrofe de "Nature's Bounty" removido solo en la query saliente (el chequeo de coincidencia exacta sigue exigiendo el `brandName` real con apóstrofe). "Multivitamínico" reapuntado de `multivitaminas` (0 resultados) a `vitaminas y minerales` (resultado real con contenido). Re-ejecución: 24/24.
- [x] T013 Verificación end-to-end en vivo contra el servidor local con cuentas QA desechables: lista de plataforma → copiar a "mías" → asignar → `GET /me/recommendations` del paciente asignado la incluye (y no antes de asignar) → `GET /recommendations/{id}/assignments` confirma el id del paciente → desasignar → `GET /me/recommendations` vacío de nuevo.
- [x] T014 Limpieza de datos QA (usuarios, paciente, invite code, recomendación copiada, assignment) conservando las 24 recomendaciones de plataforma reales sincronizadas.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 236/236 verde.
- `python -m app.scripts.sync_recommendations_library`: "Synced 21 platform recommendations..." → tras las 2 correcciones → "Synced 24 platform recommendations (supplements + brands)."
- Curl en vivo contra `http://127.0.0.1:8000` con cuentas QA (`qa-nutri-069b@example.com`, paciente vía invite code): los 6 criterios de aceptación del spec confirmados paso a paso (platform list, copy, assign, assignments list, me/recommendations gated, unassign). Cuentas QA y datos derivados eliminados; 24 recomendaciones de plataforma conservadas (`db.recommendations.count_documents({"owner_id": None})` → 24).
