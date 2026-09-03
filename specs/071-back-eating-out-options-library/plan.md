# Implementation Plan: Eating-Out Options Library

**Branch**: `071-back-eating-out-options-library` | **Date**: 2026-08-29 | **Spec**: `specs/071-back-eating-out-options-library/spec.md`

## Summary

A new, self-contained module in the modern clean-architecture shape, direct structural mirror of `recommendations`' pre-assignment/pre-platform files (entity, Protocol, Mongo repository, service, router) — no shared code, no changes to any existing module.

## Steps

1. `app/modules/eating_out_options/domain/entities.py`: `EatingOutOption` dataclass.
2. `domain/repositories.py`: `EatingOutOptionsRepository` Protocol (`list_for_owner`, `create_for_owner`, `update_for_owner`, `delete_for_owner`).
3. `infrastructure/mongo_eating_out_options_repository.py`: new `eating_out_options` Mongo collection, same CRUD shape as `mongo_recommendations_repository.py`'s pre-assignment methods.
4. `application/eating_out_options_service.py`: `_validate` requires both `restaurant` and `dish`.
5. `app/schemas/eating_out_options.py`: `EatingOutOptionOut`/`Create`/`Update`.
6. `presentation/router.py`: prefix `/eating-out-options`, `require_role("nutritionist")` on the whole router, standard 4 CRUD endpoints.
7. `app/routers/eating_out_options.py`: 1-line re-export wrapper, matching every migrated module.
8. `app/main.py`: import + `app.include_router(...)`.
9. Tests: `tests/test_eating_out_options_service.py`, fake repository mirroring `test_recommendations_service.py`'s shape.
10. Live verification: full CRUD round-trip via curl with a throwaway QA account, cleaned up.

## Constraints

- No platform tier, no assignment collection — deliberately simpler than `recommendations`, since neither an official data source nor per-patient targeting applies here.
