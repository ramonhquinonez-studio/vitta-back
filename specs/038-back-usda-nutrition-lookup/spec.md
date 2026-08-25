# Feature Specification: USDA Nutrition Lookup

**Feature Branch**: `038-back-usda-nutrition-lookup`
**Created**: 2026-08-24
**Status**: Draft
**Type**: Feature

## Objective

`036-back-plan-item-macros` and `037-back-plan-item-cooking-state` let a nutritionist hand-type kcal/protein/carbs/fat and a raw↔cooked equivalent weight per plan item, but those numbers came from the nutritionist's own knowledge or estimation — nothing backed them with real data. The user asked explicitly for protein-source items (chicken, meat, fish) to be backed by real USDA data. This exposes USDA FoodData Central (FDC) — the U.S. government's public nutrient composition database — as a search the nutritionist-facing app can call, so the numbers a nutritionist enters can be sourced from real, cited measurements instead of memory.

## In Scope

- New `nutrition_lookup` module (`domain`/`application`/`infrastructure`/`presentation`, mirroring `content_library`'s shape) that searches USDA FDC's public `/foods/search` endpoint server-side, so the API key never reaches client apps.
- `GET /nutrition/search?query=<text>` (auth required, any authenticated user) returns up to 10 matches: `fdc_id`, `description`, and per-100g `kcal`/`protein`/`carbs`/`fat` (each nullable — not every USDA record reports all four).
- `USDA_FDC_API_KEY` added to `Settings` (`app/core/config.py`), read from `.env` (gitignored, never committed) — a free personal key from `fdc.nal.usda.gov/api-key-signup`, not `DEMO_KEY` (which rate-limits at 30 req/hour, too tight for interactive use).
- One retry on a transient 404 from the upstream search endpoint — observed repeatedly during manual testing to be a flaky api.data.gov gateway hiccup, not a real not-found.

## Out of Scope

- No caching/persistence of USDA search results — every search is a live upstream call. Traffic is low (nutritionist-initiated, one search per ingredient while authoring), so this isn't a real cost yet.
- No automatic conversion or unit handling server-side — results are always per-100g; scaling to an item's actual quantity/unit is the client's job (see `037-front-usda-nutrition-lookup` in `nutri_pro`).
- No raw↔cooked pairing logic server-side (e.g. "find this food's cooked counterpart automatically") — USDA doesn't link raw/cooked records to each other, and guessing the pairing heuristically risks silently wrong data reaching a patient's plan. The nutritionist searches for each state explicitly instead.
- No write-back to USDA, no other USDA endpoints (nutrient details by fdcId, branded foods, etc.) — only the one search operation this feature needs.

## Baseline Behavior

Nutritionists had no in-app way to check a real nutrient reference while filling in macros or a cooking-state equivalent weight — every number was typed from memory or estimation, with no way to verify it against anything.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `037-front-usda-nutrition-lookup` (the meal-item editor's "Buscar en USDA" UI). `nutri_app` is unaffected — it only displays whatever macros/cooking-state values already exist on a plan, regardless of how they were sourced.

## Acceptance Criteria

1. Given `GET /nutrition/search?query=chicken+breast+raw` with a valid auth token, when called, then it returns a list of matches with real USDA `fdc_id`s and per-100g nutrient values.
2. Given a blank/whitespace-only `query`, then the endpoint returns `400`.
3. Given the upstream USDA request fails after retrying once, then the endpoint returns `502` rather than crashing.
4. Given a USDA record that doesn't report one of the four nutrients (observed in practice for some `Foundation`-type records missing `kcal`), then that field comes back `null` rather than the whole match being dropped.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 126/126 green (2 new tests in `tests/test_nutrition_lookup_service.py`, no regressions).
- Live verification against the running backend: authenticated `GET /nutrition/search?query=chicken+breast+raw` returns real matches (confirmed FDC ids 171077/171477/etc. — the same records manually cited while backfilling `036`/`037`'s real macro/cooking-state data on the assigned patient plan).
- Confirmed the nutrient-number mapping (`203`=protein, `204`=fat, `205`=carbs, `208`=kcal) directly against raw USDA JSON before writing the parser, rather than guessing field names.
