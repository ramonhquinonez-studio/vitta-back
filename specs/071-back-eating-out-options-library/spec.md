# Feature Specification: Eating-Out Options Library

**Feature Branch**: `071-back-eating-out-options-library`
**Created**: 2026-08-29
**Status**: Draft
**Type**: Feature

## Objective

User feedback, confirmed via `AskUserQuestion`: "there should be a comer fuera library, because it's not being saved anywhere" — verified true: every restaurant+dish entry a nutritionist adds to a meal's eating-out options was typed from scratch into a plain dialog every time, with zero persistence outside that specific plan. This adds a real, reusable library mirroring Recetario's CRUD shape, confirmed as "Yes, mirror Recetario exactly."

## In Scope

- New `app/modules/eating_out_options/` package (full modern clean-architecture shape): `EatingOutOption(id, owner_id, restaurant, dish, kcal, protein, carbs, fat)`, owner-scoped CRUD.
- `GET /eating-out-options`, `POST /eating-out-options`, `PATCH /eating-out-options/{id}`, `DELETE /eating-out-options/{id}` — all `require_role("nutritionist")`.
- `app/schemas/eating_out_options.py`: `EatingOutOptionOut`/`Create`/`Update`, `restaurant`/`dish` required on create, macro fields optional bounded floats.

## Out of Scope

- No platform tier — no official "recommended eating-out options" data source exists, unlike supplements/brands/articles/exercises.
- No per-patient assignment — this is a shared authoring convenience across all of a nutritionist's patients, same as recipes and equivalency foods, not a per-patient list.
- No change to how a plan's meal-embedded `EatingOutOption` (the existing `PlanMealItem`-adjacent shape on `PlanMeal.eating_out_options`) is stored or served — this is a separate, new collection a nutritionist picks from when authoring, not a replacement for the plan-embedded copy.

## Baseline Behavior

No `eating_out_options` collection or endpoints existed. Every eating-out entry lived only inside the specific plan/meal it was typed into.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro`'s `080-front-eating-out-options-library` (new library page + a picker sheet replacing the direct-to-dialog flow when adding an option to a meal).

## Acceptance Criteria

1. Given a nutritionist creates an eating-out option with restaurant/dish/macros, then it round-trips through `GET /eating-out-options` unchanged.
2. Given a nutritionist updates or deletes an option they own, then the change persists / the option disappears from the list.
3. Given a nutritionist tries to update or delete an option they don't own, then the request 404s (ownership-scoped, mirrors every other module's `*_for_owner` pattern).
4. Given `restaurant` or `dish` is missing on create, then the request is rejected with a 400.

## Validation

- Full backend unittest suite green (243/243 — 6 new tests in `tests/test_eating_out_options_service.py`: create validation ×2, create-then-list, update-then-delete, update/delete ownership rejection).
- Live CRUD round-trip verified against the running local server with a throwaway QA nutritionist account (create → list → update → delete → list-empty), cleaned up afterward.
