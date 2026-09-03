# Feature Specification: City-Scale Search Radius for Nearby Places

**Feature Branch**: `074-back-places-city-scale-radius`
**Created**: 2026-08-30
**Status**: Draft
**Type**: Enhancement

## Objective

Direct user request: an inline restaurant-suggestion dropdown "based on the current city," not just the immediate few blocks. Confirmed via `AskUserQuestion`: a large-radius-from-location approach (reusing `072-back-places-nearby-search`'s existing endpoint with a bigger radius bound) rather than true city-boundary resolution (reverse geocoding + area-based Overpass queries) — much less to build, and the distinction rarely matters for restaurant search.

## In Scope

- `GET /places/nearby`'s `radius_m` upper bound raised from 5,000 to 20,000 (both the FastAPI `Query` validator and `PlacesLookupService`'s own validation).

## Out of Scope

- No true city-boundary resolution (reverse geocoding, Overpass area queries) — a deliberate simpler tradeoff, confirmed with the user.
- No change to the result cap (still ~20, via `limit*3` raw Overpass fetch) — verified live that Overpass's own `around:` spatial filter handles a 12km-radius query efficiently regardless of how many matches exist in the area, so a larger radius doesn't meaningfully change response time or payload size.

## Baseline Behavior

`radius_m` was capped at 5,000m (a "few blocks to a small neighborhood" scale) — too small for `nutri_pro`'s new "restaurants in the current city" autocomplete request.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro`'s `083-front-restaurant-autocomplete-dropdown`, which now defaults its `SearchNearbyPlaces` usecase call to a 12km radius.

## Acceptance Criteria

1. Given `radius_m=12000`, then the request succeeds (previously rejected above 5,000).
2. Given `radius_m=25000` (above the new 20,000 bound), then the request is still rejected with a 400/422.

## Validation

- Full backend unittest suite green (247/247 — 1 existing test updated: `test_search_nearby_rejects_radius_out_of_bounds` now uses `radius_m=30000` as its out-of-bounds example, since 10,000 — the prior example — is valid under the new bound).
- Live verification: a real Overpass query at `radius_m=12000` around Mexico City center completed in ~4.5s and returned real, correctly-capped results (hit the `limit*3`=60 raw-element cap, confirming plenty of restaurants exist at that radius in a dense city).
