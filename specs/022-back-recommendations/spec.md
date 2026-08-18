# Feature Specification: Recommendations (Supplements/Brands)

**Feature Branch**: `022-back-recommendations`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Feature

## Objective

Let the nutritionist author their own supplement and recommended-brand recommendations, and let their patients read them. Before this slice, `nutri_app`'s "Suplementos y vitaminas" and "Marcas recomendadas" pages showed identical hardcoded lists for every nutritionist and every patient, with no backend at all.

## In Scope

- New `recommendations` collection: `owner_id`, `kind` (`"supplement"` | `"brand"`), `title`, `subtitle`, `category`, `brand`, `description`, `benefits` (list), `usage`, `notes`, `price`, `rating`, `emoji`.
- `GET/POST /recommendations` (list own, filterable by `?kind=`; create) and `PATCH/DELETE /recommendations/{id}` — full owner-scoped CRUD, new `recommendations` module (mirrors `recipes`' structure).
- `GET /me/recommendations?kind=` — patient-facing read (added to the `me` module), resolved through the patient's `owner_id`, same pattern as `list_recipe_collections`/`list_education_videos`.

## Out of Scope

- A unified schema forcing supplements and brands to look identical in the UI — the shared schema is a superset (supplements mostly use `subtitle`/`category`/`usage`/`notes`; brands mostly use `brand`/`price`/`rating`/`description`), each client renders only the fields relevant to that `kind`.
- Per-patient customization — recommendations are owner-scoped (shown to all of that nutritionist's patients equally), not assigned per individual patient, matching the same scoping already used for the recipe library and nutritionist profile.

## Baseline Behavior

- `nutri_app`'s `supplements_page.dart`/`recommended_brands_page.dart` were fully hardcoded, identical for every user, with zero backend concept.

## Target Design

- `POST /recommendations {"kind": "supplement", "title": "Omega 3", ...}` → `201`.
- `GET /recommendations?kind=supplement` (nutritionist) → their own supplements.
- `GET /me/recommendations?kind=supplement` (their patient) → the same list.
- `PATCH`/`DELETE /recommendations/{id}` for a recommendation not owned by the caller → `404`.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given the nutritionist creates a supplement and a brand recommendation, when they list with `?kind=supplement`, then only the supplement appears.
2. Given a linked patient reads `GET /me/recommendations?kind=brand`, then they see the same brand recommendation their nutritionist created.
3. Given a recommendation update/delete against an id not owned by the caller, then `404`.
4. Given `kind` is missing or invalid on create, then `400`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 61/61 green (5 new tests in `test_recommendations_service.py`, 2 new in `test_me_service.py`).
- Manual: full `curl` cycle — create a supplement and a brand as the nutritionist, list both, read `GET /me/recommendations?kind=supplement` as the linked patient (same data), delete both. Test data cleanly removed afterward.
