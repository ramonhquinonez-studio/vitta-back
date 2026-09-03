# Tasks: City-Scale Search Radius for Nearby Places

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `places_lookup_service.py`: límite de `radius_m` ampliado a 20,000.
- [x] T003 `presentation/router.py`: `Query(..., le=20000)`.
- [x] T004 `tests/test_places_lookup_service.py`: ejemplo fuera de rango actualizado a 30,000.

## Phase 3: Validation

- [x] T005 Suite de unittest completa → 247/247 verde.
- [x] T006 Verificación en vivo: consulta real a Overpass con `radius_m=12000` completada en ~4.5s, resultados correctamente limitados.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 247/247 verde.
- Curl en vivo (Overpass directo) con `around:12000` en coordenadas de CDMX: 60 elementos (tope `limit*3`), ~4.5s de latencia.
