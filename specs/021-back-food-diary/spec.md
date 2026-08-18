# Feature Specification: Food Diary Persistence

**Feature Branch**: `021-back-food-diary`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Feature

## Objective

Give patients real, persisted food-diary entries (what `nutri_app` calls "eating out" logging) and let the owning nutritionist read them back. Before this slice, `nutri_app`'s eating-out log lived entirely in an in-memory `RxList` on `MyDayController` — not even local disk storage, let alone a backend — lost on every app restart, and completely invisible to the nutritionist.

## In Scope

- New `food_diary_entries` collection: `patient_id`, `owner_id`, `at`, `meal_title`, `dish`, `restaurant`, `kcal`, `protein`, `notes`, `created_at`.
- `POST /me/food_diary_entries` — the patient logs an entry (`dish` required, everything else optional), following the exact `owner_id`-resolution pattern already used by `POST /me/measurements`.
- `GET /me/food_diary_entries` — the patient's own entries, newest first.
- `GET /patients/{patient_id}/food_diary_entries` — the owning nutritionist's read, same ownership-check pattern as `GET /patients/{id}/body_compositions` (added in `019`).

## Out of Scope

- Photos of the meal.
- A full free-text food diary distinct from "eating out" — this models the one real logging flow that exists in `nutri_app` today (picking a suggested restaurant option), not a broader diary concept that doesn't exist in the product yet.

## Baseline Behavior

- `MyDayController.extraMeals` (the eating-out log) was pure in-memory `RxList` state — gone on restart, never sent anywhere.

## Target Design

- `POST /me/food_diary_entries {"dish": "Tacos al pastor", "meal_title": "Comida", "restaurant": "...", "kcal": 450, "protein": 22}` → `201`, entry with generated `id`/`at`.
- `GET /me/food_diary_entries` (same patient) → that entry.
- `GET /patients/{id}/food_diary_entries` (owning nutritionist) → the same entry.
- Same nutritionist call for a patient they don't own → `404`.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a patient logs an entry, when they then read `GET /me/food_diary_entries`, then it appears, newest first.
2. Given the owning nutritionist reads `GET /patients/{id}/food_diary_entries`, then the same entry appears.
3. Given a patient not linked to any nutritionist, when they log an entry, then it's still saved (`owner_id: null` is valid — mirrors `create_measurement`'s existing handling of an ownerless patient).
4. Given a patient's entries requested by a nutritionist who doesn't own them, then `404`.
5. Given no `dish` in the `POST` payload, then `400`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 54/54 green (4 new tests in `test_me_service.py`, 2 new in `test_patients_service.py`).
- Manual: `curl POST /me/food_diary_entries` (patient) → `201`; `curl GET /me/food_diary_entries` (same patient) → entry appears; `curl GET /patients/{id}/food_diary_entries` (owning nutritionist) → same entry appears. Entry left in place (no delete path exists for this resource, matching the `body_compositions`/InBody precedent).
