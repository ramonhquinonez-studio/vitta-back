# Tasks: USDA Nutrition Lookup

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `config.py`: `USDA_FDC_API_KEY` + `.env` local (no versionado).
- [x] T003 `domain/entities.py` + `domain/repositories.py`.
- [x] T004 `infrastructure/usda_fdc_repository.py`: llamada real a USDA FDC + reintento.
- [x] T005 `application/nutrition_lookup_service.py`.
- [x] T006 `schemas/nutrition_lookup.py` + `presentation/router.py`.
- [x] T007 `routers/nutrition_lookup.py` wrapper + wiring en `main.py`.
- [x] T008 Test nuevo: `tests/test_nutrition_lookup_service.py` (2 casos).

## Phase 3: Validation

- [x] T009 Suite completa → 126/126 verde.
- [x] T010 Verificación en vivo: `GET /nutrition/search` autenticado contra el backend real.

## Evidence

- Suite completa: 126/126 (2 nuevos, sin regresiones).
- Verificación en vivo: `curl` autenticado devolvió resultados reales de USDA FDC (ej. FDC 171077/171474 para "chicken breast raw"), mapeo de nutrientes 203/204/205/208 confirmado contra el JSON crudo antes de escribir el parser.
- Nota: se detectó que el endpoint de búsqueda de USDA devuelve ocasionalmente un 404 transitorio (gateway de api.data.gov) — mitigado con un reintento simple.
