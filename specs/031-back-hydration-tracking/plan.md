# Implementation Plan: Minimal Hydration Tracking

**Branch**: `031-back-hydration-tracking` | **Date**: 2026-08-20 | **Spec**: `specs/031-back-hydration-tracking/spec.md`

## Summary

Additive slice on the already-migrated `me` module: two new repository methods against a new `hydration_logs` collection (one doc per patient per day, upserted), one new service pair reusing the existing `_require_patient`/`get_patient_for_user` patterns, two new router endpoints.

## Steps

1. `me/domain/repositories.py`: `MeRepository.get_hydration_today(patient_id) -> dict`, `add_hydration(patient_id, *, delta_ml) -> dict`.
2. `me/infrastructure/mongo_me_repository.py`: implement both against `hydration_logs` (`{patient_id, date, current_ml, target_ml}`, `date` as a `YYYY-MM-DD` UTC string key), upsert via `update_one(..., upsert=True)`; module-level `_DEFAULT_HYDRATION_TARGET_ML = 2000`.
3. `me/application/me_service.py`: `get_hydration(user_id)` (returns default for users without a linked patient, same shape as `get_progress`'s empty-state pattern); `add_hydration(user_id, delta_ml)` (uses `_require_patient`, raises `LookupError` like `add_measurement`).
4. `me/presentation/router.py`: `GET /hydration`, `POST /hydration` (payload validated as `{delta_ml: int}`, 400 if missing/wrong type).
5. `tests/test_me_service.py`: extend `_FakeMeRepository` with hydration state; add clamp/default/missing-patient tests.

## Constraints

- One record per patient per UTC day, not an append-only log — matches the mock's "single mutable counter" behavior exactly, and keeps the write path a single upsert instead of an aggregation query. A history/trend view is out of scope until there's a real product need for it.
- Target is a fixed constant for now (no per-patient override endpoint) — same simplification the mock already made.
