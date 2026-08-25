# Implementation Plan: USDA Nutrition Lookup

**Branch**: `038-back-usda-nutrition-lookup` | **Date**: 2026-08-24 | **Spec**: `specs/038-back-usda-nutrition-lookup/spec.md`

## Summary

A thin, auth-gated proxy in front of USDA FoodData Central's public search endpoint, following the same `domain/application/infrastructure/presentation` shape as every other migrated module.

## Steps

1. `app/core/config.py`: `USDA_FDC_API_KEY: str = ""` setting; local `.env` gets the real key (gitignored).
2. `app/modules/nutrition_lookup/domain/entities.py`: `NutritionMatch` dataclass.
3. `app/modules/nutrition_lookup/domain/repositories.py`: `NutritionLookupRepository` Protocol with `search(query, limit) -> list[NutritionMatch]`.
4. `app/modules/nutrition_lookup/infrastructure/usda_fdc_repository.py`: `UsdaFdcRepository` — calls `https://api.nal.usda.gov/fdc/v1/foods/search` via `requests` (matching the existing synchronous-`requests`-inside-`async def` precedent in `app/routers/google_oauth.py` rather than introducing a new async HTTP dependency), retries once on non-200, maps nutrient numbers 203/204/205/208 to protein/fat/carbs/kcal.
5. `app/modules/nutrition_lookup/application/nutrition_lookup_service.py`: `NutritionLookupService.search()` — validates non-blank query, delegates.
6. `app/schemas/nutrition_lookup.py`: `NutritionMatchOut`.
7. `app/modules/nutrition_lookup/presentation/router.py`: `GET /nutrition/search`, auth via `get_current_user`, `400` on `ValueError`, `502` on `RuntimeError` (upstream failure).
8. `app/routers/nutrition_lookup.py`: thin re-export wrapper, matching every migrated module.
9. `app/main.py`: wire the router in.
10. `tests/test_nutrition_lookup_service.py`: fake repository, mirrors `tests/test_content_library_service.py`'s shape.

## Constraints

- The API key is never returned to a client — only the server calls USDA directly.
- No new HTTP client dependency (`requests` already ships in this repo and is already used for a similar outbound call) — avoids adding `httpx`/`aiohttp` for one endpoint.
