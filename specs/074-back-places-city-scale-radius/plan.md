# Implementation Plan: City-Scale Search Radius for Nearby Places

**Branch**: `074-back-places-city-scale-radius` | **Date**: 2026-08-30 | **Spec**: `specs/074-back-places-city-scale-radius/spec.md`

## Summary

A two-line bound change, no new endpoint, no new module.

## Steps

1. `app/modules/places_lookup/application/places_lookup_service.py`: `search_nearby`'s validation, `100 <= radius_m <= 5000` → `100 <= radius_m <= 20000`.
2. `app/modules/places_lookup/presentation/router.py`: `radius_m: int = Query(1500, ge=100, le=5000)` → `le=20000`.
3. `tests/test_places_lookup_service.py`: `test_search_nearby_rejects_radius_out_of_bounds`'s out-of-bounds example bumped from `10000` (now valid) to `30000`.
4. Live verification: real Overpass query at the new city-scale radius.

## Constraints

- None beyond what's already noted in the spec (deliberate large-radius tradeoff vs. true city-boundary resolution).
