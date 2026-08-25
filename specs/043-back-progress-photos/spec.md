# Feature Specification: Progress Photos and Nutritionist Visibility into Self-Logged Measurements

**Feature Branch**: `043-back-progress-photos`
**Created**: 2026-08-25
**Status**: Draft
**Type**: Feature

## Objective

Phase 1b/1c of the TrainerStudio gap analysis (following `042-back-patient-nutritionist-chat`). The patient's self-logged `measurements` collection (behind `/me/measurements`/`/me/progress`) already existed but had no attachment support, and — more surprising — no nutritionist ever had any way to read it at all; only nutritionist-entered `body_compositions` (InBody scans) were visible on the nutritionist side. This adds photo attachments to a weigh-in, and closes the read-visibility gap so a nutritionist can actually see what their patient has logged.

## In Scope

- `POST /me/measurements` becomes `multipart/form-data` (mirroring `POST /patients/{patient_id}/body_compositions`'s existing shape exactly), accepting an optional `file` alongside the existing `at`/`weight_kg`/`body_fat_pct`/`waist_cm`/`notes` fields. On a file, reuses the existing `save_upload(file, subfolder=f"measurements/{user_id}")` (`app/core/storage.py`) — the same mechanism `body_compositions` and `plans` attachments already use.
- `attachment_url`/`attachment_type` persisted and returned on every `measurements` document (`create_measurement`, `_serialize_measurement`).
- New nutritionist-facing read endpoint: `GET /patients/{patient_id}/measurements` (role-gated, ownership-checked exactly like the sibling `body_compositions`/`food_diary_entries`/`plan_assignments` endpoints on the same router) — this is what actually makes the patient's self-logged weigh-ins and photos visible to their nutritionist for the first time.

## Out of Scope

- No change to `GET /me/progress` or `list_measurements_since` — the trend-chart data path was already graph-ready (time-ordered `weight_kg`/`body_fat_pct` series); this spec only adds the attachment and the nutritionist-read path. Chart UI itself is a front-end-only concern, covered by `049-front-progress-log` (`nutri_app`) and `041-front-nutritionist-progress-view` (`nutri_pro`).
- No index changes — `measurements` was already queried by `patient_id`; the new nutritionist-read path adds an `owner_id` ownership check via the existing `patients` collection, not a new query pattern needing its own index.
- No retroactive backfill of `attachment_url`/`attachment_type` on old documents — they simply serialize as `null`, same as any other optional field added to an existing collection in this codebase.

## Baseline Behavior

A patient could log a weigh-in (`weight_kg`/`body_fat_pct`/`waist_cm`/`notes`) via `POST /me/measurements`, but never with a photo. No nutritionist endpoint existed to read a patient's self-logged measurements at all — the nutritionist's only progress visibility was their own hand-entered `body_compositions` scans.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_app` spec `049-front-progress-log` (logging UI + trend chart) and `nutri_pro` spec `041-front-nutritionist-progress-view` (read-only view + trend chart).

## Acceptance Criteria

1. Given a patient posts a weigh-in with a photo to `POST /me/measurements`, then the response includes a resolvable `attachment_url` and its `attachment_type`.
2. Given that weigh-in exists, when the owning nutritionist calls `GET /patients/{patient_id}/measurements`, then it appears with the same `attachment_url`.
3. Given a nutritionist who doesn't own that patient, when calling `GET /patients/{patient_id}/measurements`, then it's refused with `404`.
4. Given the `attachment_url` from either endpoint, then fetching it returns the uploaded image bytes with the correct content type.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 163/163 green (1 new `test_me_service.py` case for the attachment round-trip, 2 new `test_patients_service.py` cases for `list_measurements`).
- Live verification against the running backend: registered a fresh patient, posted a weigh-in with a real PNG attachment, confirmed the owning nutritionist's `GET /patients/{id}/measurements` returns it with a fetchable `image/png` attachment, confirmed a second unrelated nutritionist gets `404`. Test accounts/data cleaned up after.
