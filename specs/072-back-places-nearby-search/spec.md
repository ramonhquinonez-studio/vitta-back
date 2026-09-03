# Feature Specification: Nearby Restaurant Search (Comer Fuera)

**Feature Branch**: `072-back-places-nearby-search`
**Created**: 2026-08-30
**Status**: Draft
**Type**: Feature

## Objective

Direct user request: "is there an API to get some places to comer fuera... I would like to view the places based in my location." Confirmed via `AskUserQuestion`: OpenStreetMap's Overpass API (free, keyless, no billing setup, vs. Google Places which needs a paid Google Cloud project) as the data source, searched around the nutritionist's own device location at add-time.

## In Scope

- New `app/modules/places_lookup/` module — a live per-request proxy (no local storage, no sync script), direct structural mirror of the existing `nutrition_lookup` module.
- `GET /places/nearby?lat=&lon=&radius_m=` (default 1500m, 100–5000m bounds), `require_role("nutritionist")`.
- Queries OSM `amenity` in `{restaurant, fast_food, cafe}` within the radius (both `node` and `way` geometries), drops unnamed entries, computes real Haversine distance from the query point, sorts nearest-first, caps at 20 results.

## Out of Scope

- No caching/storage of search results — always a live query.
- No support for a non-"nutritionist" role — this is an authoring-time convenience in `nutri_pro`, not a patient-facing feature.

## Baseline Behavior

No places/restaurant-search capability existed anywhere in the backend.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro`'s `081-front-places-nearby-search` (a "Buscar cerca de mí" button inside the eating-out-option dialog, using the device's own location).

## Acceptance Criteria

1. Given valid lat/lon, then real, named nearby restaurants/fast-food/cafés come back, sorted by distance, each with a real address/cuisine when OSM has one.
2. Given out-of-range coordinates or a radius outside 100–5000m, then the request is rejected with a 400/422.
3. Given the upstream Overpass request fails, then the endpoint returns a 502, not a raw crash.

## Validation

- Full backend unittest suite green (247/247 — 4 new tests in `tests/test_places_lookup_service.py`: delegation, invalid latitude, invalid longitude, radius-out-of-bounds).
- Live verification against the running local server with a throwaway QA nutritionist account: `GET /places/nearby?lat=19.4326&lon=-99.1332&radius_m=800` returned real, correctly-distance-sorted Mexico City restaurants (Los Especiales, Subway, El Rey del Pavo, Starbucks, El Cardenal, Pizza Hut, ...); radius-out-of-bounds returned 422; invalid latitude returned 400. QA account cleaned up afterward.
- **Live-verified vendor quirk**: the Overpass API's Apache front-end returns a bare 406 (no error body) for the default `python-requests` User-Agent — confirmed by reproducing it directly, then fixing it by sending a descriptive `User-Agent` header (also matches Overpass's own stated usage policy, which asks for one).
