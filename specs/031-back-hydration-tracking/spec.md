# Feature Specification: Minimal Hydration Tracking

**Feature Branch**: `031-back-hydration-tracking`
**Created**: 2026-08-20
**Status**: Draft
**Type**: Feature

## Objective

`nutri_app`'s Home and My Progress screens show a water-intake card (current/target ml, +/- buttons), but it was backed entirely by an in-memory mock with no persistence — every app restart reset it, and nothing was ever saved server-side. Add a minimal per-patient, per-day hydration counter so the existing UI reflects real, persisted state.

## In Scope

- `GET /me/hydration` — returns today's `{current_ml, target_ml}` for the authenticated patient, defaulting to `{0, 2000}` if nothing logged yet today.
- `POST /me/hydration` — body `{delta_ml: int}`, adds the delta to today's `current_ml`, clamped to `[0, target_ml]`, upserts the day's record, returns the updated `{current_ml, target_ml}`.
- `MeRepository.get_hydration_today` / `add_hydration` — new Protocol methods, implemented in `MongoMeRepository` against a new `hydration_logs` collection keyed by `(patient_id, date)`.

## Out of Scope

- Per-patient customizable hydration targets (fixed default of 2000 ml for now — no endpoint to change it).
- Historical hydration trends/charts (only "today" is tracked; no `list_hydration_since` equivalent to measurements).
- Nutritionist-facing visibility into a patient's hydration log.

## Baseline Behavior

- `nutri_app`'s `HomeMockDataSource.fetchHydration()`/`addHydration()` read/wrote an in-memory `MockDB.homeHydration` map — never touched the backend, reset on every app restart.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`
- **Cross-repo impact**: `nutri_app` (Home + My Progress hydration cards switch from `HomeMockDataSource` to a real `GET`/`POST /me/hydration` repository implementation).

## Acceptance Criteria

1. Given a patient with no hydration logged today, when `GET /me/hydration` is called, then `{current_ml: 0, target_ml: 2000}` is returned.
2. Given a patient adds 250ml twice, when `GET /me/hydration` is called afterward, then `current_ml` reflects 500.
3. Given `current_ml` is near 0, when a negative `delta_ml` larger than the current amount is posted, then `current_ml` clamps to 0 (never negative).
4. Given `current_ml` is near `target_ml`, when a large positive `delta_ml` is posted, then `current_ml` clamps to `target_ml` (never exceeds it).
5. Given a user with no linked patient chart, when `GET /me/hydration` is called, then the default `{0, 2000}` is returned rather than an error; `POST` raises a 404 instead.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 103/103 green (4 new tests in `test_me_service.py`).
- Manual: `curl` against the live local backend — fresh account defaults to `{0, 2000}`, two `+250` posts accumulate to 500 and persist across a subsequent `GET`, a `-1000` clamps to 0, a `+5000` clamps to 2000.
