# Feature Specification: Body Compositions List (Owner)

**Feature Branch**: `019-back-body-compositions-list`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Feature

## Objective

Let the nutritionist list a patient's InBody scan history (`GET /patients/{patient_id}/body_compositions`). Since `011-back-grip-strength-metric`-era work, scans could be logged (`POST .../body_compositions`) but never read back — `nutri_pro` was write-only.

## In Scope

- `PatientsRepository.list_body_compositions(owner_id, patient_id)` — verifies the patient belongs to the owner (same ownership check as `add_body_composition`), returns `None` (→ 404) if not, else the patient's scans sorted newest-first.
- `GET /patients/{patient_id}/body_compositions` route.

## Out of Scope

- Any change to the existing write path (`POST .../body_compositions`) or its shape.
- Pagination — a patient's scan count is small enough (logged periodically by a nutritionist) that a full list is fine for now.

## Baseline Behavior

- `body_compositions` documents existed (loggable via `POST`) but nothing let the owning nutritionist read them back — `nutri_pro`'s InBody feature (`008`/`011`) was write-only by necessity, not by design choice.

## Target Design

- `GET /patients/{id}/body_compositions` (as the owning nutritionist) → `[{"id", "at", "provider", "metrics", "attachment_url", "attachment_type"}, ...]`, newest-first.
- Same call for a patient not owned by the caller → `404`.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a patient with logged scans, when the owner calls `GET /patients/{id}/body_compositions`, then all scans are returned newest-first.
2. Given a patient owned by a different nutritionist, when called, then it's `404`, not the other owner's data.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 45/45 green (2 new tests in `test_patients_service.py`).
- Manual: `curl GET /patients/{id}/body_compositions` against the live backend for the demo patient → `200`, 5 real historical scans returned newest-first, including one with a real `attachment_url` from an earlier manual test.
