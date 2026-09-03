# Implementation Plan: Nearby Restaurant Search (Comer Fuera)

**Branch**: `072-back-places-nearby-search` | **Date**: 2026-08-30 | **Spec**: `specs/072-back-places-nearby-search/spec.md`

## Summary

A new, self-contained module mirroring `nutrition_lookup`'s exact live-proxy shape (Protocol/service/router, `requests`-based external HTTP call, no local storage) — no changes to any existing module.

## Steps

1. `app/modules/places_lookup/domain/entities.py`: `NearbyPlace(name, address, cuisine, lat, lon, distance_m)`.
2. `domain/repositories.py`: `PlacesRepository` Protocol, `search_nearby(lat, lon, *, radius_m=1500, limit=20)`.
3. `infrastructure/overpass_places_repository.py`: builds an Overpass QL query (`node`/`way` with `["amenity"~"^(restaurant|fast_food|cafe)$"]`, `around:radius_m,lat,lon`, `out center <limit*3>`), POSTs via `requests` with an explicit `User-Agent` header (required — see spec's vendor-quirk note), parses both `node` (top-level `lat`/`lon`) and `way`/`center` shapes, skips unnamed entries, builds `address` from `addr:street`/`addr:housenumber`, computes Haversine distance, sorts and truncates.
4. `application/places_lookup_service.py`: validates lat/lon ranges and a 100–5000m radius bound.
5. `app/schemas/places_lookup.py`: `NearbyPlaceOut`.
6. `presentation/router.py`: `GET /places/nearby`, `require_role("nutritionist")`.
7. `app/routers/places_lookup.py` wrapper + `app/main.py` registration.
8. Tests: `tests/test_places_lookup_service.py`, fake repository, service-layer validation tests (mirrors `nutrition_lookup`'s own lack of a dedicated HTTP-parsing unit test — that logic is verified live instead, same precedent as `usda_fdc_repository.py`).
9. Live verification: real curl round-trip against Mexico City coordinates.

## Constraints

- Overpass's Apache front-end 406s the default `python-requests` User-Agent — discovered live while implementing, fixed with an explicit `User-Agent` header on every request.
- `fast_food`/`cafe` included alongside `restaurant` because common Mexican eating-out spots (taquerías, loncherías) are frequently tagged `fast_food` in OSM, not `restaurant` — confirmed by sampling live results.
