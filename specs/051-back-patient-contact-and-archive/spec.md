# Feature Specification: Patient Contact Info + Archive Instead of Hard Delete

**Feature Branch**: `051-back-patient-contact-and-archive`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

From the "Coach App Screen Audit" punch list (TrainerStudio screenshots vs. actual code): a client record has no `email`/`phone`, and `DELETE /patients/{id}` hard-deletes the chart — irreversible, and nothing in `nutri_pro` even calls it today. TrainerStudio's client records always carry contact info and archive (reversible) instead of deleting.

## In Scope

- `email`/`phone` fields on `Patient`, settable on create and update.
- `archived_at` field on `Patient`. `DELETE /patients/{id}` now archives (sets `archived_at`) instead of removing the document.
- `GET /patients` excludes archived patients by default; `include_archived=true` includes them.
- New `POST /patients/{patient_id}/unarchive` to restore a patient to the default roster.
- Archived patients excluded from the practice dashboard's `total_patients`, `new_patients_this_month`, and inactive-patients list.
- Archived patients excluded from the billing-quota patient count (`count_for_owner`) — an archived patient shouldn't count against the plan limit.

## Out of Scope

- No cascading archive of a patient's appointments/plans/logs — those stay as-is, just no longer surfaced via the default roster.
- No permanent-delete path — once archived, a patient can only be restored, never hard-deleted, via this API.
- No `nutri_app` (patient app) changes — this is nutritionist-side roster management.

## Baseline Behavior

`Patient` had no contact fields. `DELETE /patients/{id}` called `delete_one` — permanent, no undo.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `050-front-patient-contact-and-archive` consumes this.

## Acceptance Criteria

1. Given a nutritionist creates a patient with `email`/`phone`, then `GET /patients/{id}` returns both fields.
2. Given a nutritionist calls `DELETE /patients/{id}`, then the patient is excluded from `GET /patients` (default), still returned by `GET /patients?include_archived=true`, and `archived_at` is set.
3. Given an archived patient, when the nutritionist calls `POST /patients/{id}/unarchive`, then the patient reappears in the default `GET /patients` list and `archived_at` is `null`.
4. Given an archived patient, then the practice dashboard's `total_patients` and `new_patients_this_month` do not count them.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → full suite green.
- Live-curl verification against the running local server: create a patient with email/phone, archive it, confirm it drops out of the default list and appears with `include_archived=true`, unarchive it, confirm it returns; assign/toggle unaffected. Cleaned up test data via a direct Motor script afterward.
