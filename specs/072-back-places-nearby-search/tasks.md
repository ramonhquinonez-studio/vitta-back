# Tasks: Nearby Restaurant Search (Comer Fuera)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `domain/entities.py`: `NearbyPlace`.
- [x] T003 `domain/repositories.py`: Protocol.
- [x] T004 `infrastructure/overpass_places_repository.py`: query Overpass, parsear node/way, distancia Haversine, orden y límite.
- [x] T005 `application/places_lookup_service.py`: validación de coordenadas y radio.
- [x] T006 `app/schemas/places_lookup.py`.
- [x] T007 `presentation/router.py`: `GET /places/nearby`.
- [x] T008 `app/routers/places_lookup.py` + registro en `app/main.py`.
- [x] T009 `tests/test_places_lookup_service.py` (4 tests).

## Phase 3: Validation

- [x] T010 Suite de unittest completa → 247/247 verde.
- [x] T011 Verificación en vivo: 406 encontrado y corregido (User-Agent), luego round-trip completo confirmado contra coordenadas reales de CDMX.
- [x] T012 Limpieza de cuenta QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 247/247 verde.
- Curl en vivo contra `http://127.0.0.1:8000/places/nearby?lat=19.4326&lon=-99.1332&radius_m=800`: 7+ restaurantes reales devueltos, ordenados por distancia (Los Especiales 156m, Subway 201m, El Rey del Pavo 210m, Starbucks 216m, ...).
- Validación: `radius_m=50` → 422; `lat=200` → 400 `{"detail":"Invalid coordinates"}`.
